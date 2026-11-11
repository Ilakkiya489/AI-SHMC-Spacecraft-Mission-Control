"""
End-to-End System Integration Tests for AI-SHMC.
Validates the complete 8-stage copilot workflow across the three mandatory demonstration cases:
- CASE A: LOW RISK (Autonomous recovery permitted and verified)
- CASE B: HIGH RISK (Human-in-the-loop approval gate and execution)
- CASE C: CRITICAL / UNCERTAIN (Unsafe recovery blocked; Safe-state escalation)
"""

import pytest
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.simulation.fault_injector import FaultInjector
from app.ai_models.anomaly_detection import AnomalyDetector
from app.ai_models.fault_diagnosis import FaultDiagnoser
from app.ai_models.prediction import TelemetryPredictor
from app.intelligence.decision_engine import MissionControlDecisionEngine
from app.recovery.human_approval import OperatorDecision
from app.config import FaultCategory, AutonomyLevel


@pytest.fixture
def copilot_fixture():
    twin = SpacecraftTwin()
    detector = AnomalyDetector()
    detector.load("models/anomaly_detector.joblib")
    
    diagnoser = FaultDiagnoser()
    diagnoser.load("models/fault_diagnoser.joblib")
    
    predictor = TelemetryPredictor()
    predictor.load("models/telemetry_predictor.joblib")
    
    copilot = MissionControlDecisionEngine(twin, detector, diagnoser, predictor)
    return copilot, twin


def test_case_a_low_risk_autonomous_recovery(copilot_fixture):
    """
    CASE A: LOW RISK
    Fault: Communication Packet Loss
    Workflow: DETECT -> DIAGNOSE -> PREDICT -> SIMULATE -> ASSESS -> AUTONOMOUS RECOVERY (Level 1) -> VERIFIED
    """
    copilot, twin = copilot_fixture
    injector = FaultInjector(twin)
    
    # 1. Inject Low Risk Fault: Scenario 5 (Comm Packet Loss)
    injector.inject_scenario(5, intensity=1.0)
    twin.step(4.0)
    
    # 2. Run Full Copilot Decision Cycle
    cycle_res = copilot.run_copilot_cycle(auto_execute_level_1=True)
    
    # 3. Assertions
    assert cycle_res["anomaly_detection"]["is_anomaly"] is True
    assert "Communication" in cycle_res["anomaly_detection"]["primary_subsystem"]
    
    # Fault Diagnosed accurately
    assert "Packet Loss" in cycle_res["fault_diagnosis"]["fault"] or "Communication" in cycle_res["fault_diagnosis"]["affected_subsystem"]
    
    # Permitted Autonomy Level 1: Full Autonomous Recovery
    autonomy = cycle_res["autonomy_decision"]
    assert "LEVEL 1" in autonomy["autonomy_level"]
    assert autonomy["can_execute_autonomously"] is True
    assert autonomy["requires_human_approval"] is False
    
    # Recovery Execution and Verification
    exec_rec = cycle_res["recovery_execution"]
    assert exec_rec is not None
    assert exec_rec["status"] == "EXECUTED"
    
    verif = cycle_res["verification"]
    assert verif is not None
    assert verif["improved"] is True


def test_case_b_high_risk_human_in_the_loop_approval(copilot_fixture):
    """
    CASE B: HIGH RISK
    Fault: Battery Overheating
    Workflow: DETECT -> DIAGNOSE -> PREDICT -> WHAT-IF SIMULATION -> HIGH RISK -> HUMAN APPROVAL REQUIRED (Level 3)
              -> OPERATOR APPROVES -> RECOVERY EXECUTED -> EMPIRICAL VERIFICATION
    """
    copilot, twin = copilot_fixture
    injector = FaultInjector(twin)
    
    # 1. Inject High Risk Fault: Scenario 1 (Battery Overheating)
    injector.inject_scenario(1, intensity=1.2)
    twin.step(6.0)
    
    # 2. Run Full Copilot Cycle (Without auto-bypassing human gate)
    cycle_res = copilot.run_copilot_cycle(auto_execute_level_1=True)
    
    # 3. Assertions
    assert cycle_res["anomaly_detection"]["is_anomaly"] is True
    assert cycle_res["fault_diagnosis"]["fault"] == FaultCategory.BATTERY_OVERHEATING.value
    
    autonomy = cycle_res["autonomy_decision"]
    # Level 3 Human Approval Required!
    assert "LEVEL 3" in autonomy["autonomy_level"]
    assert autonomy["can_execute_autonomously"] is False
    assert autonomy["requires_human_approval"] is True
    
    # Action must NOT execute automatically before operator signs off!
    assert cycle_res["recovery_execution"] is None
    
    # Approval Request created in Operator Queue
    pending = copilot.approval_manager.get_pending_requests()
    assert len(pending) > 0
    req = pending[0]
    assert req["status"] == "PENDING"
    assert req["detected_fault"] == FaultCategory.BATTERY_OVERHEATING.value
    
    # What-If forward simulation performed and recommended strategy
    assert cycle_res["what_if_simulation"] is not None
    assert req["recommended_recovery_action"] in [
        "REDUCE_PAYLOAD_ACTIVITY",
        "THROTTLE_CPU_WORKLOAD",
        "ACTIVATE_AUX_COOLING",
        "SHED_NON_ESSENTIAL_POWER"
    ]
    
    # 4. Operator Explicitly Approves Recovery
    approval_result = copilot.approval_manager.submit_decision(
        request_id=req["request_id"],
        decision=OperatorDecision.APPROVED,
        operator_id="CHIEF_FLIGHT_DIRECTOR",
        operator_notes="Approved based on Digital Twin thermal projection."
    )
    assert approval_result["status"] == OperatorDecision.APPROVED.value
    
    # 5. Recovery Execution dispatches post-approval
    exec_res = copilot.recovery_engine.execute_recovery(
        action_name=req["recommended_recovery_action"],
        authorized_by="OPERATOR_CHIEF_FLIGHT_DIRECTOR"
    )
    assert exec_res["status"] == "EXECUTED"
    
    # 6. Verification gathers post-recovery telemetry
    verif_res = copilot.verifier.verify_recovery(
        action_name=req["recommended_recovery_action"],
        target_parameter="battery_temperature",
        pre_telemetry=exec_res["pre_telemetry"]
    )
    assert verif_res["improved"] is True


def test_case_c_critical_uncertain_safe_state_escalation(copilot_fixture):
    """
    CASE C: CRITICAL / UNCERTAIN
    Fault: Multiple simultaneous subsystem faults + low AI diagnostic confidence / constraint breach
    Workflow: DETECT -> CRITICAL / LOW CONFIDENCE -> UNSAFE RECOVERY BLOCKED -> LEVEL 4 SAFE-STATE ESCALATION
    """
    copilot, twin = copilot_fixture
    injector = FaultInjector(twin)
    
    # 1. Inject Scenario 10 (Multiple Faults: Battery Overheating + Solar Degradation)
    injector.inject_scenario(10, intensity=1.5)
    twin.step(8.0)
    
    # 2. Run Copilot Cycle
    cycle_res = copilot.run_copilot_cycle(auto_execute_level_1=True)
    
    autonomy = cycle_res["autonomy_decision"]
    
    # 3. Assertions
    # Must trigger Level 4 Safe-State Escalation!
    assert "LEVEL 4" in autonomy["autonomy_level"]
    assert autonomy["is_escalated"] is True
    assert autonomy["can_execute_autonomously"] is False
    
    # Unsafe non-emergency recovery must be blocked
    # Emergency safe-state hold procedure is engaged
    exec_res = cycle_res["recovery_execution"]
    assert exec_res is not None
    assert exec_res["action"] == "ENTER_SAFE_HOLD"
    assert "EMERGENCY" in exec_res["authorized_by"]

