"""
AI-SHMC Decision Engine: Core Autonomous Copilot Pipeline Orchestrator.
Implements the 8-stage operational workflow:
DETECT -> DIAGNOSE -> PREDICT -> SIMULATE -> ASSESS RISK -> DECIDE -> SELF-HEAL -> VERIFY
"""

from typing import Dict, Any, Optional
from datetime import datetime

from app.simulation.spacecraft_twin import SpacecraftTwin
from app.ai_models.anomaly_detection import AnomalyDetector
from app.ai_models.fault_diagnosis import FaultDiagnoser
from app.ai_models.prediction import TelemetryPredictor
from app.intelligence.what_if_simulator import WhatIfSimulator
from app.safety.safety_autonomy_manager import SafetyAutonomyManager
from app.recovery.recovery_engine import RecoveryEngine
from app.recovery.human_approval import HumanApprovalManager, OperatorDecision
from app.recovery.recovery_verification import RecoveryVerifier, VerificationOutcome


class MissionControlDecisionEngine:
    def __init__(
        self,
        twin: SpacecraftTwin,
        detector: Optional[AnomalyDetector] = None,
        diagnoser: Optional[FaultDiagnoser] = None,
        predictor: Optional[TelemetryPredictor] = None
    ):
        self.twin = twin
        
        # Load or initialize AI models
        self.detector = detector or AnomalyDetector()
        if not self.detector.is_fitted:
            self.detector.load("models/anomaly_detector.joblib")
            
        self.diagnoser = diagnoser or FaultDiagnoser()
        if not self.diagnoser.is_fitted:
            self.diagnoser.load("models/fault_diagnoser.joblib")
            
        self.predictor = predictor or TelemetryPredictor()
        if not self.predictor.is_fitted:
            self.predictor.load("models/telemetry_predictor.joblib")
            
        # Core engines
        self.what_if_sim = WhatIfSimulator(simulation_horizon_seconds=60.0)
        self.recovery_engine = RecoveryEngine(self.twin)
        self.approval_manager = HumanApprovalManager()
        self.verifier = RecoveryVerifier(self.twin)
        
        # Historical mission cycle log
        self.cycle_history = []

    def run_copilot_cycle(self, auto_execute_level_1: bool = True) -> Dict[str, Any]:
        """
        Executes one full end-to-end mission control cycle:
        1. DETECT: Ingest live telemetry and detect anomalies
        2. DIAGNOSE: Identify probable fault category and confidence
        3. PREDICT: Forecast future subsystem trends
        4. SIMULATE: Run isolated Digital Twin What-If simulations
        5. ASSESS RISK: Evaluate independent fault and action risks
        6. DECIDE: Determine permitted autonomy level
        7. SELF-HEAL: Execute Level 1/2 recovery or submit Level 3 approval request
        8. VERIFY: Confirm recovery or escalate
        """
        now_ts = datetime.utcnow().isoformat()
        
        # 1. LIVE TELEMETRY INGESTION
        telemetry = self.twin.get_telemetry()
        
        # 2. DETECT
        anomaly_result = self.detector.detect(telemetry)
        
        # 3. DIAGNOSE
        if anomaly_result["is_anomaly"]:
            diagnosis_result = self.diagnoser.diagnose(telemetry)
        else:
            diagnosis_result = {
                "fault": "Nominal",
                "affected_subsystem": "None",
                "confidence_pct": 99.0,
                "confidence_level": "HIGH",
                "severity_score": 1,
                "severity_label": "Negligible",
                "explanation": "All subsystems operating within nominal flight envelope."
            }
            
        # 4. PREDICT
        prediction_result = self.predictor.predict(telemetry, horizon_minutes=3)
        
        # 5. SIMULATE (Digital Twin What-If Analysis)
        diagnosed_fault = diagnosis_result["fault"]
        if diagnosed_fault != "Nominal":
            what_if_result = self.what_if_sim.evaluate_candidates(self.twin, diagnosed_fault)
            recommended_action = what_if_result["top_recommended_strategy"]
        else:
            what_if_result = None
            recommended_action = "NO_ACTION"
            
        # 6. DECIDE AUTONOMY & ASSESS RISK
        autonomy_decision = SafetyAutonomyManager.evaluate_autonomy(
            telemetry=telemetry,
            fault_diagnosis=diagnosis_result,
            proposed_action=recommended_action,
            what_if_results=what_if_result,
            active_actions=self.recovery_engine.active_actions
        )
        
        recovery_execution_record = None
        verification_record = None
        approval_request_record = None
        
        # 7. SELF-HEAL / HUMAN APPROVAL GATE
        if diagnosed_fault != "Nominal" and recommended_action != "NO_ACTION":
            # Level 1 or Level 2 Authorized Autonomy
            if autonomy_decision["can_execute_autonomously"] and auto_execute_level_1:
                # Execute recovery command
                auth_tag = autonomy_decision["autonomy_level"].split(":")[0]
                recovery_execution_record = self.recovery_engine.execute_recovery(
                    action_name=recommended_action,
                    authorized_by=auth_tag
                )
                
                # 8. VERIFY
                target_param = anomaly_result.get("primary_parameter") or "battery_temperature"
                verification_record = self.verifier.verify_recovery(
                    action_name=recommended_action,
                    target_parameter=target_param,
                    pre_telemetry=telemetry
                )
                
            # Level 3 Human Approval Required
            elif autonomy_decision["requires_human_approval"] and not autonomy_decision["is_escalated"]:
                target_param = anomaly_result.get("primary_parameter") or "battery_temperature"
                predicted_consequence = (
                    f"Parameter '{target_param}' predicted to reach "
                    f"{prediction_result['predictions'].get(target_param, {}).get('predicted_value', 'Critical')} "
                    f"in 3 mins. Trend: {prediction_result['overall_risk_trend']}."
                )
                
                approval_request_record = self.approval_manager.create_approval_request(
                    detected_fault=diagnosed_fault,
                    affected_subsystem=diagnosis_result["affected_subsystem"],
                    fault_severity=diagnosis_result["severity_score"],
                    fault_risk_score=autonomy_decision["fault_risk_level"],
                    recovery_action_risk=autonomy_decision["action_risk_level"],
                    ai_confidence_pct=diagnosis_result["confidence_pct"],
                    predicted_consequences=predicted_consequence,
                    available_recovery_strategies=what_if_result["evaluated_strategies"] if what_if_result else [],
                    recommended_recovery_action=recommended_action,
                    reason_for_recommendation=what_if_result["selection_reason"] if what_if_result else "Safety mitigation"
                )
                
            # Level 4 Safe-State Escalation
            elif autonomy_decision["is_escalated"]:
                # Execute emergency safe-state procedure
                recovery_execution_record = self.recovery_engine.execute_recovery(
                    action_name="ENTER_SAFE_HOLD",
                    authorized_by="LEVEL_4_EMERGENCY_PROTECTION",
                    bypass_safety_check=True
                )
                verification_record = self.verifier.verify_recovery(
                    action_name="ENTER_SAFE_HOLD",
                    target_parameter="battery_temperature",
                    pre_telemetry=telemetry
                )
                
        cycle_result = {
            "timestamp": now_ts,
            "telemetry": telemetry,
            "anomaly_detection": anomaly_result,
            "fault_diagnosis": diagnosis_result,
            "predictive_analytics": prediction_result,
            "what_if_simulation": what_if_result,
            "autonomy_decision": autonomy_decision,
            "recovery_execution": recovery_execution_record,
            "verification": verification_record,
            "pending_approval": approval_request_record
        }
        
        self.cycle_history.append(cycle_result)
        return cycle_result

