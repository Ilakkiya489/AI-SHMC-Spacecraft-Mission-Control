"""
AI Predictive Analytics Module for AI-SHMC.
Multi-horizon telemetry forecasting using lightweight Random Forest Regressors.
Predicts future values for:
- Battery Temperature
- Battery Voltage
- CPU Temperature
- Power Consumption
- Signal Strength
across configurable prediction horizons (1, 3, 5, 10 minutes).
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.config import DEFAULT_PREDICTION_HORIZONS, TELEMETRY_SPECS
from app.ai_models.anomaly_detection import FEATURE_COLUMNS


PREDICTION_TARGETS = [
    "battery_temperature",
    "battery_voltage",
    "cpu_temperature",
    "power_consumption",
    "signal_strength"
]


class TelemetryPredictor:
    def __init__(self, horizons: List[int] = DEFAULT_PREDICTION_HORIZONS, random_state: int = 42):
        self.horizons = horizons  # in simulation minutes
        self.random_state = random_state
        # Models dictionary: horizon_min -> target -> RandomForestRegressor
        self.models: Dict[int, Dict[str, RandomForestRegressor]] = {}
        self.is_fitted = False
        
    def fit(self, train_df: pd.DataFrame, step_size_s: float = 1.0):
        """
        Trains multi-horizon regressor models.
        Constructs lead-lag feature matrices for each prediction horizon.
        """
        df = train_df.copy().reset_index(drop=True)
        self.models = {}
        
        for h_min in self.horizons:
            self.models[h_min] = {}
            # Offset in records (assuming sampling step_size_s)
            offset = max(1, int((h_min * 60) / (step_size_s * 10)))  # Subsample offset for fast CPU fit
            offset = min(offset, len(df) // 10)
            
            X = df[FEATURE_COLUMNS].iloc[:-offset].values
            
            for target in PREDICTION_TARGETS:
                y = df[target].iloc[offset:].values
                
                # Lightweight CPU-friendly regressor
                reg = RandomForestRegressor(
                    n_estimators=30,
                    max_depth=8,
                    random_state=self.random_state,
                    n_jobs=-1
                )
                reg.fit(X, y)
                self.models[h_min][target] = reg
                
        self.is_fitted = True
        return self

    def predict(self, telemetry: Dict[str, Any], horizon_minutes: int = 3) -> Dict[str, Any]:
        """
        Predicts future values for target parameters at requested horizon.
        Evaluates parameter slope and identifies increasing risk trends.
        """
        if horizon_minutes not in self.models and self.is_fitted:
            # Pick closest available horizon
            horizon_minutes = min(self.horizons, key=lambda x: abs(x - horizon_minutes))
            
        x_vec = np.array([[float(telemetry.get(col, 0.0)) for col in FEATURE_COLUMNS]])
        
        predictions: Dict[str, Dict[str, Any]] = {}
        highest_risk_trend = "STABLE"
        
        for target in PREDICTION_TARGETS:
            current_val = float(telemetry.get(target, 0.0))
            spec = TELEMETRY_SPECS.get(target, {})
            unit = spec.get("unit", "")
            crit_max = spec.get("critical_max", 9999.0)
            crit_min = spec.get("critical_min", -9999.0)
            nom_max = spec.get("nominal_max", 9999.0)
            nom_min = spec.get("nominal_min", -9999.0)
            
            if self.is_fitted and horizon_minutes in self.models:
                pred_val = float(self.models[horizon_minutes][target].predict(x_vec)[0])
            else:
                pred_val = current_val
                
            delta = pred_val - current_val
            rate_per_min = delta / max(1, horizon_minutes)
            
            # Trend direction
            if abs(delta) < 0.2:
                trend = "STABLE"
            elif delta > 0:
                trend = "INCREASING"
            else:
                trend = "DECREASING"
                
            # Assess whether the trend increases mission risk
            risk_trend = "NOMINAL"
            if "temperature" in target or "consumption" in target:
                if pred_val > nom_max or delta > 3.0:
                    risk_trend = "INCREASING_RISK"
                    highest_risk_trend = "CRITICAL" if pred_val > crit_max else "HIGH_RISK"
            elif target in ["battery_voltage", "battery_charge", "signal_strength"]:
                if pred_val < nom_min or delta < -2.0:
                    risk_trend = "INCREASING_RISK"
                    highest_risk_trend = "CRITICAL" if pred_val < crit_min else "HIGH_RISK"
                    
            predictions[target] = {
                "current_value": round(current_val, 2),
                "predicted_value": round(pred_val, 2),
                "delta": round(delta, 2),
                "rate_per_min": round(rate_per_min, 2),
                "unit": unit,
                "trend": trend,
                "risk_trend": risk_trend
            }
            
        return {
            "horizon_minutes": horizon_minutes,
            "overall_risk_trend": highest_risk_trend,
            "predictions": predictions,
            "summary": (
                f"Prediction ({horizon_minutes}m): Battery Temp -> {predictions['battery_temperature']['predicted_value']}°C, "
                f"Battery Voltage -> {predictions['battery_voltage']['predicted_value']}V. Risk Trend: {highest_risk_trend}"
            )
        }

    def evaluate(self, test_df: pd.DataFrame, horizon_minutes: int = 3) -> Dict[str, Any]:
        """
        Computes formal time-series validation metrics: MAE, RMSE, R2.
        """
        if not self.is_fitted or horizon_minutes not in self.models:
            return {}
            
        offset = max(1, int((horizon_minutes * 60) / 10))
        offset = min(offset, len(test_df) // 10)
        
        X = test_df[FEATURE_COLUMNS].iloc[:-offset].values
        metrics = {}
        
        for target in PREDICTION_TARGETS:
            y_true = test_df[target].iloc[offset:].values
            y_pred = self.models[horizon_minutes][target].predict(X)
            
            mae = float(mean_absolute_error(y_true, y_pred))
            rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
            r2 = float(r2_score(y_true, y_pred))
            
            metrics[target] = {
                "mae": round(mae, 3),
                "rmse": round(rmse, 3),
                "r2_score": round(r2, 3)
            }
            
        return metrics

    def save(self, filepath: str = "models/telemetry_predictor.joblib"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            "models": self.models,
            "horizons": self.horizons,
            "is_fitted": self.is_fitted
        }, filepath)
        print(f"[TelemetryPredictor] Saved models to {filepath}")

    def load(self, filepath: str = "models/telemetry_predictor.joblib") -> bool:
        if not os.path.exists(filepath):
            return False
        data = joblib.load(filepath)
        self.models = data["models"]
        self.horizons = data["horizons"]
        self.is_fitted = data["is_fitted"]
        print(f"[TelemetryPredictor] Loaded models from {filepath}")
        return True

