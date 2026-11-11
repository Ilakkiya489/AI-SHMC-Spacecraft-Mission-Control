"""
Mission Objectives and Strategy Optimization Weights for AI-SHMC.
Defines aerospace trade-off weights between spacecraft survival,
telemetry stabilization, mission disruption, and recovery latency.
"""

from typing import Dict, Any


# Multi-Objective Optimization Weights
OBJECTIVE_WEIGHTS = {
    "safety_stabilization": 0.45,   # Priority 1: Eliminating thermal/power/comm hazards
    "mission_preservation": 0.25,   # Priority 2: Minimizing scientific payload downtime
    "action_risk_penalty": 0.20,    # Priority 3: Penalizing irreversible or hazardous actions
    "time_efficiency": 0.10         # Priority 4: Fast convergence to nominal state
}

# Subsystem critical penalties
SUBSYSTEM_WEIGHTS = {
    "power": 1.5,
    "thermal": 1.4,
    "communication": 1.2,
    "processing": 1.0,
    "storage": 0.8,
    "payload": 0.7
}


def score_recovery_strategy(
    safety_gain: float,           # 0.0 to 100.0 (improvement in health / reduction in violations)
    mission_impact: str,          # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    action_risk: str,             # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    recovery_time_s: float,       # estimated duration in seconds
    secondary_faults_count: int   # number of potential secondary hazards detected
) -> float:
    """
    Computes an objective fitness score from 0.0 to 100.0 for a candidate recovery strategy.
    Penalizes high mission impact, high action risk, and secondary faults.
    """
    impact_penalties = {
        "LOW": 5.0,
        "MEDIUM": 20.0,
        "HIGH": 45.0,
        "CRITICAL": 80.0
    }
    
    risk_penalties = {
        "LOW": 5.0,
        "MEDIUM": 25.0,
        "HIGH": 50.0,
        "CRITICAL": 90.0
    }
    
    time_penalty = min(20.0, (recovery_time_s / 60.0) * 10.0)
    secondary_penalty = secondary_faults_count * 35.0
    
    w = OBJECTIVE_WEIGHTS
    score = (
        (w["safety_stabilization"] * safety_gain)
        - (w["mission_preservation"] * impact_penalties.get(mission_impact, 20.0))
        - (w["action_risk_penalty"] * risk_penalties.get(action_risk, 25.0))
        - (w["time_efficiency"] * time_penalty)
        - secondary_penalty
    )
    
    return max(0.0, min(100.0, round(score, 2)))

