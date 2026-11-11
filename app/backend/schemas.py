"""
Pydantic Schemas for AI-SHMC FastAPI Backend.
Validates telemetry input, fault injection, approval requests, and API payloads.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TelemetryFrame(BaseModel):
    timestamp: str
    simulation_time: float
    spacecraft_id: str
    overall_health_score: float
    subsystem_status: str
    fault_label: str
    fault_severity: int
    battery_voltage: float
    battery_temperature: float
    battery_charge: float
    solar_current: float
    power_consumption: float
    cpu_temperature: float
    cpu_usage: float
    memory_usage: float
    signal_strength: float
    packet_loss: float
    communication_latency: float
    storage_usage: float
    payload_activity: float
    subsystem_health: Optional[Dict[str, str]] = None
    active_faults: Optional[List[str]] = None


class FaultInjectionRequest(BaseModel):
    scenario_id: int = Field(..., ge=1, le=10, description="Scenario ID 1 to 10")
    intensity: float = Field(1.0, ge=0.1, le=3.0, description="Fault magnitude scalar")


class SimulationSpeedRequest(BaseModel):
    speed_factor: float = Field(1.0, ge=0.1, le=20.0, description="Simulation acceleration multiplier")


class OperatorDecisionRequest(BaseModel):
    decision: str = Field(..., description="APPROVED, REJECTED, or REQUEST_ADDITIONAL_SIMULATION")
    operator_id: str = Field("FLIGHT_DIRECTOR_01", description="Identifier of the approving flight controller")
    operator_notes: Optional[str] = Field("", description="Justification or flight notes")


class RecoveryExecutionRequest(BaseModel):
    action_name: str
    authorized_by: str = "MANUAL_OPERATOR"
    bypass_safety: bool = False


class WhatIfRequest(BaseModel):
    fault_category: str
    simulation_horizon_s: float = 60.0
    candidate_actions: Optional[List[str]] = None


class MissionEventFilter(BaseModel):
    subsystem: Optional[str] = None
    risk_level: Optional[str] = None
    event_type: Optional[str] = None
    limit: int = 100

