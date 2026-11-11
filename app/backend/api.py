"""
FastAPI REST API Service for AI-SHMC.
Exposes modular spacecraft simulation controls, AI model inference, Digital Twin what-if,
safety and autonomy gates, operator approvals, recovery execution, and event log endpoints.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc

from app.config import SubsystemName, FaultCategory, RecoveryActionType
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.simulation.fault_injector import FaultInjector
from app.ai_models.anomaly_detection import AnomalyDetector
from app.ai_models.fault_diagnosis import FaultDiagnoser
from app.ai_models.prediction import TelemetryPredictor
from app.intelligence.decision_engine import MissionControlDecisionEngine
from app.recovery.human_approval import OperatorDecision
from app.backend.schemas import (
    TelemetryFrame,
    FaultInjectionRequest,
    SimulationSpeedRequest,
    OperatorDecisionRequest,
    RecoveryExecutionRequest,
    WhatIfRequest
)
from app.backend.database import (
    SessionLocal,
    init_db,
    log_mission_event,
    TelemetryRecordDB,
    AnomalyEventDB,
    FaultDiagnosisDB,
    PredictionDB,
    RiskAssessmentDB,
    RecoveryActionDB,
    OperatorApprovalDB,
    RecoveryVerificationDB,
    MissionEventLogDB
)


# Initialize Database
init_db()

# Instantiate Singletons for the live spacecraft session
live_twin = SpacecraftTwin()
fault_injector = FaultInjector(live_twin)

# AI Models
detector = AnomalyDetector()
detector.load("models/anomaly_detector.joblib")

diagnoser = FaultDiagnoser()
diagnoser.load("models/fault_diagnoser.joblib")

predictor = TelemetryPredictor()
predictor.load("models/telemetry_predictor.joblib")

# Copilot Decision Engine
copilot = MissionControlDecisionEngine(
    twin=live_twin,
    detector=detector,
    diagnoser=diagnoser,
    predictor=predictor
)

# FastAPI Application
app = FastAPI(
    title="AI-SHMC Spacecraft Mission Control API",
    description="Autonomous Spacecraft Health Monitoring and Self-Healing Copilot Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "project": "AI-SHMC",
        "name": "AI-Based Self-Healing Mission Control Copilot for Autonomous Spacecraft Operations",
        "status": "OPERATIONAL",
        "spacecraft_id": live_twin.spacecraft_id,
        "docs_url": "/docs"
    }


# =====================================================================
# SIMULATION & TELEMETRY ENDPOINTS
# =====================================================================

@app.get("/api/telemetry/current", response_model=TelemetryFrame)
def get_current_telemetry():
    """Returns the instantaneous telemetry frame from all six subsystems."""
    return live_twin.get_telemetry()


@app.post("/api/simulation/step")
def step_simulation(dt_seconds: float = 1.0):
    """Manually steps the spacecraft simulation forward."""
    telem = live_twin.step(dt_seconds)
    # Log to DB
    db = SessionLocal()
    try:
        rec = TelemetryRecordDB(
            timestamp=telem["timestamp"],
            simulation_time=telem["simulation_time"],
            spacecraft_id=telem["spacecraft_id"],
            overall_health_score=telem["overall_health_score"],
            subsystem_status=telem["subsystem_status"],
            fault_label=telem["fault_label"],
            fault_severity=telem["fault_severity"],
            battery_voltage=telem["battery_voltage"],
            battery_temperature=telem["battery_temperature"],
            battery_charge=telem["battery_charge"],
            solar_current=telem["solar_current"],
            power_consumption=telem["power_consumption"],
            cpu_temperature=telem["cpu_temperature"],
            cpu_usage=telem["cpu_usage"],
            memory_usage=telem["memory_usage"],
            signal_strength=telem["signal_strength"],
            packet_loss=telem["packet_loss"],
            communication_latency=telem["communication_latency"],
            storage_usage=telem["storage_usage"],
            payload_activity=telem["payload_activity"]
        )
        db.add(rec)
        db.commit()
    finally:
        db.close()
    return telem


@app.post("/api/simulation/pause")
def pause_simulation():
    live_twin.is_paused = True
    return {"status": "PAUSED"}


@app.post("/api/simulation/resume")
def resume_simulation():
    live_twin.is_paused = False
    return {"status": "RESUMED"}


@app.post("/api/simulation/reset")
def reset_simulation():
    global live_twin, fault_injector, copilot
    live_twin = SpacecraftTwin()
    fault_injector = FaultInjector(live_twin)
    copilot = MissionControlDecisionEngine(live_twin, detector, diagnoser, predictor)
    return {"status": "RESET_COMPLETED"}


@app.post("/api/simulation/speed")
def set_simulation_speed(req: SimulationSpeedRequest):
    live_twin.time_acceleration = req.speed_factor
    return {"speed_factor": live_twin.time_acceleration}


@app.get("/api/simulation/scenarios")
def get_fault_scenarios():
    """Returns the catalog of 10 supported fault scenarios."""
    return FaultInjector.get_catalog()


@app.post("/api/simulation/inject_fault")
def inject_fault(req: FaultInjectionRequest):
    """Injects one of the 10 preset fault scenarios into the active twin."""
    res = fault_injector.inject_scenario(req.scenario_id, req.intensity)
    log_mission_event(
        subsystem=res.get("affected_subsystem", "Simulation"),
        event_type="FAULT_INJECTION",
        risk_level="HIGH" if req.scenario_id in [1, 2, 4, 10] else "MEDIUM",
        message=f"Injected Scenario {req.scenario_id}: {res['name']}",
        details=res
    )
    return res


@app.post("/api/simulation/clear_faults")
def clear_all_faults():
    res = fault_injector.clear_all_faults()
    log_mission_event(
        subsystem="Simulation",
        event_type="FAULT_CLEAR",
        risk_level="LOW",
        message="All active simulated faults cleared."
    )
    return res


# =====================================================================
# AI / ML MODULE INFERENCE ENDPOINTS
# =====================================================================

@app.get("/api/ai/anomaly")
def run_anomaly_detection():
    telem = live_twin.get_telemetry()
    res = detector.detect(telem)
    if res["is_anomaly"]:
        log_mission_event(
            subsystem=res["primary_subsystem"],
            event_type="ANOMALY",
            risk_level="HIGH" if res["anomaly_score"] > 0.7 else "MEDIUM",
            message=res["summary"],
            details=res
        )
    return res


@app.get("/api/ai/diagnose")
def run_fault_diagnosis():
    telem = live_twin.get_telemetry()
    res = diagnoser.diagnose(telem)
    return res


@app.get("/api/ai/predict")
def run_telemetry_prediction(horizon_minutes: int = Query(3, ge=1, le=10)):
    telem = live_twin.get_telemetry()
    res = predictor.predict(telem, horizon_minutes)
    return res


# =====================================================================
# DIGITAL TWIN WHAT-IF SIMULATION
# =====================================================================

@app.post("/api/digital_twin/what_if")
def run_what_if_simulation(req: WhatIfRequest):
    """
    Executes What-If forward sandbox evaluation on candidate recovery strategies.
    Guarantees that live spacecraft state is unmutated!
    """
    res = copilot.what_if_sim.evaluate_candidates(
        live_twin=live_twin,
        diagnosed_fault=req.fault_category,
        custom_candidates=req.candidate_actions
    )
    return res


# =====================================================================
# SAFETY & AUTONOMY ENDPOINTS
# =====================================================================

@app.get("/api/safety/autonomy_decision")
def get_autonomy_decision():
    """Evaluates current telemetry against the 8-stage deterministic safety gate."""
    telem = live_twin.get_telemetry()
    anom = detector.detect(telem)
    diag = diagnoser.diagnose(telem) if anom["is_anomaly"] else {
        "fault": "Nominal", "confidence_pct": 99.0, "severity_score": 1
    }
    
    proposed_action = "NO_ACTION"
    what_if_res = None
    if diag["fault"] != "Nominal":
        what_if_res = copilot.what_if_sim.evaluate_candidates(live_twin, diag["fault"])
        proposed_action = what_if_res["top_recommended_strategy"]
        
    decision = copilot.approval_manager
    autonomy_res = copilot.what_if_sim
    from app.safety.safety_autonomy_manager import SafetyAutonomyManager
    res = SafetyAutonomyManager.evaluate_autonomy(
        telemetry=telem,
        fault_diagnosis=diag,
        proposed_action=proposed_action,
        what_if_results=what_if_res,
        active_actions=copilot.recovery_engine.active_actions
    )
    return res


# =====================================================================
# HUMAN-IN-THE-LOOP APPROVAL ENDPOINTS
# =====================================================================

@app.get("/api/approval/pending")
def get_pending_approvals():
    """Lists all pending operator approval requests."""
    return copilot.approval_manager.get_pending_requests()


@app.post("/api/approval/{request_id}/decide")
def submit_operator_decision(request_id: str, req: OperatorDecisionRequest):
    """
    Operator submits decision: APPROVED, REJECTED, or REQUEST_ADDITIONAL_SIMULATION.
    If APPROVED, dispatches recovery action to recovery engine.
    """
    try:
        decision_enum = OperatorDecision(req.decision)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid decision: {req.decision}")
        
    result = copilot.approval_manager.submit_decision(
        request_id=request_id,
        decision=decision_enum,
        operator_id=req.operator_id,
        operator_notes=req.operator_notes
    )
    
    # If approved, dispatch recovery execution
    execution_result = None
    verification_result = None
    if decision_enum == OperatorDecision.APPROVED:
        action_name = result["recommended_recovery_action"]
        execution_result = copilot.recovery_engine.execute_recovery(
            action_name=action_name,
            authorized_by=f"OPERATOR_{req.operator_id}"
        )
        # Verify recovery
        verification_result = copilot.verifier.verify_recovery(
            action_name=action_name,
            target_parameter="battery_temperature",
            pre_telemetry=execution_result["pre_telemetry"]
        )
        
    log_mission_event(
        subsystem=result["affected_subsystem"],
        event_type="OPERATOR_DECISION",
        risk_level="HIGH" if decision_enum == OperatorDecision.APPROVED else "MEDIUM",
        message=f"Operator {req.operator_id} marked request {request_id} as {req.decision}",
        details={"request": result, "execution": execution_result, "verification": verification_result}
    )
    
    return {
        "approval_request": result,
        "execution": execution_result,
        "verification": verification_result
    }


# =====================================================================
# RECOVERY & VERIFICATION ENDPOINTS
# =====================================================================

@app.post("/api/recovery/execute")
def execute_recovery_action(req: RecoveryExecutionRequest):
    """Manually dispatch an authorized recovery action."""
    res = copilot.recovery_engine.execute_recovery(
        action_name=req.action_name,
        authorized_by=req.authorized_by,
        bypass_safety_check=req.bypass_safety
    )
    log_mission_event(
        subsystem="Recovery",
        event_type="RECOVERY_EXECUTION",
        risk_level="MEDIUM",
        message=f"Dispatched recovery action '{req.action_name}' ({res['status']})",
        details=res
    )
    return res


# =====================================================================
# FULL COPILOT REASONING CYCLE
# =====================================================================

@app.post("/api/copilot/cycle")
def execute_copilot_cycle(auto_execute_level_1: bool = True):
    """
    Executes one complete end-to-end mission control loop:
    DETECT -> DIAGNOSE -> PREDICT -> SIMULATE -> ASSESS RISK -> DECIDE -> SELF-HEAL -> VERIFY.
    """
    result = copilot.run_copilot_cycle(auto_execute_level_1=auto_execute_level_1)
    
    # Persist summary event to database
    telem = result["telemetry"]
    diag = result["fault_diagnosis"]
    auto = result["autonomy_decision"]
    
    if diag["fault"] != "Nominal":
        log_mission_event(
            subsystem=diag["affected_subsystem"],
            event_type="COPILOT_CYCLE",
            risk_level=auto["fault_risk_level"],
            message=f"Copilot Cycle: {diag['fault']} -> Autonomy {auto['autonomy_level']}",
            details={
                "diagnosis": diag,
                "autonomy": auto,
                "recovery": result["recovery_execution"],
                "verification": result["verification"]
            }
        )
    return result


# =====================================================================
# MISSION EVENT LOGS AND EVALUATION
# =====================================================================

@app.get("/api/events/history")
def get_mission_events(
    subsystem: Optional[str] = None,
    risk_level: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50
):
    """Retrieves auditable mission event history with optional filters."""
    db = SessionLocal()
    try:
        query = db.query(MissionEventLogDB)
        if subsystem:
            query = query.filter(MissionEventLogDB.subsystem.ilike(f"%{subsystem}%"))
        if risk_level:
            query = query.filter(MissionEventLogDB.risk_level == risk_level)
        if event_type:
            query = query.filter(MissionEventLogDB.event_type == event_type)
        events = query.order_by(desc(MissionEventLogDB.id)).limit(limit).all()
        
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "subsystem": e.subsystem,
                "event_type": e.event_type,
                "risk_level": e.risk_level,
                "message": e.message,
                "details": json.loads(e.details_json) if e.details_json else None
            }
            for e in events
        ]
    finally:
        db.close()


@app.get("/api/metrics/summary")
def get_model_evaluation_metrics():
    """Returns the trained AI model evaluation benchmark metrics."""
    metrics_path = "models/evaluation_metrics.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {"message": "Metrics not yet available. Run train_models.py."}

