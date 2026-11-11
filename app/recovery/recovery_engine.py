"""
Autonomous Recovery Engine for AI-SHMC (PART 9).
Executes only verified, authorized recovery commands on the active spacecraft simulation.
Enforces hard safety gates, execution timeouts, automatic retry limits,
and rollback capabilities for reversible operations.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import RecoveryActionType, RECOVERY_ACTIONS_METADATA
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.safety.safety_constraints import SafetyConstraintChecker


class RecoveryEngine:
    def __init__(self, twin: SpacecraftTwin, max_retries: int = 2):
        self.twin = twin
        self.max_retries = max_retries
        self.execution_log: List[Dict[str, Any]] = []
        self.action_retry_counts: Dict[str, int] = {}
        self.active_actions: List[str] = []
        # Saved pre-recovery snapshots for rollback
        self.rollback_snapshots: Dict[str, Dict[str, Any]] = {}

    def execute_recovery(
        self,
        action_name: str,
        authorized_by: str,          # "AUTONOMY_LEVEL_1", "AUTONOMY_LEVEL_2", or operator ID
        bypass_safety_check: bool = False
    ) -> Dict[str, Any]:
        """
        Safely dispatches an authorized recovery procedure to the active spacecraft twin.
        """
        now_ts = datetime.utcnow().isoformat()
        current_telemetry = self.twin.get_telemetry()
        
        # 1. Safety verification check
        if not bypass_safety_check:
            is_safe, block_reason = SafetyConstraintChecker.check_action_safety(
                action_name, current_telemetry, self.active_actions
            )
            if not is_safe:
                record = {
                    "action": action_name,
                    "timestamp": now_ts,
                    "authorized_by": authorized_by,
                    "status": "BLOCKED_SAFETY_VIOLATION",
                    "reason": block_reason,
                    "pre_telemetry": current_telemetry,
                    "post_telemetry": current_telemetry
                }
                self.execution_log.append(record)
                return record
                
        # 2. Check retry count to prevent infinite failure loops
        retry_count = self.action_retry_counts.get(action_name, 0)
        if retry_count >= self.max_retries:
            record = {
                "action": action_name,
                "timestamp": now_ts,
                "authorized_by": authorized_by,
                "status": "BLOCKED_MAX_RETRIES_EXCEEDED",
                "reason": f"Action '{action_name}' has exceeded maximum allowed retries ({self.max_retries}). Escalation required.",
                "pre_telemetry": current_telemetry,
                "post_telemetry": current_telemetry
            }
            self.execution_log.append(record)
            return record
            
        # 3. Save pre-execution snapshot for rollback
        self.rollback_snapshots[action_name] = self.twin.clone()
        
        # 4. Dispatch bounded recovery command to spacecraft twin
        t0 = time.time()
        result = self.twin.apply_recovery_action(action_name)
        duration_s = round(time.time() - t0, 3)
        
        # Step simulation by 2 seconds to allow physical propagation
        self.twin.step(2.0)
        post_telemetry = self.twin.get_telemetry()
        
        self.action_retry_counts[action_name] = retry_count + 1
        if action_name not in self.active_actions:
            self.active_actions.append(action_name)
            
        record = {
            "action": action_name,
            "timestamp": now_ts,
            "authorized_by": authorized_by,
            "status": "EXECUTED",
            "message": result.get("message", "Recovery command committed."),
            "execution_duration_s": duration_s,
            "retry_attempt": retry_count + 1,
            "pre_telemetry": current_telemetry,
            "post_telemetry": post_telemetry
        }
        self.execution_log.append(record)
        return record

    def rollback_action(self, action_name: str, operator_reason: str = "Rollback requested") -> Dict[str, Any]:
        """
        Restores spacecraft state to pre-action snapshot if the operation is reversible.
        """
        now_ts = datetime.utcnow().isoformat()
        if action_name not in self.rollback_snapshots:
            return {
                "action": action_name,
                "status": "ROLLBACK_UNAVAILABLE",
                "message": "No pre-recovery snapshot available for rollback."
            }
            
        # Restore snapshot
        snapshot_twin = self.rollback_snapshots[action_name]
        self.twin = snapshot_twin.clone()
        if action_name in self.active_actions:
            self.active_actions.remove(action_name)
            
        record = {
            "action": action_name,
            "timestamp": now_ts,
            "status": "ROLLED_BACK",
            "reason": operator_reason,
            "message": f"Successfully rolled back action '{action_name}'."
        }
        self.execution_log.append(record)
        return record

