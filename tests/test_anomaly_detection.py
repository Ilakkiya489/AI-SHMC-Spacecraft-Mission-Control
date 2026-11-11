"""
Unit tests for AI Anomaly Detection and Fault Diagnosis Models.
"""

import pytest
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.ai_models.anomaly_detection import AnomalyDetector
from app.ai_models.fault_diagnosis import FaultDiagnoser
from app.config import FaultCategory


def test_anomaly_detection_nominal():
    detector = AnomalyDetector()
    assert detector.load("models/anomaly_detector.joblib")
    
    twin = SpacecraftTwin()
    telem = twin.get_telemetry()
    res = detector.detect(telem)
    
    assert "is_anomaly" in res
    assert "anomaly_score" in res
    assert res["detection_status"] in ["NORMAL", "ABNORMAL"]


def test_anomaly_detection_fault_attribution():
    detector = AnomalyDetector()
    detector.load("models/anomaly_detector.joblib")
    
    # Create anomalous telemetry frame (overheating battery)
    telem = SpacecraftTwin().get_telemetry()
    telem["battery_temperature"] = 49.5  # Critical bound violation
    
    res = detector.detect(telem)
    assert res["is_anomaly"] is True
    assert res["detection_status"] == "ABNORMAL"
    assert res["primary_parameter"] == "battery_temperature"


def test_fault_diagnosis_accuracy():
    diagnoser = FaultDiagnoser()
    assert diagnoser.load("models/fault_diagnoser.joblib")
    
    twin = SpacecraftTwin()
    twin.inject_fault(FaultCategory.BATTERY_OVERHEATING.value)
    twin.step(10.0)
    telem = twin.get_telemetry()
    
    res = diagnoser.diagnose(telem)
    assert res["fault"] == FaultCategory.BATTERY_OVERHEATING.value
    assert res["confidence_pct"] >= 75.0
    assert "Power" in res["affected_subsystem"] or "Thermal" in res["affected_subsystem"]
    assert res["severity_score"] >= 3

