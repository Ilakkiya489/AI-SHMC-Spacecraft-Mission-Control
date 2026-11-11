"""
Action Risk Evaluator for AI-SHMC.
Evaluates proposed spacecraft recovery actions independently of the fault risk.
Assesses reversibility, critical subsystem cross-impact, mission disruption,
rollback availability, and What-If projected secondary hazards.
"""

from typing import Dict, Any, List, Optional
from app.config import RiskLevel, RECOVERY_ACTIONS_METADATA, RecoveryActionType


class ActionRiskEvaluator:
    @staticmethod
    def evaluate(
        action_name: str,
        what_if_strategy_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates independent recovery action risk profile.
        """
        meta = RECOVERY_ACTIONS_METADATA.get(action_name, {})
        base_risk = meta.get("action_risk", RiskLevel.MEDIUM.value)
        reversibility = meta.get("reversibility", "MEDIUM")
        disruption = meta.get("mission_disruption", "MEDIUM")
        pre_approved = meta.get("pre_approved", False)
        
        # Check secondary hazards from what-if simulations
        secondary_faults = []
        if what_if_strategy_result:
            secondary_faults = what_if_strategy_result.get("secondary_faults", [])
            
        # Determine dynamic action risk score (1-5 scale)
        risk_score_map = {
            RiskLevel.LOW.value: 1,
            RiskLevel.MEDIUM.value: 2,
            RiskLevel.HIGH.value: 4,
            RiskLevel.CRITICAL.value: 5
        }
        score = risk_score_map.get(base_risk, 2)
        
        # Escalate risk if secondary hazards projected or action is irreversible
        if secondary_faults:
            score = min(5, score + len(secondary_faults))
        if reversibility == "LOW" and score < 4:
            score = 4
            
        if score <= 1:
            risk_level = RiskLevel.LOW.value
        elif score <= 3:
            risk_level = RiskLevel.MEDIUM.value
        elif score <= 4:
            risk_level = RiskLevel.HIGH.value
        else:
            risk_level = RiskLevel.CRITICAL.value
            
        rollback_available = (reversibility in ["HIGH", "MEDIUM"])
        
        explanation = (
            f"Action Risk: {risk_level} (Score {score}/5). Reversibility: {reversibility}, "
            f"Mission Disruption: {disruption}, Rollback: {'Available' if rollback_available else 'None'}."
        )
        if secondary_faults:
            explanation += f" Warning: What-If identified {len(secondary_faults)} secondary hazards."
            
        return {
            "action_name": action_name,
            "action_risk_level": risk_level,
            "action_risk_score": score,
            "reversibility": reversibility,
            "mission_disruption": disruption,
            "rollback_available": rollback_available,
            "pre_approved": pre_approved,
            "secondary_hazards_count": len(secondary_faults),
            "explanation": explanation
        }

