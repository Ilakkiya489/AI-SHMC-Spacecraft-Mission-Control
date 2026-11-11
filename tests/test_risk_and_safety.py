"""
Unit tests for Risk Assessment, Safety Constraints, and Autonomy Management.
"""

import pytest
from app.config import RiskLevel, AutonomyLevel, RecoveryActionType, FaultCategory
from app.safety.risk_assessment import RiskAssessmentEngine
from app.safety.action_risk_evaluator import ActionRiskEvaluator
from app.safety.safety_constraints import SafetyConstraintChecker
from app.safety.safety_autonomy_manager import SafetyAutonomyManager
from app.simulation.spacecraft_twin import SpacecraftTwin


def test_fault_risk_calculation():
    # Low risk fault: Communication packet loss (S=2, P=2 -> Score=4)
    low_res = RiskAssessmentEngine.calculate_fault_risk(FaultCategory.COMMUNICATION_PACKET_LOSS.value)
    assert low_res["risk_score"] == 4
    assert low_res["risk_level"] == RiskLevel.LOW.value
    
    # High risk fault: Battery overheating (S=4, P=4 -> Score=16)
    high_res = RiskAssessmentEngine.calculate_fault_risk(FaultCategory.BATTERY_OVERHEATING.value)
    assert high_res["risk_score"] == 16
    assert high_res["risk_level"] == RiskLevel.HIGH.value
    
    # Critical risk fault: Multiple faults (S=5, P=4 -> Score=20)
    crit_res = RiskAssessmentEngine.calculate_fault_risk(FaultCategory.MULTIPLE_FAULTS.value)
    assert crit_res["risk_score"] == 20
    assert crit_res["risk_level"] == RiskLevel.CRITICAL.value


def test_action_risk_evaluation():
    # Pre-approved low-risk action
    act_low = ActionRiskEvaluator.evaluate(RecoveryActionType.RETRY_COMM_TRANSMISSION.value)
    assert act_low["action_risk_level"] == RiskLevel.LOW.value
    assert act_low["pre_approved"] is True
    
    # Critical irreversible action
    act_crit = ActionRiskEvaluator.evaluate(RecoveryActionType.ENTER_SAFE_HOLD.value)
    assert act_crit["action_risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]


def test_safety_constraints():
    # Nominal telemetry passes
    nom_telem = SpacecraftTwin().get_telemetry()
    passed, violations = SafetyConstraintChecker.check_telemetry_bounds(nom_telem)
    assert passed is True
    assert len(violations) == 0
    
    # Inviolable limit breach
    bad_telem = dict(nom_telem)
    bad_telem["battery_temperature"] = 55.0  # Above 52°C hard limit
    passed, violations = SafetyConstraintChecker.check_telemetry_bounds(bad_telem)
    assert passed is False
    assert len(violations) > 0


def test_autonomy_levels_classification():
    # CASE 1: Low risk fault + Low action risk + High confidence -> LEVEL 1
    diag_low = {"fault": FaultCategory.COMMUNICATION_PACKET_LOSS.value, "confidence_pct": 95.0, "severity_score": 2}
    res_l1 = SafetyAutonomyManager.evaluate_autonomy(
        telemetry=SpacecraftTwin().get_telemetry(),
        fault_diagnosis=diag_low,
        proposed_action=RecoveryActionType.RETRY_COMM_TRANSMISSION.value
    )
    assert "LEVEL 1" in res_l1["autonomy_level"]
    assert res_l1["can_execute_autonomously"] is True
    assert res_l1["requires_human_approval"] is False
    
    # CASE 2: High risk fault + High action risk -> LEVEL 3 (Human Approval Required)
    diag_high = {"fault": FaultCategory.BATTERY_OVERHEATING.value, "confidence_pct": 92.0, "severity_score": 4}
    res_l3 = SafetyAutonomyManager.evaluate_autonomy(
        telemetry=SpacecraftTwin().get_telemetry(),
        fault_diagnosis=diag_high,
        proposed_action=RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value
    )
    assert "LEVEL 3" in res_l3["autonomy_level"]
    assert res_l3["can_execute_autonomously"] is False
    assert res_l3["requires_human_approval"] is True
    
    # CASE 3: Low confidence (< 75%) -> Blocks risky autonomy
    diag_uncertain = {"fault": FaultCategory.BATTERY_OVERHEATING.value, "confidence_pct": 60.0, "severity_score": 4}
    res_uncert = SafetyAutonomyManager.evaluate_autonomy(
        telemetry=SpacecraftTwin().get_telemetry(),
        fault_diagnosis=diag_uncertain,
        proposed_action=RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value
    )
    assert res_uncert["can_execute_autonomously"] is False
    assert "ESCALATION" in res_uncert["decision_code"] or res_uncert["requires_human_approval"]

