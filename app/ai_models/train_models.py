"""
Model Training Pipeline for AI-SHMC.
Trains Anomaly Detector, Fault Diagnoser, and Predictive Regressors.
Evaluates model performance and saves serialized weights.
"""

import os
import sys
import time

# Ensure dependencies and project root are in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_deps_path = os.path.join(_project_root, ".deps")
if sys.version_info[:2] == (3, 8):
    if os.path.exists(_deps_path) and _deps_path not in sys.path:
        sys.path.insert(0, _deps_path)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pandas as pd
from app.simulation.telemetry_generator import TelemetryGenerator
from app.ai_models.anomaly_detection import AnomalyDetector
from app.ai_models.fault_diagnosis import FaultDiagnoser
from app.ai_models.prediction import TelemetryPredictor
from app.ai_models.model_evaluation import ModelEvaluator


def train_all(force_regenerate: bool = False, total_records: int = 12000):
    start_time = time.time()
    print("=" * 65)
    print("AI-SHMC: Starting End-to-End AI/ML Model Training Pipeline")
    print("=" * 65)
    
    data_dir = "data/synthetic"
    processed_dir = "data/processed"
    raw_csv = os.path.join(data_dir, "synthetic_spacecraft_telemetry.csv")
    train_csv = os.path.join(processed_dir, "train_telemetry.csv")
    val_csv = os.path.join(processed_dir, "val_telemetry.csv")
    test_csv = os.path.join(processed_dir, "test_telemetry.csv")
    
    # 1. Dataset Generation or Loading
    generator = TelemetryGenerator()
    if force_regenerate or not os.path.exists(train_csv):
        print(f"[Pipeline] Generating fresh dataset with {total_records} records...")
        df = generator.generate_dataset(total_records=total_records)
        train_df, val_df, test_df = generator.split_dataset(df)
    else:
        print("[Pipeline] Loading existing train/val/test splits...")
        train_df = pd.read_csv(train_csv)
        val_df = pd.read_csv(val_csv)
        test_df = pd.read_csv(test_csv)
        print(f"[Pipeline] Loaded: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
        
    os.makedirs("models", exist_ok=True)
    
    # 2. Train Anomaly Detector (Isolation Forest)
    print("\n[Step 1/3] Training Isolation Forest Anomaly Detector...")
    t0 = time.time()
    # Train primarily on nominal data so model learns normal spacecraft manifold
    nominal_train = train_df[train_df["fault_label"] == "Nominal"]
    detector = AnomalyDetector(contamination=0.05)
    detector.fit(nominal_train if len(nominal_train) > 500 else train_df)
    detector.save("models/anomaly_detector.joblib")
    print(f"[Step 1/3] Anomaly Detector fitted in {round(time.time() - t0, 2)}s")
    
    # 3. Train Fault Diagnoser (Multiclass Random Forest)
    print("\n[Step 2/3] Training Random Forest Fault Diagnoser...")
    t0 = time.time()
    diagnoser = FaultDiagnoser(n_estimators=100, max_depth=12)
    diagnoser.fit(train_df)
    diagnoser.save("models/fault_diagnoser.joblib")
    print(f"[Step 2/3] Fault Diagnoser fitted in {round(time.time() - t0, 2)}s")
    
    # 4. Train Multi-Horizon Telemetry Predictor
    print("\n[Step 3/3] Training Telemetry Predictor Regressors (Horizons: 1m, 3m, 5m, 10m)...")
    t0 = time.time()
    predictor = TelemetryPredictor(horizons=[1, 3, 5, 10])
    predictor.fit(train_df)
    predictor.save("models/telemetry_predictor.joblib")
    print(f"[Step 3/3] Telemetry Predictor fitted in {round(time.time() - t0, 2)}s")
    
    # 5. Evaluate on Holdout Test Set
    print("\n[Step 4] Running Evaluation Benchmarks on Test Set...")
    metrics = ModelEvaluator.evaluate_all(
        detector=detector,
        diagnoser=diagnoser,
        predictor=predictor,
        test_df=test_df,
        output_filepath="models/evaluation_metrics.json"
    )
    
    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 65)
    print(f"AI-SHMC: Model Training Completed Successfully in {elapsed}s!")
    print(f"Anomaly Detection ML F1: {metrics['anomaly_detection']['ml_model']['f1_score']}")
    print(f"Fault Diagnosis Weighted F1: {metrics['fault_diagnosis']['weighted_f1_score']}")
    print("=" * 65)
    return metrics


if __name__ == "__main__":
    train_all(force_regenerate=True)

