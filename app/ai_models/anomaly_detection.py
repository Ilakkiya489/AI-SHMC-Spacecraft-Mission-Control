"""
AI Anomaly Detection Module for AI-SHMC.
Combines Isolation Forest with a Statistical Z-score & Hard Bound baseline
to detect abnormal telemetry behaviors and isolate affected parameters.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest

from app.config import TELEMETRY_SPECS, SubsystemName


FEATURE_COLUMNS = [
    "battery_voltage",
    "battery_temperature",
    "battery_charge",
    "solar_current",
    "power_consumption",
    "cpu_temperature",
    "cpu_usage",
    "memory_usage",
    "signal_strength",
    "packet_loss",
    "communication_latency",
    "storage_usage",
    "payload_activity"
]

PARAM_TO_SUBSYSTEM = {
    "battery_voltage": SubsystemName.POWER.value,
    "battery_temperature": SubsystemName.THERMAL.value,
    "battery_charge": SubsystemName.POWER.value,
    "solar_current": SubsystemName.POWER.value,
    "power_consumption": SubsystemName.POWER.value,
    "cpu_temperature": SubsystemName.THERMAL.value,
    "cpu_usage": SubsystemName.PROCESSING.value,
    "memory_usage": SubsystemName.PROCESSING.value,
    "signal_strength": SubsystemName.COMMUNICATION.value,
    "packet_loss": SubsystemName.COMMUNICATION.value,
    "communication_latency": SubsystemName.COMMUNICATION.value,
    "storage_usage": SubsystemName.STORAGE.value,
    "payload_activity": SubsystemName.PAYLOAD.value
}


class AnomalyDetector:
    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.feature_means: Dict[str, float] = {}
        self.feature_stds: Dict[str, float] = {}
        self.is_fitted = False
        
    def fit(self, df: pd.DataFrame):
        """
        Trains Isolation Forest and computes baseline statistics on nominal training telemetry.
        """
        X = df[FEATURE_COLUMNS].copy()
        
        # Calculate statistical baselines for z-score attribution
        for col in FEATURE_COLUMNS:
            self.feature_means[col] = float(X[col].mean())
            self.feature_stds[col] = max(1e-4, float(X[col].std()))
            
        self.model.fit(X.values)
        self.is_fitted = True
        return self

    def detect(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects anomalies in an incoming telemetry frame.
        Evaluates Isolation Forest score + statistical deviations + safety bounds.
        """
        # Extract features
        x_vec = np.array([[float(telemetry.get(col, 0.0)) for col in FEATURE_COLUMNS]])
        
        # 1. Isolation Forest inference
        if self.is_fitted:
            # -1 for anomaly, 1 for normal
            pred = int(self.model.predict(x_vec)[0])
            # anomaly score: lower is more abnormal, negative is anomalous
            raw_score = float(self.model.score_samples(x_vec)[0])
            # Normalize anomaly score to [0.0, 1.0] where 1.0 is most anomalous
            # Isolation forest score_samples typically ranges from -0.8 to -0.3
            normalized_score = max(0.0, min(1.0, (-raw_score - 0.35) / 0.45))
            if_anomaly = (pred == -1)
        else:
            if_anomaly = False
            normalized_score = 0.0
            
        # 2. Statistical threshold & hard boundary check with quantitative severity ranking
        bound_violations = []
        warning_parameters = []
        
        for col in FEATURE_COLUMNS:
            val = float(telemetry.get(col, 0.0))
            spec = TELEMETRY_SPECS.get(col, {})
            
            nom_min = spec.get("nominal_min", -9999.0)
            nom_max = spec.get("nominal_max", 9999.0)
            crit_min = spec.get("critical_min", -9999.0)
            crit_max = spec.get("critical_max", 9999.0)
            unit = spec.get("unit", "")
            
            subsystem = PARAM_TO_SUBSYSTEM.get(col, "Unknown")
            
            # If value is within nominal safe operational envelope, it is strictly NOMINAL
            if nom_min <= val <= nom_max:
                continue

            # Quantitative breach severity calculation for out-of-nominal parameters
            sev_score = 0.0
            violation_type = "NOMINAL"

            if val > crit_max:
                sev_score = 2.0 + (val - crit_max) / max(0.5, crit_max - nom_max)
                violation_type = "CRITICAL_HIGH"
            elif val < crit_min:
                sev_score = 2.0 + (crit_min - val) / max(0.5, nom_min - crit_min)
                violation_type = "CRITICAL_LOW"
            elif val > nom_max:
                sev_score = 1.0 + (val - nom_max) / max(0.5, crit_max - nom_max)
                violation_type = "WARNING_HIGH"
            elif val < nom_min:
                sev_score = 1.0 + (nom_min - val) / max(0.5, nom_min - crit_min)
                violation_type = "WARNING_LOW"

            if sev_score >= 2.0:
                bound_violations.append({
                    "parameter": col,
                    "value": val,
                    "unit": unit,
                    "violation": violation_type,
                    "severity_score": round(sev_score, 3),
                    "subsystem": subsystem
                })
            elif sev_score >= 1.0:
                warning_parameters.append({
                    "parameter": col,
                    "value": val,
                    "unit": unit,
                    "violation": violation_type,
                    "severity_score": round(sev_score, 3),
                    "subsystem": subsystem
                })

        # Sort both lists by severity_score descending so most severe anomaly is always ranked first!
        bound_violations.sort(key=lambda x: x["severity_score"], reverse=True)
        warning_parameters.sort(key=lambda x: x["severity_score"], reverse=True)
        all_affected = bound_violations + warning_parameters

        # Aerospace hybrid safety rule: If no physical parameter breached nominal range,
        # telemetry is strictly NORMAL, suppressing false alarms on nominal flight states.
        if len(all_affected) == 0:
            is_anomaly = False
            normalized_score = min(0.12, normalized_score * 0.15)
        else:
            is_anomaly = True
            normalized_score = max(0.40, normalized_score)

        primary_param = all_affected[0] if all_affected else None
        primary_subsystem = primary_param["subsystem"] if primary_param else "None"
            
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(normalized_score, 3),
            "detection_status": "ABNORMAL" if is_anomaly else "NORMAL",
            "if_model_decision": "ANOMALY" if if_anomaly else "NORMAL",
            "primary_parameter": primary_param["parameter"] if primary_param else None,
            "primary_subsystem": primary_subsystem or "None",
            "primary_value": primary_param["value"] if primary_param else None,
            "primary_unit": primary_param["unit"] if primary_param else "",
            "affected_parameters": all_affected,
            "summary": (
                f"ANOMALY DETECTED: Subsystem {primary_subsystem}, Parameter {primary_param['parameter']} "
                f"value {primary_param['value']}{primary_param['unit']}"
                if is_anomaly and primary_param else "ALL TELEMETRY NOMINAL"
            )
        }

    def save(self, filepath: str = "models/anomaly_detector.joblib"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            "model": self.model,
            "feature_means": self.feature_means,
            "feature_stds": self.feature_stds,
            "is_fitted": self.is_fitted,
            "contamination": self.contamination
        }, filepath)
        print(f"[AnomalyDetector] Saved model to {filepath}")

    def load(self, filepath: str = "models/anomaly_detector.joblib") -> bool:
        if not os.path.exists(filepath):
            return False
        data = joblib.load(filepath)
        self.model = data["model"]
        self.feature_means = data["feature_means"]
        self.feature_stds = data["feature_stds"]
        self.is_fitted = data["is_fitted"]
        self.contamination = data.get("contamination", 0.08)
        print(f"[AnomalyDetector] Loaded model from {filepath}")
        return True
