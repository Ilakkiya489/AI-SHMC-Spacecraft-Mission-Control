"""
Fault Injector Module for AI-SHMC Simulation.
Allows manual or automated injection of 10 distinct spacecraft fault scenarios
with configurable intensity, progression profiles, and multi-subsystem cascades.
"""

from typing import Dict, Any, List
from app.config import FaultCategory
from app.simulation.spacecraft_twin import SpacecraftTwin


SCENARIOS_CATALOG: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Battery Overheating",
        "category": FaultCategory.BATTERY_OVERHEATING.value,
        "affected_subsystem": "Power / Thermal",
        "primary_symptom": "Rapid temperature rise in lithium-ion battery cells > 45°C",
        "severity": 4,
        "likelihood": 4,
        "description": "Internal cell short circuit or cooling degradation causes battery temperature to rise above safe thresholds."
    },
    2: {
        "id": 2,
        "name": "Battery Voltage Drop",
        "category": FaultCategory.BATTERY_VOLTAGE_DROP.value,
        "affected_subsystem": "Power",
        "primary_symptom": "Main bus voltage drops below 24.0V",
        "severity": 4,
        "likelihood": 3,
        "description": "Excessive discharge or cell degradation causes rapid terminal voltage drop under nominal load."
    },
    3: {
        "id": 3,
        "name": "Solar Panel Degradation",
        "category": FaultCategory.SOLAR_PANEL_DEGRADATION.value,
        "affected_subsystem": "Power",
        "primary_symptom": "Solar array current drops by >60% under full sunlight",
        "severity": 3,
        "likelihood": 3,
        "description": "Micrometeoroid strike or gimbal tracking error severely reduces solar array power generation."
    },
    4: {
        "id": 4,
        "name": "Communication Signal Loss",
        "category": FaultCategory.COMMUNICATION_SIGNAL_LOSS.value,
        "affected_subsystem": "Communication",
        "primary_symptom": "Received Signal Strength Indicator (RSSI) drops below -115 dBm",
        "severity": 4,
        "likelihood": 4,
        "description": "Antenna pointing drift or high-gain amplifier failure terminates ground link contact."
    },
    5: {
        "id": 5,
        "name": "Communication Packet Loss",
        "category": FaultCategory.COMMUNICATION_PACKET_LOSS.value,
        "affected_subsystem": "Communication",
        "primary_symptom": "Uplink/Downlink packet error rate spikes above 15%",
        "severity": 2,
        "likelihood": 2,
        "description": "Transient RF interference and channel fading cause elevated packet drop rates."
    },
    6: {
        "id": 6,
        "name": "CPU Overload",
        "category": FaultCategory.CPU_OVERLOAD.value,
        "affected_subsystem": "Processing",
        "primary_symptom": "CPU utilization saturates near 99% with processing latency > 70ms",
        "severity": 3,
        "likelihood": 3,
        "description": "Uncontrolled looping thread in telemetry compression algorithm starves other flight tasks."
    },
    7: {
        "id": 7,
        "name": "Memory Exhaustion",
        "category": FaultCategory.MEMORY_EXHAUSTION.value,
        "affected_subsystem": "Processing",
        "primary_symptom": "RAM consumption continuously increases towards 98%",
        "severity": 3,
        "likelihood": 3,
        "description": "Memory buffer leak in payload image parser continuously accumulates uncollected allocations."
    },
    8: {
        "id": 8,
        "name": "Storage Overflow",
        "category": FaultCategory.STORAGE_OVERFLOW.value,
        "affected_subsystem": "Storage",
        "primary_symptom": "Flash storage capacity reaches > 95% with write errors",
        "severity": 3,
        "likelihood": 2,
        "description": "Downlink delays combined with uninterrupted science logging fill onboard non-volatile memory."
    },
    9: {
        "id": 9,
        "name": "Payload Malfunction",
        "category": FaultCategory.PAYLOAD_MALFUNCTION.value,
        "affected_subsystem": "Payload",
        "primary_symptom": "Spectrometer reports ERROR status and consumes abnormal power > 180W",
        "severity": 3,
        "likelihood": 4,
        "description": "Science instrument sensor head experiences latch-up, halting valid data collection while drawing excessive power."
    },
    10: {
        "id": 10,
        "name": "Multiple Simultaneous Subsystem Faults",
        "category": FaultCategory.MULTIPLE_FAULTS.value,
        "affected_subsystem": "Power + Thermal + Comm",
        "primary_symptom": "Simultaneous battery thermal runaway and solar array power degradation",
        "severity": 5,
        "likelihood": 4,
        "description": "Compound failure mode: Battery overheating coincides with solar power collapse, stressing emergency power reserves."
    }
}


class FaultInjector:
    def __init__(self, twin: SpacecraftTwin):
        self.twin = twin
        
    def inject_scenario(self, scenario_id: int, intensity: float = 1.0) -> Dict[str, Any]:
        """
        Injects a scenario by numeric ID (1-10) into the active twin
        with immediate realistic physical symptom onset.
        """
        scenario = SCENARIOS_CATALOG.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario ID: {scenario_id}. Choose between 1 and 10.")
            
        category = scenario["category"]
        
        # Apply immediate realistic symptom onset so AI models and operators
        # observe the fault signature with high confidence without ambiguous delays
        if category == FaultCategory.BATTERY_OVERHEATING.value:
            self.twin.thermal.battery_temperature = max(self.twin.thermal.battery_temperature, 46.5 * intensity)
            self.twin.power.battery_voltage = max(22.0, self.twin.power.battery_voltage - 0.8 * intensity)
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.BATTERY_VOLTAGE_DROP.value:
            self.twin.power.battery_voltage = min(self.twin.power.battery_voltage, 22.5 / intensity)
            self.twin.power.battery_charge = max(25.0, self.twin.power.battery_charge - 15.0 * intensity)
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.SOLAR_PANEL_DEGRADATION.value:
            self.twin.power.solar_efficiency = 0.25
            self.twin.power.solar_current = 2.4 / intensity
            self.twin.power.solar_voltage = 20.0
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.COMMUNICATION_PACKET_LOSS.value:
            self.twin.comm.packet_loss = max(self.twin.comm.packet_loss, 15.5 * intensity)
            self.twin.comm.communication_latency = max(self.twin.comm.communication_latency, 490.0 * intensity)
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.COMMUNICATION_SIGNAL_LOSS.value:
            self.twin.comm.signal_strength = -118.0
            self.twin.comm.packet_loss = 92.0
            self.twin.comm.connection_status = "LOST"
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.CPU_OVERLOAD.value:
            self.twin.processing.cpu_usage = min(99.0, max(self.twin.processing.cpu_usage, 96.5 * intensity))
            self.twin.thermal.cpu_temperature = max(self.twin.thermal.cpu_temperature, 76.0 * intensity)
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.MEMORY_EXHAUSTION.value:
            self.twin.processing.process_leak_active = True
            self.twin.processing.memory_usage = min(98.5, max(self.twin.processing.memory_usage, 94.5 * intensity))
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.STORAGE_OVERFLOW.value:
            self.twin.storage.storage_usage = min(99.0, max(self.twin.storage.storage_usage, 96.0 * intensity))
            self.twin.storage.data_integrity_status = "DEGRADED"
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.PAYLOAD_MALFUNCTION.value:
            self.twin.payload.malfunction = True
            self.twin.payload.payload_power = 185.0 * intensity
            self.twin.payload.sensor_status = "ERROR"
            self.twin.inject_fault(category, intensity=intensity)
            
        elif category == FaultCategory.MULTIPLE_FAULTS.value:
            # Compound failure: Battery Overheating + Solar Panel Degradation
            self.twin.thermal.battery_temperature = max(self.twin.thermal.battery_temperature, 48.0 * intensity)
            self.twin.power.solar_efficiency = 0.25
            self.twin.power.solar_current = 2.2 / intensity
            self.twin.inject_fault(FaultCategory.BATTERY_OVERHEATING.value, intensity=intensity)
            self.twin.inject_fault(FaultCategory.SOLAR_PANEL_DEGRADATION.value, intensity=intensity)
            
        return {
            "scenario_id": scenario_id,
            "name": scenario["name"],
            "category": category,
            "intensity": intensity,
            "primary_symptom": scenario["primary_symptom"],
            "status": "INJECTED"
        }

    def inject_precision_override(self, overrides: Dict[str, float]) -> Dict[str, Any]:
        """
        Allows precision manual perturbation of individual physical parameters.
        """
        applied = {}
        for param, val in overrides.items():
            if param == "battery_temperature":
                self.twin.thermal.battery_temperature = float(val)
                applied[param] = float(val)
                if val > 42.0:
                    self.twin.inject_fault(FaultCategory.BATTERY_OVERHEATING.value, intensity=val / 45.0)
            elif param == "battery_voltage":
                self.twin.power.battery_voltage = float(val)
                applied[param] = float(val)
                if val < 24.0:
                    self.twin.inject_fault(FaultCategory.BATTERY_VOLTAGE_DROP.value, intensity=28.0 / max(1.0, val))
            elif param == "solar_current":
                self.twin.power.solar_current = float(val)
                applied[param] = float(val)
                if val < 3.5:
                    self.twin.inject_fault(FaultCategory.SOLAR_PANEL_DEGRADATION.value)
            elif param == "cpu_usage":
                self.twin.processing.cpu_usage = float(val)
                applied[param] = float(val)
                if val > 85.0:
                    self.twin.inject_fault(FaultCategory.CPU_OVERLOAD.value)
            elif param == "memory_usage":
                self.twin.processing.memory_usage = float(val)
                applied[param] = float(val)
                if val > 85.0:
                    self.twin.inject_fault(FaultCategory.MEMORY_EXHAUSTION.value)
            elif param == "packet_loss":
                self.twin.comm.packet_loss = float(val)
                applied[param] = float(val)
                if val > 5.0:
                    self.twin.inject_fault(FaultCategory.COMMUNICATION_PACKET_LOSS.value)
            elif param == "signal_strength":
                self.twin.comm.signal_strength = float(val)
                applied[param] = float(val)
                if val < -105.0:
                    self.twin.inject_fault(FaultCategory.COMMUNICATION_SIGNAL_LOSS.value)
            elif param == "storage_usage":
                self.twin.storage.storage_usage = float(val)
                applied[param] = float(val)
                if val > 85.0:
                    self.twin.inject_fault(FaultCategory.STORAGE_OVERFLOW.value)
            elif param == "payload_power":
                self.twin.payload.payload_power = float(val)
                applied[param] = float(val)
                if val > 150.0:
                    self.twin.inject_fault(FaultCategory.PAYLOAD_MALFUNCTION.value)
                    
        return {"status": "OVERRIDE_APPLIED", "parameters": applied}

    def clear_all_faults(self) -> Dict[str, Any]:
        """
        Clears all active faults on the twin, restoring nominal performance.
        """
        for category in list(self.twin.active_faults.keys()):
            self.twin.clear_fault(category)
        return {"status": "ALL_FAULTS_CLEARED"}

    @staticmethod
    def get_catalog() -> List[Dict[str, Any]]:
        """
        Returns list of all available fault scenarios.
        """
        return list(SCENARIOS_CATALOG.values())

