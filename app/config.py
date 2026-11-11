"""
AI-SHMC: Spacecraft Configuration and Parameter Constants
Defines nominal ranges, safety thresholds, FMEA risk tables, and recovery action specifications.
"""

import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_deps_path = os.path.join(_project_root, ".deps")
if sys.version_info[:2] == (3, 8):
    if os.path.exists(_deps_path) and _deps_path not in sys.path:
        sys.path.insert(0, _deps_path)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from typing import Dict, Any, List
from enum import Enum
from pydantic import BaseModel


class SubsystemName(str, Enum):
    POWER = "Power"
    THERMAL = "Thermal"
    COMMUNICATION = "Communication"
    PROCESSING = "Processing"
    STORAGE = "Storage"
    PAYLOAD = "Payload"


class FaultCategory(str, Enum):
    NOMINAL = "Nominal"
    BATTERY_OVERHEATING = "Battery Overheating"
    BATTERY_VOLTAGE_DROP = "Battery Voltage Drop"
    SOLAR_PANEL_DEGRADATION = "Solar Panel Degradation"
    COMMUNICATION_SIGNAL_LOSS = "Communication Signal Loss"
    COMMUNICATION_PACKET_LOSS = "Communication Packet Loss"
    CPU_OVERLOAD = "CPU Overload"
    MEMORY_EXHAUSTION = "Memory Exhaustion"
    STORAGE_OVERFLOW = "Storage Overflow"
    PAYLOAD_MALFUNCTION = "Payload Malfunction"
    THERMAL_CONTROL_ANOMALY = "Thermal Control Anomaly"
    MULTIPLE_FAULTS = "Multiple Subsystem Faults"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AutonomyLevel(str, Enum):
    LEVEL_1_AUTONOMOUS = "LEVEL 1: AUTONOMOUS RECOVERY"
    LEVEL_2_CONDITIONAL = "LEVEL 2: CONDITIONAL AUTONOMY"
    LEVEL_3_HUMAN_APPROVAL = "LEVEL 3: HUMAN APPROVAL REQUIRED"
    LEVEL_4_SAFE_STATE = "LEVEL 4: SAFE-STATE ESCALATION"


class RecoveryActionType(str, Enum):
    # Comm actions
    RETRY_COMM_TRANSMISSION = "RETRY_COMM_TRANSMISSION"
    REINITIALIZE_COMM_SESSION = "REINITIALIZE_COMM_SESSION"
    SWITCH_ANTENNA_BEAM = "SWITCH_ANTENNA_BEAM"
    
    # Processing actions
    THROTTLE_CPU_WORKLOAD = "THROTTLE_CPU_WORKLOAD"
    RESTART_NON_CRITICAL_PROCESS = "RESTART_NON_CRITICAL_PROCESS"
    PURGE_MEMORY_CACHE = "PURGE_MEMORY_CACHE"
    
    # Power actions
    SHED_NON_ESSENTIAL_POWER = "SHED_NON_ESSENTIAL_POWER"
    SWITCH_POWER_BUS_BACKUP = "SWITCH_POWER_BUS_BACKUP"
    REORIENT_SOLAR_PANELS = "REORIENT_SOLAR_PANELS"
    
    # Thermal actions
    ACTIVATE_AUX_COOLING = "ACTIVATE_AUX_COOLING"
    REDUCE_THERMAL_LOAD = "REDUCE_THERMAL_LOAD"
    ADJUST_RADIATOR_LOUVERS = "ADJUST_RADIATOR_LOUVERS"
    
    # Storage actions
    PURGE_TELEMETRY_CACHE = "PURGE_TELEMETRY_CACHE"
    SUSPEND_HIGH_RATE_LOGGING = "SUSPEND_HIGH_RATE_LOGGING"
    TRIGGER_STORAGE_DEFRAG = "TRIGGER_STORAGE_DEFRAG"
    
    # Payload actions
    REDUCE_PAYLOAD_ACTIVITY = "REDUCE_PAYLOAD_ACTIVITY"
    PAUSE_PAYLOAD_DATA_COLLECTION = "PAUSE_PAYLOAD_DATA_COLLECTION"
    REBOOT_PAYLOAD_INSTRUMENT = "REBOOT_PAYLOAD_INSTRUMENT"
    
    # System protective actions
    ENTER_SAFE_HOLD = "ENTER_SAFE_HOLD"
    NO_ACTION = "NO_ACTION"


# Telemetry Nominal Ranges and Hard Critical Bounds
TELEMETRY_SPECS: Dict[str, Dict[str, float]] = {
    "battery_voltage": {
        "nominal_min": 26.0,
        "nominal_max": 32.0,
        "critical_min": 22.0,
        "critical_max": 34.5,
        "unit": "V"
    },
    "battery_temperature": {
        "nominal_min": 10.0,
        "nominal_max": 35.0,
        "critical_min": -5.0,
        "critical_max": 50.0,
        "unit": "°C"
    },
    "battery_charge": {
        "nominal_min": 60.0,
        "nominal_max": 100.0,
        "critical_min": 25.0,
        "critical_max": 100.0,
        "unit": "%"
    },
    "solar_current": {
        "nominal_min": 4.0,
        "nominal_max": 12.0,
        "critical_min": 1.0,
        "critical_max": 15.0,
        "unit": "A"
    },
    "power_consumption": {
        "nominal_min": 120.0,
        "nominal_max": 350.0,
        "critical_min": 80.0,
        "critical_max": 550.0,
        "unit": "W"
    },
    "cpu_temperature": {
        "nominal_min": 35.0,
        "nominal_max": 65.0,
        "critical_min": 20.0,
        "critical_max": 85.0,
        "unit": "°C"
    },
    "cpu_usage": {
        "nominal_min": 15.0,
        "nominal_max": 65.0,
        "critical_min": 5.0,
        "critical_max": 95.0,
        "unit": "%"
    },
    "memory_usage": {
        "nominal_min": 25.0,
        "nominal_max": 70.0,
        "critical_min": 10.0,
        "critical_max": 92.0,
        "unit": "%"
    },
    "signal_strength": {
        "nominal_min": -95.0,
        "nominal_max": -65.0,
        "critical_min": -120.0,
        "critical_max": -50.0,
        "unit": "dBm"
    },
    "packet_loss": {
        "nominal_min": 0.0,
        "nominal_max": 2.5,
        "critical_min": 0.0,
        "critical_max": 20.0,
        "unit": "%"
    },
    "communication_latency": {
        "nominal_min": 120.0,
        "nominal_max": 380.0,
        "critical_min": 80.0,
        "critical_max": 1200.0,
        "unit": "ms"
    },
    "storage_usage": {
        "nominal_min": 30.0,
        "nominal_max": 75.0,
        "critical_min": 10.0,
        "critical_max": 95.0,
        "unit": "%"
    },
    "payload_activity": {
        "nominal_min": 20.0,
        "nominal_max": 80.0,
        "critical_min": 0.0,
        "critical_max": 100.0,
        "unit": "%"
    }
}


# Predefined Recovery Action Profiles (Safety & Risk Attributes)
RECOVERY_ACTIONS_METADATA: Dict[str, Dict[str, Any]] = {
    RecoveryActionType.RETRY_COMM_TRANSMISSION.value: {
        "target_subsystem": SubsystemName.COMMUNICATION.value,
        "action_risk": RiskLevel.LOW.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": True,
        "description": "Retransmit unacknowledged telemetry packets and refresh TCP/UDP link frames.",
        "expected_duration_s": 5
    },
    RecoveryActionType.REINITIALIZE_COMM_SESSION.value: {
        "target_subsystem": SubsystemName.COMMUNICATION.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "HIGH",
        "mission_disruption": "MEDIUM",
        "pre_approved": False,
        "description": "Restart transponder baseband software and reacquire carrier signal.",
        "expected_duration_s": 15
    },
    RecoveryActionType.SWITCH_ANTENNA_BEAM.value: {
        "target_subsystem": SubsystemName.COMMUNICATION.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": False,
        "description": "Switch phased array transmitter beam direction to secondary ground station track.",
        "expected_duration_s": 10
    },
    RecoveryActionType.THROTTLE_CPU_WORKLOAD.value: {
        "target_subsystem": SubsystemName.PROCESSING.value,
        "action_risk": RiskLevel.LOW.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": True,
        "description": "Throttle non-critical telemetry compression background worker threads by 50%.",
        "expected_duration_s": 3
    },
    RecoveryActionType.PURGE_MEMORY_CACHE.value: {
        "target_subsystem": SubsystemName.PROCESSING.value,
        "action_risk": RiskLevel.LOW.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": True,
        "description": "Drop clean file caches, reclaim zombie buffers, and run garbage collection.",
        "expected_duration_s": 2
    },
    RecoveryActionType.RESTART_NON_CRITICAL_PROCESS.value: {
        "target_subsystem": SubsystemName.PROCESSING.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "MEDIUM",
        "mission_disruption": "MEDIUM",
        "pre_approved": False,
        "description": "Gracefully restart payload data preprocessing pipeline service.",
        "expected_duration_s": 12
    },
    RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value: {
        "target_subsystem": SubsystemName.POWER.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "HIGH",
        "mission_disruption": "MEDIUM",
        "pre_approved": False,
        "description": "De-energize secondary science sensors and non-essential payload heaters.",
        "expected_duration_s": 5
    },
    RecoveryActionType.SWITCH_POWER_BUS_BACKUP.value: {
        "target_subsystem": SubsystemName.POWER.value,
        "action_risk": RiskLevel.HIGH.value,
        "reversibility": "LOW",
        "mission_disruption": "HIGH",
        "pre_approved": False,
        "description": "Transfer DC power bus distribution from primary rail to backup cross-tie switch.",
        "expected_duration_s": 20
    },
    RecoveryActionType.REORIENT_SOLAR_PANELS.value: {
        "target_subsystem": SubsystemName.POWER.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": False,
        "description": "Drive solar array drive assembly (SADA) gimbal +15 deg toward optimum sun vector.",
        "expected_duration_s": 25
    },
    RecoveryActionType.ACTIVATE_AUX_COOLING.value: {
        "target_subsystem": SubsystemName.THERMAL.value,
        "action_risk": RiskLevel.LOW.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": True,
        "description": "Engage secondary thermoelectric cooler (TEC) loop for high-heat components.",
        "expected_duration_s": 8
    },
    RecoveryActionType.REDUCE_THERMAL_LOAD.value: {
        "target_subsystem": SubsystemName.THERMAL.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "HIGH",
        "mission_disruption": "MEDIUM",
        "pre_approved": False,
        "description": "Scale down computation clock rate and turn off auxiliary instrument illumination.",
        "expected_duration_s": 10
    },
    RecoveryActionType.ADJUST_RADIATOR_LOUVERS.value: {
        "target_subsystem": SubsystemName.THERMAL.value,
        "action_risk": RiskLevel.LOW.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": True,
        "description": "Open thermal radiator louvers by 30 degrees to maximize radiative heat ejection.",
        "expected_duration_s": 15
    },
    RecoveryActionType.PURGE_TELEMETRY_CACHE.value: {
        "target_subsystem": SubsystemName.STORAGE.value,
        "action_risk": RiskLevel.LOW.value,
        "reversibility": "MEDIUM",
        "mission_disruption": "LOW",
        "pre_approved": True,
        "description": "Flush already-downlinked mission telemetry circular buffers from onboard SSD.",
        "expected_duration_s": 5
    },
    RecoveryActionType.SUSPEND_HIGH_RATE_LOGGING.value: {
        "target_subsystem": SubsystemName.STORAGE.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "HIGH",
        "mission_disruption": "MEDIUM",
        "pre_approved": False,
        "description": "Downgrade payload raw dump logging to compressed summary records only.",
        "expected_duration_s": 4
    },
    RecoveryActionType.TRIGGER_STORAGE_DEFRAG.value: {
        "target_subsystem": SubsystemName.STORAGE.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "MEDIUM",
        "mission_disruption": "MEDIUM",
        "pre_approved": False,
        "description": "Run NAND flash wear-leveling and block garbage collection.",
        "expected_duration_s": 15
    },
    RecoveryActionType.REDUCE_PAYLOAD_ACTIVITY.value: {
        "target_subsystem": SubsystemName.PAYLOAD.value,
        "action_risk": RiskLevel.MEDIUM.value,
        "reversibility": "HIGH",
        "mission_disruption": "HIGH",
        "pre_approved": False,
        "description": "Step down science optical imaging spectrometer duty cycle from 100% to 30%.",
        "expected_duration_s": 6
    },
    RecoveryActionType.PAUSE_PAYLOAD_DATA_COLLECTION.value: {
        "target_subsystem": SubsystemName.PAYLOAD.value,
        "action_risk": RiskLevel.HIGH.value,
        "reversibility": "HIGH",
        "mission_disruption": "HIGH",
        "pre_approved": False,
        "description": "Temporarily enter payload standby mode; halt survey observation cycle.",
        "expected_duration_s": 8
    },
    RecoveryActionType.REBOOT_PAYLOAD_INSTRUMENT.value: {
        "target_subsystem": SubsystemName.PAYLOAD.value,
        "action_risk": RiskLevel.HIGH.value,
        "reversibility": "LOW",
        "mission_disruption": "HIGH",
        "pre_approved": False,
        "description": "Full power cycle of science payload sensor instrument payload FPGA.",
        "expected_duration_s": 30
    },
    RecoveryActionType.ENTER_SAFE_HOLD.value: {
        "target_subsystem": "Spacecraft",
        "action_risk": RiskLevel.CRITICAL.value,
        "reversibility": "LOW",
        "mission_disruption": "CRITICAL",
        "pre_approved": False,
        "description": "Spacecraft-wide emergency hold: shed all non-essential loads, point sun-safe, preserve battery.",
        "expected_duration_s": 60
    },
    RecoveryActionType.NO_ACTION.value: {
        "target_subsystem": "None",
        "action_risk": RiskLevel.LOW.value,
        "reversibility": "HIGH",
        "mission_disruption": "LOW",
        "pre_approved": True,
        "description": "Take no active recovery; maintain current operational configuration and continue monitoring.",
        "expected_duration_s": 0
    }
}


# Mapping of Fault Categories to candidate recovery strategies for Digital Twin evaluation
FAULT_RECOVERY_CANDIDATES: Dict[str, List[str]] = {
    FaultCategory.BATTERY_OVERHEATING.value: [
        RecoveryActionType.REDUCE_PAYLOAD_ACTIVITY.value,
        RecoveryActionType.THROTTLE_CPU_WORKLOAD.value,
        RecoveryActionType.ACTIVATE_AUX_COOLING.value,
        RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value,
        RecoveryActionType.ENTER_SAFE_HOLD.value
    ],
    FaultCategory.BATTERY_VOLTAGE_DROP.value: [
        RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value,
        RecoveryActionType.REDUCE_PAYLOAD_ACTIVITY.value,
        RecoveryActionType.REORIENT_SOLAR_PANELS.value,
        RecoveryActionType.ENTER_SAFE_HOLD.value
    ],
    FaultCategory.SOLAR_PANEL_DEGRADATION.value: [
        RecoveryActionType.REORIENT_SOLAR_PANELS.value,
        RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value,
        RecoveryActionType.REDUCE_PAYLOAD_ACTIVITY.value,
        RecoveryActionType.ENTER_SAFE_HOLD.value
    ],
    FaultCategory.COMMUNICATION_PACKET_LOSS.value: [
        RecoveryActionType.RETRY_COMM_TRANSMISSION.value,
        RecoveryActionType.SWITCH_ANTENNA_BEAM.value,
        RecoveryActionType.REINITIALIZE_COMM_SESSION.value
    ],
    FaultCategory.COMMUNICATION_SIGNAL_LOSS.value: [
        RecoveryActionType.SWITCH_ANTENNA_BEAM.value,
        RecoveryActionType.REINITIALIZE_COMM_SESSION.value,
        RecoveryActionType.ENTER_SAFE_HOLD.value
    ],
    FaultCategory.CPU_OVERLOAD.value: [
        RecoveryActionType.THROTTLE_CPU_WORKLOAD.value,
        RecoveryActionType.PURGE_MEMORY_CACHE.value,
        RecoveryActionType.RESTART_NON_CRITICAL_PROCESS.value
    ],
    FaultCategory.MEMORY_EXHAUSTION.value: [
        RecoveryActionType.PURGE_MEMORY_CACHE.value,
        RecoveryActionType.RESTART_NON_CRITICAL_PROCESS.value,
        RecoveryActionType.THROTTLE_CPU_WORKLOAD.value
    ],
    FaultCategory.STORAGE_OVERFLOW.value: [
        RecoveryActionType.PURGE_TELEMETRY_CACHE.value,
        RecoveryActionType.SUSPEND_HIGH_RATE_LOGGING.value,
        RecoveryActionType.TRIGGER_STORAGE_DEFRAG.value
    ],
    FaultCategory.PAYLOAD_MALFUNCTION.value: [
        RecoveryActionType.REDUCE_PAYLOAD_ACTIVITY.value,
        RecoveryActionType.REBOOT_PAYLOAD_INSTRUMENT.value,
        RecoveryActionType.PAUSE_PAYLOAD_DATA_COLLECTION.value
    ],
    FaultCategory.THERMAL_CONTROL_ANOMALY.value: [
        RecoveryActionType.ACTIVATE_AUX_COOLING.value,
        RecoveryActionType.ADJUST_RADIATOR_LOUVERS.value,
        RecoveryActionType.REDUCE_THERMAL_LOAD.value
    ],
    FaultCategory.MULTIPLE_FAULTS.value: [
        RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value,
        RecoveryActionType.REDUCE_PAYLOAD_ACTIVITY.value,
        RecoveryActionType.ENTER_SAFE_HOLD.value
    ]
}


# FMEA Severity and Likelihood Baseline Table
FMEA_FAULT_PROFILES: Dict[str, Dict[str, int]] = {
    FaultCategory.NOMINAL.value: {"severity": 1, "likelihood": 1},
    FaultCategory.COMMUNICATION_PACKET_LOSS.value: {"severity": 2, "likelihood": 2},  # Score 4 -> LOW
    FaultCategory.STORAGE_OVERFLOW.value: {"severity": 3, "likelihood": 2},          # Score 6 -> MEDIUM
    FaultCategory.CPU_OVERLOAD.value: {"severity": 3, "likelihood": 3},              # Score 9 -> MEDIUM
    FaultCategory.MEMORY_EXHAUSTION.value: {"severity": 3, "likelihood": 3},         # Score 9 -> MEDIUM
    FaultCategory.SOLAR_PANEL_DEGRADATION.value: {"severity": 3, "likelihood": 3},   # Score 9 -> MEDIUM
    FaultCategory.THERMAL_CONTROL_ANOMALY.value: {"severity": 4, "likelihood": 3},   # Score 12 -> HIGH
    FaultCategory.BATTERY_OVERHEATING.value: {"severity": 4, "likelihood": 4},       # Score 16 -> HIGH
    FaultCategory.BATTERY_VOLTAGE_DROP.value: {"severity": 4, "likelihood": 3},      # Score 12 -> HIGH
    FaultCategory.PAYLOAD_MALFUNCTION.value: {"severity": 3, "likelihood": 4},       # Score 12 -> HIGH
    FaultCategory.COMMUNICATION_SIGNAL_LOSS.value: {"severity": 4, "likelihood": 4}, # Score 16 -> HIGH
    FaultCategory.MULTIPLE_FAULTS.value: {"severity": 5, "likelihood": 4}           # Score 20 -> CRITICAL
}

# Database and Paths
DATABASE_URL = "sqlite:///./data/ai_shmc.db"
RANDOM_SEED = 42
DEFAULT_PREDICTION_HORIZONS = [1, 3, 5, 10]  # simulation minutes
