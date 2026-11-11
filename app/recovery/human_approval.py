"""
Human-in-the-Loop Operator Approval System for AI-SHMC (PART 8).
Manages pending authorization requests for Level 3 high-risk operations.
Guarantees rejected actions are blocked and pending requests never default to approved.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class OperatorDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SIMULATE_MORE = "REQUEST_ADDITIONAL_SIMULATION"


class HumanApprovalManager:
    def __init__(self):
        # In-memory storage for active requests (synced with database)
        self.requests: Dict[str, Dict[str, Any]] = {}
        self.decision_history: List[Dict[str, Any]] = []

    def create_approval_request(
        self,
        detected_fault: str,
        affected_subsystem: str,
        fault_severity: int,
        fault_risk_score: int,
        recovery_action_risk: str,
        ai_confidence_pct: float,
        predicted_consequences: str,
        available_recovery_strategies: List[Dict[str, Any]],
        recommended_recovery_action: str,
        reason_for_recommendation: str,
        spacecraft_id: str = "SAT-AI-SHMC-01"
    ) -> Dict[str, Any]:
        """
        Creates a structured approval request for flight operators.
        """
        req_id = str(uuid.uuid4())[:8].upper()
        now_ts = datetime.utcnow().isoformat()
        
        request_obj = {
            "request_id": req_id,
            "created_at": now_ts,
            "spacecraft_id": spacecraft_id,
            "status": OperatorDecision.PENDING.value,
            "detected_fault": detected_fault,
            "affected_subsystem": affected_subsystem,
            "fault_severity": fault_severity,
            "fault_risk_score": fault_risk_score,
            "recovery_action_risk": recovery_action_risk,
            "ai_confidence_pct": round(ai_confidence_pct, 1),
            "predicted_consequences": predicted_consequences,
            "available_recovery_strategies": available_recovery_strategies,
            "recommended_recovery_action": recommended_recovery_action,
            "reason_for_recommendation": reason_for_recommendation,
            "operator_id": None,
            "operator_notes": None,
            "decided_at": None,
            "execution_status": "WAITING_FOR_DECISION"
        }
        
        self.requests[req_id] = request_obj
        return request_obj

    def submit_decision(
        self,
        request_id: str,
        decision: OperatorDecision,
        operator_id: str = "FLIGHT_DIR_01",
        operator_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Records the explicit operator decision.
        Enforces that rejected actions are marked blocked.
        """
        if request_id not in self.requests:
            raise KeyError(f"Approval request '{request_id}' not found.")
            
        req = self.requests[request_id]
        if req["status"] != OperatorDecision.PENDING.value:
            raise ValueError(f"Request '{request_id}' has already been decided ({req['status']}).")
            
        now_ts = datetime.utcnow().isoformat()
        req["status"] = decision.value
        req["operator_id"] = operator_id
        req["operator_notes"] = operator_notes
        req["decided_at"] = now_ts
        
        if decision == OperatorDecision.APPROVED:
            req["execution_status"] = "AUTHORIZED_FOR_EXECUTION"
        elif decision == OperatorDecision.REJECTED:
            req["execution_status"] = "BLOCKED_BY_OPERATOR"
        elif decision == OperatorDecision.SIMULATE_MORE:
            req["execution_status"] = "RE_SIMULATION_REQUESTED"
            
        self.decision_history.append(dict(req))
        return req

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        return [r for r in self.requests.values() if r["status"] == OperatorDecision.PENDING.value]

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self.requests.get(request_id)

