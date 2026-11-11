"""
Risk Assessment Engine for AI-SHMC (PART 6).
Evaluates two independent risks:
A. Fault Risk (FMEA-inspired: Severity S 1-5, Likelihood P 1-5 -> Score S x P).
B. Recovery Action Risk (Reversibility, Disruption, Cross-impact, Rollback).
C. AI Diagnostic Confidence (High >= 90%, Moderate 75-89%, Low < 75%).
"""

from typing import Dict, Any, Optional
from app.config import RiskLevel, FMEA_FAULT_PROFILES, FaultCategory
from app.safety.action_risk_evaluator import ActionRiskEvaluator


class RiskAssessmentEngine:
    @staticmethod
    def calculate_fault_risk(
        fault_name: str,
        observed_severity_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculates Fault Risk based on FMEA Failure Mode and Effects Analysis.
        Severity (S): 1-5, Likelihood (P): 1-5.
        Risk Score = S x P (1 to 25).
        """
        fmea = FMEA_FAULT_PROFILES.get(fault_name, {"severity": 2, "likelihood": 2})
        severity = observed_severity_override or fmea["severity"]
        likelihood = fmea["likelihood"]
        
        severity = max(1, min(5, int(severity)))
        likelihood = max(1, min(5, int(likelihood)))
        risk_score = severity * likelihood
        
        # Risk Classification according to Part 6.1:
        # 1-4 = LOW
        # 5-9 = MEDIUM
        # 10-16 = HIGH
        # 17-25 = CRITICAL
        if risk_score <= 4:
            risk_level = RiskLevel.LOW.value
        elif risk_score <= 9:
            risk_level = RiskLevel.MEDIUM.value
        elif risk_score <= 16:
            risk_level = RiskLevel.HIGH.value
        else:
            risk_level = RiskLevel.CRITICAL.value
            
        severity_labels = {
            1: "Negligible",
            2: "Minor",
            3: "Moderate",
            4: "Major",
            5: "Catastrophic"
        }
        likelihood_labels = {
            1: "Rare",
            2: "Unlikely",
            3: "Possible",
            4: "Likely",
            5: "Almost Certain"
        }
        
        explanation = (
            f"FMEA Fault Risk: {risk_level} (Score {risk_score}/25). "
            f"Severity: {severity}/5 ({severity_labels[severity]}), "
            f"Likelihood: {likelihood}/5 ({likelihood_labels[likelihood]})."
        )
        
        return {
            "fault_name": fault_name,
            "severity": severity,
            "severity_label": severity_labels[severity],
            "likelihood": likelihood,
            "likelihood_label": likelihood_labels[likelihood],
            "risk_score": risk_score,
            "risk_level": risk_level,
            "explanation": explanation
        }

    @staticmethod
    def evaluate_ai_confidence(confidence_pct: float) -> Dict[str, Any]:
        """
        Evaluates AI model diagnostic confidence independently of risk.
        90%-100% = High confidence.
        75%-89% = Moderate confidence.
        Below 75% = Low confidence.
        """
        conf = max(0.0, min(100.0, float(confidence_pct)))
        if conf >= 90.0:
            level = "HIGH"
            is_sufficient = True
        elif conf >= 75.0:
            level = "MODERATE"
            is_sufficient = True
        else:
            level = "LOW"
            is_sufficient = False
            
        return {
            "confidence_pct": round(conf, 1),
            "confidence_level": level,
            "is_sufficient_for_autonomy": is_sufficient,
            "explanation": (
                f"Diagnostic Confidence: {round(conf, 1)}% ({level}). "
                f"{'Meets autonomy threshold.' if is_sufficient else 'Below 75% threshold; requires human confirmation or safe-state escalation.'}"
            )
        }

    @classmethod
    def assess_comprehensive_risk(
        cls,
        fault_name: str,
        proposed_action: str,
        diagnosis_confidence_pct: float,
        what_if_strategy_result: Optional[Dict[str, Any]] = None,
        observed_severity: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Combines Fault Risk, Action Risk, and AI Confidence into an audited assessment report.
        """
        fault_risk = cls.calculate_fault_risk(fault_name, observed_severity)
        action_risk = ActionRiskEvaluator.evaluate(proposed_action, what_if_strategy_result)
        ai_conf = cls.evaluate_ai_confidence(diagnosis_confidence_pct)
        
        return {
            "fault_risk": fault_risk,
            "action_risk": action_risk,
            "ai_confidence": ai_conf,
            "combined_summary": (
                f"Fault: {fault_name} [Risk: {fault_risk['risk_level']}] | "
                f"Action: {proposed_action} [Risk: {action_risk['action_risk_level']}] | "
                f"AI Conf: {ai_conf['confidence_pct']}% [{ai_conf['confidence_level']}]"
            )
        }

