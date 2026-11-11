"""
Hard Spacecraft Safety Constraints for AI-SHMC.
Enforces non-negotiable physical and operational boundaries.
Deterministic rules that no AI recommendation can override.
"""

from typing import Dict, Any, List, Tuple
from app.config import TELEMETRY_SPECS, RecoveryActionType


# Hard Inviolable Spacecraft Limits
HARD_SAFETY_CONSTRAINTS = {
    "min_battery_voltage": 20.0,      # V
    "max_battery_voltage": 34.0,      # V
    "max_battery_temp": 52.0,         # °C
    "min_battery_charge": 20.0,       # %
    "max_cpu_temp": 88.0,             # °C
    "max_packet_loss": 85.0           # %
}

# Subsystem Action Incompatibility Matrix (Mutual Exclusion)
# Actions that cannot be executed concurrently
MUTUALLY_EXCLUSIVE_ACTIONS = [
    (RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value, RecoveryActionType.REBOOT_PAYLOAD_INSTRUMENT.value),
    (RecoveryActionType.ENTER_SAFE_HOLD.value, RecoveryActionType.REINITIALIZE_COMM_SESSION.value)
]


class SafetyConstraintChecker:
    @staticmethod
    def check_telemetry_bounds(telemetry: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates telemetry against hard physical bounds.
        Returns (passed, list_of_violations).
        """
        violations = []
        
        v = float(telemetry.get("battery_voltage", 28.0))
        if v < HARD_SAFETY_CONSTRAINTS["min_battery_voltage"]:
            violations.append(f"CRITICAL: Battery voltage {v}V below hard limit {HARD_SAFETY_CONSTRAINTS['min_battery_voltage']}V")
        elif v > HARD_SAFETY_CONSTRAINTS["max_battery_voltage"]:
            violations.append(f"CRITICAL: Battery voltage {v}V above hard limit {HARD_SAFETY_CONSTRAINTS['max_battery_voltage']}V")
            
        bt = float(telemetry.get("battery_temperature", 25.0))
        if bt > HARD_SAFETY_CONSTRAINTS["max_battery_temp"]:
            violations.append(f"CRITICAL: Battery temperature {bt}°C exceeds survival limit {HARD_SAFETY_CONSTRAINTS['max_battery_temp']}°C")
            
        bc = float(telemetry.get("battery_charge", 90.0))
        if bc < HARD_SAFETY_CONSTRAINTS["min_battery_charge"]:
            violations.append(f"CRITICAL: Battery state of charge {bc}% below safe threshold {HARD_SAFETY_CONSTRAINTS['min_battery_charge']}%")
            
        ct = float(telemetry.get("cpu_temperature", 45.0))
        if ct > HARD_SAFETY_CONSTRAINTS["max_cpu_temp"]:
            violations.append(f"CRITICAL: CPU temperature {ct}°C exceeds semiconductor rating {HARD_SAFETY_CONSTRAINTS['max_cpu_temp']}°C")
            
        return (len(violations) == 0, violations)

    @staticmethod
    def check_action_safety(
        action: str,
        current_telemetry: Dict[str, Any],
        active_actions: List[str]
    ) -> Tuple[bool, str]:
        """
        Determines whether executing this action is safe in the current state.
        Checks mutual exclusivity and situational prerequisites.
        """
        # Mutual exclusion
        for act1, act2 in MUTUALLY_EXCLUSIVE_ACTIONS:
            if (action == act1 and act2 in active_actions) or (action == act2 and act1 in active_actions):
                return False, f"Action '{action}' is mutually exclusive with active action '{act1 if action == act2 else act2}'"
                
        # Critical battery condition prohibits high-draw actions
        battery_charge = float(current_telemetry.get("battery_charge", 100.0))
        if battery_charge < 25.0 and action in [
            RecoveryActionType.REBOOT_PAYLOAD_INSTRUMENT.value,
            RecoveryActionType.SWITCH_POWER_BUS_BACKUP.value
        ]:
            return False, f"Action '{action}' blocked: Insufficient battery energy ({battery_charge}%)"
            
        return True, "Safety constraints passed"

