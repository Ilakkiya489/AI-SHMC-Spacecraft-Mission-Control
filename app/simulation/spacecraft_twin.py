"""
Spacecraft Digital Twin Core Engine.
Simulates stateful telemetry across Power, Thermal, Communication, Processing,
Storage, and Payload subsystems with dynamic inter-subsystem dependencies.
Supports deep cloning for sandbox what-if simulations.
"""

import copy
import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import (
    SubsystemName,
    FaultCategory,
    RecoveryActionType,
    TELEMETRY_SPECS
)
from app.simulation.subsystem_models import (
    PowerSubsystem,
    ThermalSubsystem,
    CommunicationSubsystem,
    ProcessingSubsystem,
    StorageSubsystem,
    PayloadSubsystem
)


class SpacecraftTwin:
    def __init__(self, spacecraft_id: str = "SAT-AI-SHMC-01"):
        self.spacecraft_id = spacecraft_id
        self.simulation_time = 0.0          # Elapsed simulation seconds
        self.real_start_time = datetime.utcnow()
        self.is_paused = False
        self.time_acceleration = 1.0        # 1x, 2x, 5x, 10x
        
        # Subsystems
        self.power = PowerSubsystem()
        self.thermal = ThermalSubsystem()
        self.comm = CommunicationSubsystem()
        self.processing = ProcessingSubsystem()
        self.storage = StorageSubsystem()
        self.payload = PayloadSubsystem()
        
        # Active fault tracking
        self.active_faults: Dict[str, Dict[str, Any]] = {}
        
        # Executed recovery history
        self.active_recovery_actions: Dict[str, float] = {}
        
        # Health indicators
        self.subsystem_health: Dict[str, str] = {
            SubsystemName.POWER.value: "NOMINAL",
            SubsystemName.THERMAL.value: "NOMINAL",
            SubsystemName.COMMUNICATION.value: "NOMINAL",
            SubsystemName.PROCESSING.value: "NOMINAL",
            SubsystemName.STORAGE.value: "NOMINAL",
            SubsystemName.PAYLOAD.value: "NOMINAL"
        }
        
    def clone(self) -> 'SpacecraftTwin':
        """
        Creates an independent deep-copy clone of the spacecraft twin.
        Crucial requirement: What-If simulation engine must never modify live spacecraft state!
        """
        return copy.deepcopy(self)

    def step(self, dt_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Advances the spacecraft state by dt_seconds, updating inter-subsystem physics.
        """
        if self.is_paused:
            return self.get_telemetry()
            
        dt = dt_seconds * self.time_acceleration
        self.simulation_time += dt
        
        # 1. Update payload
        self.payload.step(dt)
        
        # 2. Update processing (CPU depends on payload activity)
        self.processing.step(dt, self.payload.payload_activity)
        
        # 3. Update power (depends on payload power, CPU usage, and aux cooling)
        power_consumption = self.power.step(
            dt,
            self.payload.payload_power,
            self.processing.cpu_usage,
            self.thermal.aux_cooling_active
        )
        
        # 4. Update thermal (depends on power consumption, CPU load, and battery current)
        self.thermal.step(
            dt,
            power_consumption,
            self.processing.cpu_usage,
            self.power.battery_current
        )
        
        # 5. Update communication
        self.comm.step(dt)
        
        # 6. Update storage (depends on payload data rate and comm status)
        self.storage.step(dt, self.payload.data_collection_rate, self.comm.connection_status)
        
        # 7. Apply active fault dynamics
        self._apply_active_fault_effects(dt)
        
        # 8. Update subsystem health statuses based on critical bounds
        self._update_health_status()
        
        return self.get_telemetry()

    def _apply_active_fault_effects(self, dt: float):
        """
        Drives progressive degradation when simulated faults are active
        using realistic physical asymptotic target convergence.
        """
        if FaultCategory.BATTERY_OVERHEATING.value in self.active_faults:
            fault_meta = self.active_faults[FaultCategory.BATTERY_OVERHEATING.value]
            intensity = fault_meta.get("intensity", 1.0)
            target_t = 48.0 + 8.0 * (intensity - 1.0)
            self.thermal.battery_temperature += (target_t - self.thermal.battery_temperature) * 0.18 * dt
            self.power.battery_voltage = max(22.0, self.power.battery_voltage - 0.05 * intensity * dt)
            
        if FaultCategory.BATTERY_VOLTAGE_DROP.value in self.active_faults:
            fault_meta = self.active_faults[FaultCategory.BATTERY_VOLTAGE_DROP.value]
            intensity = fault_meta.get("intensity", 1.0)
            target_v = 21.0 / intensity
            self.power.battery_voltage += (target_v - self.power.battery_voltage) * 0.25 * dt
            self.power.battery_charge = max(15.0, self.power.battery_charge - 0.8 * intensity * dt)
            
        if FaultCategory.SOLAR_PANEL_DEGRADATION.value in self.active_faults:
            self.power.solar_efficiency = 0.25
            self.power.solar_current = 2.4
            self.power.solar_voltage = 20.0
            
        if FaultCategory.COMMUNICATION_PACKET_LOSS.value in self.active_faults:
            fault_meta = self.active_faults[FaultCategory.COMMUNICATION_PACKET_LOSS.value]
            intensity = fault_meta.get("intensity", 1.0)
            target_pl = 16.0 * intensity
            self.comm.packet_loss += (target_pl - self.comm.packet_loss) * 0.35 * dt
            self.comm.communication_latency += (520.0 - self.comm.communication_latency) * 0.2 * dt
            
        if FaultCategory.COMMUNICATION_SIGNAL_LOSS.value in self.active_faults:
            self.comm.signal_strength = -118.0
            self.comm.packet_loss = 92.0
            self.comm.connection_status = "LOST"
            
        if FaultCategory.CPU_OVERLOAD.value in self.active_faults:
            self.processing.cpu_usage += (98.5 - self.processing.cpu_usage) * 0.35 * dt
            self.thermal.cpu_temperature += (78.0 - self.thermal.cpu_temperature) * 0.2 * dt
            
        if FaultCategory.MEMORY_EXHAUSTION.value in self.active_faults:
            self.processing.process_leak_active = True
            self.processing.memory_usage += (96.0 - self.processing.memory_usage) * 0.25 * dt
            
        if FaultCategory.STORAGE_OVERFLOW.value in self.active_faults:
            self.storage.storage_usage += (98.0 - self.storage.storage_usage) * 0.25 * dt
            self.storage.storage_error_count += int(1 * dt)
            self.storage.data_integrity_status = "DEGRADED"
            
        if FaultCategory.PAYLOAD_MALFUNCTION.value in self.active_faults:
            self.payload.malfunction = True
            
        if FaultCategory.THERMAL_CONTROL_ANOMALY.value in self.active_faults:
            self.thermal.cooling_efficiency = 0.25
            self.thermal.radiator_louver_open = 0.05
            self.thermal.internal_temperature += (38.0 - self.thermal.internal_temperature) * 0.15 * dt
            self.thermal.cpu_temperature += (72.0 - self.thermal.cpu_temperature) * 0.15 * dt

    def inject_fault(self, fault_category: str, intensity: float = 1.0) -> bool:
        """
        Injects a designated fault into the simulation.
        """
        self.active_faults[fault_category] = {
            "category": fault_category,
            "intensity": intensity,
            "injected_at": self.simulation_time
        }
        return True

    def clear_fault(self, fault_category: str) -> bool:
        """
        Clears an active fault and restores nominal baseline behavior.
        """
        if fault_category in self.active_faults:
            del self.active_faults[fault_category]
            
        if fault_category == FaultCategory.PAYLOAD_MALFUNCTION.value:
            self.payload.malfunction = False
            self.payload.sensor_status = "OPERATIONAL"
            self.payload.payload_activity = 40.0
        elif fault_category == FaultCategory.MEMORY_EXHAUSTION.value:
            self.processing.process_leak_active = False
            self.processing.memory_usage = 42.0
        elif fault_category == FaultCategory.SOLAR_PANEL_DEGRADATION.value:
            self.power.solar_efficiency = 1.0
        elif fault_category == FaultCategory.THERMAL_CONTROL_ANOMALY.value:
            self.thermal.cooling_efficiency = 1.0
            self.thermal.radiator_louver_open = 0.5
        elif fault_category == FaultCategory.COMMUNICATION_SIGNAL_LOSS.value:
            self.comm.antenna_tracking_error = 0.0
            self.comm.rf_interference = 0.0
            self.comm.connection_status = "CONNECTED"
            
        return True

    def apply_recovery_action(self, action_type: str) -> Dict[str, Any]:
        """
        Executes an authorized recovery action on the simulated spacecraft.
        Modifies system state in accordance with aerospace recovery procedures.
        """
        success = False
        message = ""
        
        if action_type == RecoveryActionType.RETRY_COMM_TRANSMISSION.value:
            self.comm.packet_loss = max(0.2, self.comm.packet_loss * 0.15)
            self.comm.communication_latency = max(180.0, self.comm.communication_latency * 0.6)
            self.clear_fault(FaultCategory.COMMUNICATION_PACKET_LOSS.value)
            success = True
            message = "Unacknowledged packets retransmitted. Packet loss reduced to nominal."
            
        elif action_type == RecoveryActionType.REINITIALIZE_COMM_SESSION.value:
            self.comm.signal_strength = -84.0
            self.comm.packet_loss = 0.8
            self.comm.connection_status = "CONNECTED"
            self.clear_fault(FaultCategory.COMMUNICATION_SIGNAL_LOSS.value)
            self.clear_fault(FaultCategory.COMMUNICATION_PACKET_LOSS.value)
            success = True
            message = "Transponder baseband reinitialized. RF carrier lock re-established."
            
        elif action_type == RecoveryActionType.SWITCH_ANTENNA_BEAM.value:
            self.comm.antenna_tracking_error = 0.0
            self.comm.signal_strength = -78.0
            self.comm.packet_loss = 0.5
            self.comm.connection_status = "CONNECTED"
            self.clear_fault(FaultCategory.COMMUNICATION_SIGNAL_LOSS.value)
            success = True
            message = "Switched to secondary ground track antenna beam. Signal strength restored."
            
        elif action_type == RecoveryActionType.THROTTLE_CPU_WORKLOAD.value:
            self.processing.cpu_throttle_active = True
            self.processing.cpu_usage = max(25.0, self.processing.cpu_usage * 0.5)
            self.clear_fault(FaultCategory.CPU_OVERLOAD.value)
            success = True
            message = "Non-essential worker threads throttled by 50%. CPU load mitigated."
            
        elif action_type == RecoveryActionType.PURGE_MEMORY_CACHE.value:
            self.processing.process_leak_active = False
            self.processing.memory_usage = max(35.0, self.processing.memory_usage * 0.45)
            self.clear_fault(FaultCategory.MEMORY_EXHAUSTION.value)
            success = True
            message = "File buffers and memory caches purged. Memory utilization nominal."
            
        elif action_type == RecoveryActionType.RESTART_NON_CRITICAL_PROCESS.value:
            self.processing.process_leak_active = False
            self.processing.cpu_usage = 30.0
            self.processing.memory_usage = 38.0
            self.clear_fault(FaultCategory.CPU_OVERLOAD.value)
            self.clear_fault(FaultCategory.MEMORY_EXHAUSTION.value)
            success = True
            message = "Restarted processing pipeline daemon. Reclaimed thread resources."
            
        elif action_type == RecoveryActionType.ACTIVATE_AUX_COOLING.value:
            self.thermal.aux_cooling_active = True
            self.thermal.battery_temperature = max(22.0, self.thermal.battery_temperature - 12.0)
            self.thermal.cpu_temperature = max(40.0, self.thermal.cpu_temperature - 15.0)
            self.clear_fault(FaultCategory.BATTERY_OVERHEATING.value)
            self.clear_fault(FaultCategory.THERMAL_CONTROL_ANOMALY.value)
            success = True
            message = "Auxiliary TEC cooling loop engaged. Temperatures dropping."
            
        elif action_type == RecoveryActionType.ADJUST_RADIATOR_LOUVERS.value:
            self.thermal.radiator_louver_open = 1.0  # Fully open
            self.thermal.cooling_efficiency = 1.0
            self.clear_fault(FaultCategory.THERMAL_CONTROL_ANOMALY.value)
            success = True
            message = "Radiator louvers adjusted to maximum dissipation profile."
            
        elif action_type == RecoveryActionType.REDUCE_THERMAL_LOAD.value:
            self.processing.cpu_usage = min(35.0, self.processing.cpu_usage)
            self.payload.payload_activity = min(20.0, self.payload.payload_activity)
            self.thermal.battery_temperature = max(25.0, self.thermal.battery_temperature - 8.0)
            self.clear_fault(FaultCategory.BATTERY_OVERHEATING.value)
            success = True
            message = "Thermal shedding commands active. Lowered thermal dissipation load."
            
        elif action_type == RecoveryActionType.SHED_NON_ESSENTIAL_POWER.value:
            self.payload.payload_activity = 15.0
            self.processing.cpu_usage = min(30.0, self.processing.cpu_usage)
            self.power.battery_voltage = min(29.0, max(26.5, self.power.battery_voltage + 2.5))
            self.clear_fault(FaultCategory.BATTERY_VOLTAGE_DROP.value)
            success = True
            message = "Non-essential power loads shed. Bus voltage stabilized."
            
        elif action_type == RecoveryActionType.REORIENT_SOLAR_PANELS.value:
            self.power.solar_panel_offset_deg = 0.0
            self.power.solar_efficiency = 1.0
            self.power.solar_current = 9.8
            self.clear_fault(FaultCategory.SOLAR_PANEL_DEGRADATION.value)
            success = True
            message = "SADA drive reoriented panels towards optimal sun vector."
            
        elif action_type == RecoveryActionType.SWITCH_POWER_BUS_BACKUP.value:
            self.power.power_bus_backup = True
            self.power.battery_voltage = 28.2
            self.clear_fault(FaultCategory.BATTERY_VOLTAGE_DROP.value)
            success = True
            message = "Switched to secondary power bus distribution. Voltage nominal."
            
        elif action_type == RecoveryActionType.PURGE_TELEMETRY_CACHE.value:
            self.storage.storage_usage = max(35.0, self.storage.storage_usage - 40.0)
            self.storage.data_integrity_status = "VALID"
            self.clear_fault(FaultCategory.STORAGE_OVERFLOW.value)
            success = True
            message = "Downlinked science telemetry flushed from SSD buffer."
            
        elif action_type == RecoveryActionType.SUSPEND_HIGH_RATE_LOGGING.value:
            self.storage.high_rate_logging = False
            self.clear_fault(FaultCategory.STORAGE_OVERFLOW.value)
            success = True
            message = "High-rate debug logging suspended. Storage fill rate minimized."
            
        elif action_type == RecoveryActionType.TRIGGER_STORAGE_DEFRAG.value:
            self.storage.storage_usage = max(40.0, self.storage.storage_usage - 15.0)
            self.storage.storage_error_count = 0
            self.storage.data_integrity_status = "VALID"
            self.clear_fault(FaultCategory.STORAGE_OVERFLOW.value)
            success = True
            message = "NAND flash wear-leveling completed. Error count cleared."
            
        elif action_type == RecoveryActionType.REDUCE_PAYLOAD_ACTIVITY.value:
            self.payload.payload_activity = 25.0
            self.payload.payload_power = 45.0
            self.clear_fault(FaultCategory.PAYLOAD_MALFUNCTION.value)
            self.clear_fault(FaultCategory.BATTERY_OVERHEATING.value)
            success = True
            message = "Payload duty cycle decreased to 25%. Mitigated power and thermal demands."
            
        elif action_type == RecoveryActionType.PAUSE_PAYLOAD_DATA_COLLECTION.value:
            self.payload.payload_activity = 0.0
            self.payload.payload_power = 20.0
            self.clear_fault(FaultCategory.PAYLOAD_MALFUNCTION.value)
            success = True
            message = "Payload observations paused. Sensor entered quiescent standby."
            
        elif action_type == RecoveryActionType.REBOOT_PAYLOAD_INSTRUMENT.value:
            self.payload.malfunction = False
            self.payload.sensor_status = "OPERATIONAL"
            self.payload.payload_activity = 35.0
            self.payload.payload_power = 60.0
            self.clear_fault(FaultCategory.PAYLOAD_MALFUNCTION.value)
            success = True
            message = "Instrument FPGA power-cycled. Nominal calibration reloaded."
            
        elif action_type == RecoveryActionType.ENTER_SAFE_HOLD.value:
            # Spacecraft-wide emergency hold
            self.payload.payload_activity = 0.0
            self.payload.payload_power = 15.0
            self.processing.cpu_throttle_active = True
            self.processing.cpu_usage = 20.0
            self.thermal.aux_cooling_active = True
            self.thermal.radiator_louver_open = 1.0
            self.power.solar_panel_offset_deg = 0.0
            self.active_faults.clear()
            success = True
            message = "ENTERED SAFE-HOLD: Minimum survival configuration active. Sun-pointing locked."
            
        elif action_type == RecoveryActionType.NO_ACTION.value:
            success = True
            message = "No recovery action applied; spacecraft in baseline operational state."
            
        if success:
            self.active_recovery_actions[action_type] = self.simulation_time
            
        return {"action": action_type, "success": success, "message": message}

    def _update_health_status(self):
        """
        Evaluates subsystem health based on current telemetry metrics.
        """
        # Power
        v = self.power.battery_voltage
        c = self.power.battery_charge
        if v < 23.0 or c < 30.0:
            self.subsystem_health[SubsystemName.POWER.value] = "CRITICAL"
        elif v < 26.0 or c < 60.0:
            self.subsystem_health[SubsystemName.POWER.value] = "DEGRADED"
        else:
            self.subsystem_health[SubsystemName.POWER.value] = "NOMINAL"
            
        # Thermal
        bt = self.thermal.battery_temperature
        ct = self.thermal.cpu_temperature
        if bt > 48.0 or ct > 82.0:
            self.subsystem_health[SubsystemName.THERMAL.value] = "CRITICAL"
        elif bt > 36.0 or ct > 68.0:
            self.subsystem_health[SubsystemName.THERMAL.value] = "DEGRADED"
        else:
            self.subsystem_health[SubsystemName.THERMAL.value] = "NOMINAL"
            
        # Communication
        pl = self.comm.packet_loss
        sig = self.comm.signal_strength
        if pl > 50.0 or sig < -115.0:
            self.subsystem_health[SubsystemName.COMMUNICATION.value] = "CRITICAL"
        elif pl > 3.0 or sig < -95.0:
            self.subsystem_health[SubsystemName.COMMUNICATION.value] = "DEGRADED"
        else:
            self.subsystem_health[SubsystemName.COMMUNICATION.value] = "NOMINAL"
            
        # Processing
        cpu = self.processing.cpu_usage
        mem = self.processing.memory_usage
        if cpu > 92.0 or mem > 92.0:
            self.subsystem_health[SubsystemName.PROCESSING.value] = "CRITICAL"
        elif cpu > 70.0 or mem > 75.0:
            self.subsystem_health[SubsystemName.PROCESSING.value] = "DEGRADED"
        else:
            self.subsystem_health[SubsystemName.PROCESSING.value] = "NOMINAL"
            
        # Storage
        st = self.storage.storage_usage
        if st > 92.0:
            self.subsystem_health[SubsystemName.STORAGE.value] = "CRITICAL"
        elif st > 75.0:
            self.subsystem_health[SubsystemName.STORAGE.value] = "DEGRADED"
        else:
            self.subsystem_health[SubsystemName.STORAGE.value] = "NOMINAL"
            
        # Payload
        if self.payload.sensor_status == "ERROR":
            self.subsystem_health[SubsystemName.PAYLOAD.value] = "CRITICAL"
        elif self.payload.payload_activity > 85.0:
            self.subsystem_health[SubsystemName.PAYLOAD.value] = "DEGRADED"
        else:
            self.subsystem_health[SubsystemName.PAYLOAD.value] = "NOMINAL"

    def get_overall_health_score(self) -> float:
        """
        Calculates spacecraft aggregate health score from 0.0 (catastrophic) to 100.0 (optimal).
        """
        penalties = 0.0
        for status in self.subsystem_health.values():
            if status == "CRITICAL":
                penalties += 20.0
            elif status == "DEGRADED":
                penalties += 8.0
        return max(0.0, 100.0 - penalties)

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Formats all instantaneous telemetry readings into standard schema.
        """
        # Determine dominant fault label and severity if any
        if not self.active_faults:
            fault_label = FaultCategory.NOMINAL.value
            fault_severity = 0
            subsystem_status = "NOMINAL"
        elif len(self.active_faults) > 1:
            fault_label = FaultCategory.MULTIPLE_FAULTS.value
            fault_severity = 5
            subsystem_status = "CRITICAL"
        else:
            first_fault = list(self.active_faults.values())[0]
            fault_label = first_fault["category"]
            fault_severity = 4 if "OVERHEATING" in fault_label or "SIGNAL_LOSS" in fault_label else 3
            subsystem_status = "DEGRADED"
            
        now_ts = datetime.utcnow().isoformat()
        
        return {
            "timestamp": now_ts,
            "simulation_time": round(self.simulation_time, 2),
            "spacecraft_id": self.spacecraft_id,
            "overall_health_score": round(self.get_overall_health_score(), 1),
            "subsystem_status": subsystem_status,
            "fault_label": fault_label,
            "fault_severity": fault_severity,
            # Subsystem Telemetry parameters
            "battery_voltage": round(self.power.battery_voltage, 2),
            "battery_temperature": round(self.thermal.battery_temperature, 2),
            "battery_charge": round(self.power.battery_charge, 2),
            "solar_current": round(self.power.solar_current, 2),
            "power_consumption": round(
                95.0 + (20.0 + (self.processing.cpu_usage / 100.0) * 45.0) +
                35.0 + self.payload.payload_power + (40.0 if self.thermal.aux_cooling_active else 0.0), 2
            ),
            "cpu_temperature": round(self.thermal.cpu_temperature, 2),
            "cpu_usage": round(self.processing.cpu_usage, 2),
            "memory_usage": round(self.processing.memory_usage, 2),
            "signal_strength": round(self.comm.signal_strength, 2),
            "packet_loss": round(self.comm.packet_loss, 2),
            "communication_latency": round(self.comm.communication_latency, 2),
            "storage_usage": round(self.storage.storage_usage, 2),
            "payload_activity": round(self.payload.payload_activity, 2),
            # Detailed Subsystem States
            "subsystem_health": dict(self.subsystem_health),
            "active_faults": list(self.active_faults.keys())
        }
