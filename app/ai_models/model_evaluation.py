"""
Model Evaluation and Benchmarking Module for AI-SHMC.
Calculates formal performance metrics:
- Precision, Recall, F1-score, Confusion Matrix for Anomaly Detection
- Multiclass Accuracy, Precision, Recall, F1-score for Fault Diagnosis
- MAE, RMSE, R2 for Predictive Telemetry Regressors
- Ablation & Baseline comparison (Threshold-based vs ML-based)
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix,
    classification_report
)

from app.config import TELEMETRY_SPECS
from app.ai_models.anomaly_detection import AnomalyDetector, FEATURE_COLUMNS
from app.ai_models.fault_diagnosis import FaultDiagnoser
from app.ai_models.prediction import TelemetryPredictor, PREDICTION_TARGETS


class ModelEvaluator:
    @staticmethod
    def evaluate_anomaly_detection(detector: AnomalyDetector, test_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluates Isolation Forest anomaly detector against test ground truth.
        """
        y_true = (test_df["fault_label"] != "Nominal").astype(int).values
        
        # Isolation Forest prediction
        X = test_df[FEATURE_COLUMNS].values
        raw_pred = detector.model.predict(X)
        y_pred = (raw_pred == -1).astype(int)
        
        # Compare with threshold-based monitoring baseline
        y_thresh_pred = []
        for _, row in test_df[FEATURE_COLUMNS].iterrows():
            is_thresh_viol = False
            for col in FEATURE_COLUMNS:
                v = float(row[col])
                spec = TELEMETRY_SPECS.get(col, {})
                if v < spec.get("nominal_min", -9e9) or v > spec.get("nominal_max", 9e9):
                    is_thresh_viol = True
                    break
            y_thresh_pred.append(int(is_thresh_viol))
        y_thresh_pred = np.array(y_thresh_pred)
        
        # Metrics for ML model
        ml_prec = float(precision_score(y_true, y_pred, zero_division=0))
        ml_rec = float(recall_score(y_true, y_pred, zero_division=0))
        ml_f1 = float(f1_score(y_true, y_pred, zero_division=0))
        ml_acc = float(accuracy_score(y_true, y_pred))
        ml_cm = confusion_matrix(y_true, y_pred).tolist()
        
        # Metrics for Threshold baseline
        th_prec = float(precision_score(y_true, y_thresh_pred, zero_division=0))
        th_rec = float(recall_score(y_true, y_thresh_pred, zero_division=0))
        th_f1 = float(f1_score(y_true, y_thresh_pred, zero_division=0))
        th_acc = float(accuracy_score(y_true, y_thresh_pred))
        th_cm = confusion_matrix(y_true, y_thresh_pred).tolist()
        
        return {
            "ml_model": {
                "name": "Isolation Forest",
                "accuracy": round(ml_acc, 4),
                "precision": round(ml_prec, 4),
                "recall": round(ml_rec, 4),
                "f1_score": round(ml_f1, 4),
                "confusion_matrix": ml_cm
            },
            "threshold_baseline": {
                "name": "Statistical Threshold Monitor",
                "accuracy": round(th_acc, 4),
                "precision": round(th_prec, 4),
                "recall": round(th_rec, 4),
                "f1_score": round(th_f1, 4),
                "confusion_matrix": th_cm
            },
            "f1_improvement_pct": round(((ml_f1 - th_f1) / max(1e-4, th_f1)) * 100.0, 2)
        }

    @staticmethod
    def evaluate_fault_diagnosis(diagnoser: FaultDiagnoser, test_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluates multiclass Random Forest fault classifier on test set.
        """
        X = test_df[FEATURE_COLUMNS].values
        y_true = test_df["fault_label"].values
        y_pred = diagnoser.model.predict(X)
        
        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
        
        classes = list(diagnoser.classes_)
        cm = confusion_matrix(y_true, y_pred, labels=classes).tolist()
        
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        
        return {
            "name": "Random Forest Classifier",
            "accuracy": round(acc, 4),
            "weighted_precision": round(prec, 4),
            "weighted_recall": round(rec, 4),
            "weighted_f1_score": round(f1, 4),
            "classes": classes,
            "confusion_matrix": cm,
            "classification_report": report
        }

    @staticmethod
    def evaluate_all(
        detector: AnomalyDetector,
        diagnoser: FaultDiagnoser,
        predictor: TelemetryPredictor,
        test_df: pd.DataFrame,
        output_filepath: str = "models/evaluation_metrics.json"
    ) -> Dict[str, Any]:
        """
        Runs comprehensive evaluation across all AI modules and persists results.
        """
        results = {
            "anomaly_detection": ModelEvaluator.evaluate_anomaly_detection(detector, test_df),
            "fault_diagnosis": ModelEvaluator.evaluate_fault_diagnosis(diagnoser, test_df),
            "predictive_analytics": {
                f"horizon_{h}m": predictor.evaluate(test_df, horizon_minutes=h)
                for h in predictor.horizons
            }
        }
        
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        with open(output_filepath, "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"[ModelEvaluator] Evaluation report saved to {output_filepath}")
        return results

