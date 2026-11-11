"""
Recovery Verification and Escalation Engine for AI-SHMC (PART 10).
Performs empirical post-recovery telemetry analysis.
Verifies telemetry delta improvement, validates secondary subsystem stability,
and manages operator escalation upon failed operations.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import TELEMETRY_SPECS
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.safety.safety_constraints import SafetyConstraintChecker


class VerificationOutcome:
    SUCCESS = "RECOVERY_SUCCESSFUL"
    IN_PROGRESS = "RECOVERY_IN_PROGRESS"
    FAILED = "RECOVERY_FAILED"
    SECONDARY_FAULT = "SECONDARY_FAULT_DETECTED"
    ESCALATION_REQUIRED = "OPERATOR_ESCALATION_REQUIRED"


class RecoveryVerifier:
    def __init__(self, twin: SpacecraftTwin):
        self.twin = twin
        self.verification_history: List[Dict[str, Any]] = []

    def verify_recovery(
        self,
        action_name: str,
        target_parameter: str,
        pre_telemetry: Dict[str, Any],
        post_telemetry: Optional[Dict[str, Any]] = None,
        settling_time_s: float = 3.0
    ) -> Dict[str, Any]:
        """
        Gathers post-recovery telemetry and conducts empirical verification.
        Requires quantifiable evidence before certifying success.
        """
        # Step twin slightly to observe settled physical response
        self.twin.step(settling_time_s)
        current_telemetry = post_telemetry or self.twin.get_telemetry()
        now_ts = datetime.utcnow().isoformat()
        
        # 1. Evaluate Target Parameter Improvement
        pre_val = float(pre_telemetry.get(target_parameter, 0.0))
        post_val = float(current_telemetry.get(target_parameter, 0.0))
        delta = post_val - pre_val
        spec = TELEMETRY_SPECS.get(target_parameter, {})
        nom_min = spec.get("nominal_min", -9999.0)
        nom_max = spec.get("nominal_max", 9999.0)
        
        # Target parameter improvement logic
        improved = False
        if "temperature" in target_parameter or "loss" in target_parameter or "consumption" in target_parameter:
            # Lower is better
            improved = (post_val < pre_val) or (nom_min <= post_val <= nom_max)
        elif target_parameter in ["battery_voltage", "battery_charge", "signal_strength"]:
            # Higher is better
            improved = (post_val > pre_val) or (nom_min <= post_val <= nom_max)
        else:
            improved = (nom_min <= post_val <= nom_max)
            
        # 2. Check Secondary Subsystem Hazards
        bounds_ok, bound_violations = SafetyConstraintChecker.check_telemetry_bounds(current_telemetry)
        
        # 3. Check Overall Spacecraft Health Score Gain
        health_gain = current_telemetry["overall_health_score"] - pre_telemetry["overall_health_score"]
        
        # 4. Determine Verification Verdict
        if not bounds_ok:
            outcome = VerificationOutcome.SECONDARY_FAULT
            summary = f"CRITICAL: Recovery action triggered secondary constraint violations: {bound_violations}"
        elif improved and current_telemetry["subsystem_status"] in ["NOMINAL", "DEGRADED"]:
            if current_telemetry["overall_health_score"] >= 80.0:
                outcome = VerificationOutcome.SUCCESS
                summary = (
                    f"RECOVERY SUCCESSFUL: Parameter '{target_parameter}' improved from {pre_val} to {post_val}. "
                    f"Spacecraft Health Score: {current_telemetry['overall_health_score']}%."
                )
            else:
                outcome = VerificationOutcome.IN_PROGRESS
                summary = (
                    f"RECOVERY IN PROGRESS: Parameter '{target_parameter}' improved to {post_val}. "
                    f"Health Score {current_telemetry['overall_health_score']}% still converging."
                )
        else:
            outcome = VerificationOutcome.FAILED
            summary = (
                f"RECOVERY FAILED: Parameter '{target_parameter}' did not return to nominal. "
                f"Pre: {pre_val}, Post: {post_val}. Escalation to operator required."
            )
            
        record = {
            "timestamp": now_ts,
            "action_executed": action_name,
            "target_parameter": target_parameter,
            "outcome": outcome,
            "pre_value": pre_val,
            "post_value": post_val,
            "delta": round(delta, 2),
            "improved": improved,
            "health_score_gain": round(health_gain, 1),
            "current_health_score": current_telemetry["overall_health_score"],
            "secondary_violations": bound_violations,
            "summary": summary
        }
        self.verification_history.append(record)
        return record

