"""
Unit tests for Recovery Engine and Verification Engine.
"""

import pytest
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.recovery.recovery_engine import RecoveryEngine
from app.recovery.recovery_verification import RecoveryVerifier, VerificationOutcome
from app.config import RecoveryActionType, FaultCategory


def test_recovery_execution():
    twin = SpacecraftTwin()
    engine = RecoveryEngine(twin, max_retries=2)
    
    twin.inject_fault(FaultCategory.COMMUNICATION_PACKET_LOSS.value)
    twin.step(3.0)
    
    res = engine.execute_recovery(RecoveryActionType.RETRY_COMM_TRANSMISSION.value, authorized_by="UNIT_TEST")
    assert res["status"] == "EXECUTED"
    assert res["retry_attempt"] == 1
    assert len(engine.execution_log) == 1


def test_recovery_retry_limit_enforcement():
    twin = SpacecraftTwin()
    engine = RecoveryEngine(twin, max_retries=2)
    
    act = RecoveryActionType.RETRY_COMM_TRANSMISSION.value
    # Attempt 1
    engine.execute_recovery(act, authorized_by="TEST")
    # Attempt 2
    engine.execute_recovery(act, authorized_by="TEST")
    # Attempt 3: Exceeds max_retries=2
    res3 = engine.execute_recovery(act, authorized_by="TEST")
    
    assert res3["status"] == "BLOCKED_MAX_RETRIES_EXCEEDED"


def test_recovery_verification_empirical_evidence():
    twin = SpacecraftTwin()
    verifier = RecoveryVerifier(twin)
    
    pre_telem = twin.get_telemetry()
    pre_telem["battery_temperature"] = 46.0  # Abnormally high
    
    # Simulate twin returning to nominal 24°C
    twin.thermal.battery_temperature = 24.0
    twin.step(1.0)
    
    verif_res = verifier.verify_recovery(
        action_name="ACTIVATE_AUX_COOLING",
        target_parameter="battery_temperature",
        pre_telemetry=pre_telem
    )
    assert verif_res["outcome"] in [VerificationOutcome.SUCCESS, VerificationOutcome.IN_PROGRESS]
    assert verif_res["improved"] is True
    assert verif_res["post_value"] < 46.0

