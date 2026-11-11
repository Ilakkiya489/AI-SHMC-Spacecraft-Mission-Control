"""
Digital Twin What-If Simulation Engine for AI-SHMC.
Evaluates candidate spacecraft recovery strategies in an isolated sandbox clone
prior to actual execution. Guarantees zero mutation of the live spacecraft twin.
"""

from typing import Dict, Any, List, Optional
from app.config import (
    FAULT_RECOVERY_CANDIDATES,
    RECOVERY_ACTIONS_METADATA,
    RecoveryActionType,
    TELEMETRY_SPECS
)
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.intelligence.mission_objectives import score_recovery_strategy


class WhatIfSimulator:
    def __init__(self, simulation_horizon_seconds: float = 60.0):
        self.simulation_horizon_seconds = simulation_horizon_seconds

    def evaluate_candidates(
        self,
        live_twin: SpacecraftTwin,
        diagnosed_fault: str,
        custom_candidates: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs forward What-If simulations for baseline non-intervention and
        all candidate recovery actions against isolated clones of live_twin.
        """
        candidates = custom_candidates or FAULT_RECOVERY_CANDIDATES.get(
            diagnosed_fault,
            [RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value, RecoveryActionType.ENTER_SAFE_HOLD.value]
        )
        
        # Always evaluate NO_ACTION baseline
        if RecoveryActionType.NO_ACTION.value not in candidates:
            candidates = [RecoveryActionType.NO_ACTION.value] + candidates
            
        initial_telemetry = live_twin.get_telemetry()
        results: List[Dict[str, Any]] = []
        
        for action in candidates:
            # 1. Deep-copy clone to guarantee sandbox isolation
            twin_clone = live_twin.clone()
            
            # 2. Apply action if not NO_ACTION
            action_meta = RECOVERY_ACTIONS_METADATA.get(action, {})
            action_risk = action_meta.get("action_risk", "MEDIUM")
            mission_disruption = action_meta.get("mission_disruption", "MEDIUM")
            expected_duration = action_meta.get("expected_duration_s", 10)
            
            if action != RecoveryActionType.NO_ACTION.value:
                twin_clone.apply_recovery_action(action)
                
            # 3. Simulate forward in time
            dt = 1.0
            steps = int(self.simulation_horizon_seconds / dt)
            for _ in range(steps):
                twin_clone.step(dt)
                
            post_telem = twin_clone.get_telemetry()
            
            # 4. Analyze secondary effects & safety metrics
            secondary_faults = self._check_secondary_faults(post_telem)
            health_gain = max(0.0, post_telem["overall_health_score"] - initial_telemetry["overall_health_score"])
            
            if action == RecoveryActionType.NO_ACTION.value:
                # Baseline non-intervention degradation
                health_gain = 0.0
                mission_disruption = "LOW"
                action_risk = "LOW"
                
            fitness_score = score_recovery_strategy(
                safety_gain=post_telem["overall_health_score"],
                mission_impact=mission_disruption,
                action_risk=action_risk,
                recovery_time_s=expected_duration,
                secondary_faults_count=len(secondary_faults)
            )
            
            results.append({
                "action": action,
                "description": action_meta.get("description", "Execute recovery procedure."),
                "action_risk": action_risk,
                "mission_disruption": mission_disruption,
                "expected_duration_s": expected_duration,
                "projected_battery_temp": post_telem["battery_temperature"],
                "projected_battery_voltage": post_telem["battery_voltage"],
                "projected_battery_charge": post_telem["battery_charge"],
                "projected_power_consumption": post_telem["power_consumption"],
                "projected_comm_signal": post_telem["signal_strength"],
                "projected_packet_loss": post_telem["packet_loss"],
                "projected_payload_activity": post_telem["payload_activity"],
                "projected_health_score": post_telem["overall_health_score"],
                "secondary_faults": secondary_faults,
                "fitness_score": fitness_score
            })
            
        # 5. Rank strategies (excluding NO_ACTION from top unless no better option)
        active_candidates = [r for r in results if r["action"] != RecoveryActionType.NO_ACTION.value]
        if active_candidates:
            ranked = sorted(active_candidates, key=lambda x: x["fitness_score"], reverse=True)
            top_strategy = ranked[0]
        else:
            ranked = sorted(results, key=lambda x: x["fitness_score"], reverse=True)
            top_strategy = ranked[0]
            
        baseline_result = next((r for r in results if r["action"] == RecoveryActionType.NO_ACTION.value), results[0])
        
        selection_reason = (
            f"Selected '{top_strategy['action']}' as optimal strategy with fitness score {top_strategy['fitness_score']}/100. "
            f"Projected Health: {top_strategy['projected_health_score']}% (vs {baseline_result['projected_health_score']}% without intervention). "
            f"Action Risk: {top_strategy['action_risk']}, Mission Disruption: {top_strategy['mission_disruption']}."
        )
        
        return {
            "diagnosed_fault": diagnosed_fault,
            "horizon_seconds": self.simulation_horizon_seconds,
            "current_condition": initial_telemetry,
            "baseline_unintervened": baseline_result,
            "evaluated_strategies": results,
            "top_recommended_strategy": top_strategy["action"],
            "top_strategy_details": top_strategy,
            "selection_reason": selection_reason
        }

    def _check_secondary_faults(self, telem: Dict[str, Any]) -> List[str]:
        """
        Scans projected telemetry for new violations introduced by recovery.
        """
        violations = []
        for param, spec in TELEMETRY_SPECS.items():
            val = float(telem.get(param, 0.0))
            if val < spec["critical_min"]:
                violations.append(f"{param} dropped below critical {spec['critical_min']}{spec['unit']}")
            elif val > spec["critical_max"]:
                violations.append(f"{param} exceeded critical {spec['critical_max']}{spec['unit']}")
        return violations

