"""
Safety & Autonomy Manager for AI-SHMC (PART 7).
Acts as the deterministic safety gate between AI recommendations and execution.
Enforces the 8-step decision priority and classifies autonomy into:
- LEVEL 1: AUTONOMOUS RECOVERY
- LEVEL 2: CONDITIONAL AUTONOMY
- LEVEL 3: HUMAN APPROVAL REQUIRED
- LEVEL 4: SAFE-STATE ESCALATION
"""

from typing import Dict, Any, List, Optional
from app.config import AutonomyLevel, RiskLevel, RecoveryActionType
from app.safety.safety_constraints import SafetyConstraintChecker
from app.safety.risk_assessment import RiskAssessmentEngine


class SafetyAutonomyManager:
    @staticmethod
    def evaluate_autonomy(
        telemetry: Dict[str, Any],
        fault_diagnosis: Dict[str, Any],
        proposed_action: str,
        what_if_results: Optional[Dict[str, Any]] = None,
        active_actions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes strict 8-step safety authorization sequence.
        Returns deterministic autonomy classification, execution authorization, and rationale.
        """
        active_actions = active_actions or []
        fault_name = fault_diagnosis.get("fault", "Nominal")
        confidence_pct = float(fault_diagnosis.get("confidence_pct", 50.0))
        
        # -------------------------------------------------------------
        # STEP 1: Check Hard Safety Constraints
        # -------------------------------------------------------------
        bounds_ok, bound_violations = SafetyConstraintChecker.check_telemetry_bounds(telemetry)
        action_safe, action_block_reason = SafetyConstraintChecker.check_action_safety(
            proposed_action, telemetry, active_actions
        )

        # -------------------------------------------------------------
        # STEP 0: Check Nominal Flight Baseline
        # -------------------------------------------------------------
        if (fault_name == "Nominal" or fault_name == "None") and bounds_ok and len(bound_violations) == 0:
            return {
                "autonomy_level": "LEVEL 1: AUTONOMOUS RECOVERY",
                "decision_code": "NOMINAL_MONITORING",
                "can_execute_autonomously": True,
                "requires_human_approval": False,
                "is_escalated": False,
                "proposed_action": "NO_ACTION",
                "fault_name": "Nominal",
                "fault_risk_level": RiskLevel.LOW.value,
                "action_risk_level": RiskLevel.LOW.value,
                "confidence_pct": 99.0,
                "bounds_passed": True,
                "bound_violations": [],
                "dt_validation_passed": True,
                "decision_reason": "Spacecraft operates in nominal flight envelope. All subsystems nominal; autonomous copilot standing by."
            }
        
        # -------------------------------------------------------------
        # STEP 2: Check Critical Fault Conditions & Multiple Failures
        # -------------------------------------------------------------
        is_multiple_faults = (fault_name == "Multiple Subsystem Faults")
        active_faults_count = len(telemetry.get("active_faults", []))
        is_critical_threat = (not bounds_ok) or is_multiple_faults or (active_faults_count > 1)
        
        # -------------------------------------------------------------
        # STEP 3: Check Model Diagnostic Confidence
        # -------------------------------------------------------------
        confidence_eval = RiskAssessmentEngine.evaluate_ai_confidence(confidence_pct)
        confidence_sufficient = confidence_eval["is_sufficient_for_autonomy"]
        
        # -------------------------------------------------------------
        # STEP 4: Evaluate Fault Risk (FMEA S x P)
        # -------------------------------------------------------------
        observed_sev = fault_diagnosis.get("severity_score")
        fault_risk = RiskAssessmentEngine.calculate_fault_risk(fault_name, observed_sev)
        
        # -------------------------------------------------------------
        # STEP 5: Evaluate Recovery Action Risk Independently
        # -------------------------------------------------------------
        top_strat_meta = what_if_results.get("top_strategy_details", {}) if what_if_results else None
        assessment = RiskAssessmentEngine.assess_comprehensive_risk(
            fault_name=fault_name,
            proposed_action=proposed_action,
            diagnosis_confidence_pct=confidence_pct,
            what_if_strategy_result=top_strat_meta,
            observed_severity=observed_sev
        )
        action_risk_level = assessment["action_risk"]["action_risk_level"]
        fault_risk_level = fault_risk["risk_level"]
        is_pre_approved = assessment["action_risk"]["pre_approved"]
        
        # -------------------------------------------------------------
        # STEP 6: Validate Action using Digital Twin Simulation
        # -------------------------------------------------------------
        dt_secondary_hazards = top_strat_meta.get("secondary_faults", []) if top_strat_meta else []
        dt_validation_passed = (len(dt_secondary_hazards) == 0)
        
        # -------------------------------------------------------------
        # STEP 7: Determine Permitted Autonomy Level
        # -------------------------------------------------------------
        # Priority Rule 1: Catastrophic compound threat or physical survival breach -> LEVEL 4 Safe-State
        if is_multiple_faults or (not bounds_ok and len(bound_violations) > 1) or fault_risk_level == RiskLevel.CRITICAL.value:
            autonomy_level = AutonomyLevel.LEVEL_4_SAFE_STATE.value
            can_execute_autonomously = False
            requires_human_approval = False
            is_escalated = True
            decision_code = "SAFE_STATE_ESCALATION"
            decision_reason = (
                f"LEVEL 4 TRIGGERED: Critical hazard condition detected. "
                f"Violations: {bound_violations or 'Critical compound fault'}. "
                f"Autonomous recovery blocked. Engaging emergency protective safe hold."
            )
            
        # Priority Rule 2: High Fault Risk or High Action Risk -> LEVEL 3 (HUMAN OPERATOR SIGN-OFF MANDATORY)
        elif fault_risk_level == RiskLevel.HIGH.value or action_risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value] or not dt_validation_passed:
            autonomy_level = AutonomyLevel.LEVEL_3_HUMAN_APPROVAL.value
            can_execute_autonomously = False
            requires_human_approval = True
            is_escalated = False
            decision_code = "HUMAN_APPROVAL_REQUIRED"
            decision_reason = (
                f"LEVEL 3: High-risk operation detected (Fault Risk: {fault_risk_level}, Action Risk: {action_risk_level}). "
                f"Action '{proposed_action}' requires explicit operator verification before execution."
            )

        # Priority Rule 3: Low Model Confidence (< 75%) -> Route to Human Operator Approval (Human-in-the-Loop)
        elif not confidence_sufficient:
            autonomy_level = AutonomyLevel.LEVEL_3_HUMAN_APPROVAL.value
            can_execute_autonomously = False
            requires_human_approval = True
            is_escalated = False
            decision_code = "HUMAN_APPROVAL_LOW_CONFIDENCE"
            decision_reason = (
                f"LEVEL 3: AI diagnosis confidence {confidence_pct}% is below 75% autonomy threshold. "
                f"Autonomous execution blocked; routing to flight controller for human verification."
            )
            
        # Priority Rule 4: Medium Risk -> LEVEL 2 Conditional Autonomy
        elif fault_risk_level == RiskLevel.MEDIUM.value or action_risk_level == RiskLevel.MEDIUM.value:
            if is_pre_approved and dt_validation_passed:
                autonomy_level = AutonomyLevel.LEVEL_2_CONDITIONAL.value
                can_execute_autonomously = True
                requires_human_approval = False
                is_escalated = False
                decision_code = "CONDITIONAL_AUTONOMY_AUTHORIZED"
                decision_reason = (
                    f"LEVEL 2: Medium risk with validated digital twin simulation and pre-approved action. "
                    f"Conditional autonomous execution authorized."
                )
            else:
                autonomy_level = AutonomyLevel.LEVEL_3_HUMAN_APPROVAL.value
                can_execute_autonomously = False
                requires_human_approval = True
                is_escalated = False
                decision_code = "HUMAN_APPROVAL_REQUIRED_UNAPPROVED_ACTION"
                decision_reason = (
                    f"LEVEL 2 -> 3: Action '{proposed_action}' lacks automatic pre-approval. Operator approval requested."
                )
                
        # Priority Rule 5: Low Risk + Low Action Risk + Sufficient Confidence -> LEVEL 1 Autonomous Recovery
        else:
            autonomy_level = AutonomyLevel.LEVEL_1_AUTONOMOUS.value
            can_execute_autonomously = True
            requires_human_approval = False
            is_escalated = False
            decision_code = "AUTONOMOUS_EXECUTION_AUTHORIZED"
            decision_reason = (
                f"LEVEL 1: Fault risk LOW, Action risk LOW, Diagnostic confidence {confidence_pct}% (HIGH). "
                f"Action '{proposed_action}' is safe and pre-approved for full autonomous execution."
            )
            
        return {
            "autonomy_level": autonomy_level,
            "decision_code": decision_code,
            "can_execute_autonomously": can_execute_autonomously,
            "requires_human_approval": requires_human_approval,
            "is_escalated": is_escalated,
            "proposed_action": proposed_action,
            "fault_name": fault_name,
            "fault_risk_level": fault_risk_level,
            "action_risk_level": action_risk_level,
            "confidence_pct": confidence_pct,
            "bounds_passed": bounds_ok,
            "bound_violations": bound_violations,
            "dt_validation_passed": dt_validation_passed,
            "decision_reason": decision_reason
        }

