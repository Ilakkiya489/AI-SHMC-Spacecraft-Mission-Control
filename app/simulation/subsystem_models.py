"""
Subsystem Models for the AI-SHMC Digital Twin.
Implements stateful physics and operational dependencies across:
- Power Subsystem
- Thermal Subsystem
- Communication Subsystem
- Processing Subsystem
- Storage Subsystem
- Payload Subsystem
"""

import math
from typing import Dict, Any
from app.config import SubsystemName


class PowerSubsystem:
    def __init__(self):
        self.battery_voltage = 28.5        # Volts (nominal ~28.0 - 30.0V)
        self.battery_current = 4.2         # Amps (positive = discharging, negative = charging)
        self.battery_charge = 92.0         # Percentage 0-100%
        self.solar_voltage = 32.0          # Volts
        self.solar_current = 8.5           # Amps
        self.solar_efficiency = 1.0        # Factor 0.0 - 1.0
        self.sunlit = True                 # Orbit sunlit vs eclipse
        self.power_bus_backup = False      # Primary vs backup bus
        self.solar_panel_offset_deg = 0.0  # Misalignment angle
        
    def step(self, dt_s: float, payload_power: float, cpu_usage: float, aux_cooling: bool):
        # Base bus load + CPU + Payload + Subsystems
        base_power = 95.0
        cpu_power = 20.0 + (cpu_usage / 100.0) * 45.0
        comm_power = 35.0
        cooling_power = 40.0 if aux_cooling else 0.0
        total_consumption = base_power + cpu_power + comm_power + payload_power + cooling_power
        
        # Solar generation
        if self.sunlit:
            cos_angle = max(0.1, math.cos(math.radians(self.solar_panel_offset_deg)))
            self.solar_current = 10.5 * self.solar_efficiency * cos_angle
            self.solar_voltage = 32.0 * max(0.5, self.solar_efficiency)
            solar_power = self.solar_voltage * self.solar_current
        else:
            self.solar_current = 0.0
            self.solar_voltage = 0.0
            solar_power = 0.0
            
        net_power = solar_power - total_consumption
        
        # Battery state update: 1 kWh battery (~3600000 Joules)
        capacity_ws = 3600000.0
        delta_energy = net_power * dt_s
        delta_pct = (delta_energy / capacity_ws) * 100.0
        self.battery_charge = max(5.0, min(100.0, self.battery_charge + delta_pct))
        
        # Battery voltage responds to charge state and net current
        nominal_v = 24.0 + (self.battery_charge / 100.0) * 6.5
        if net_power < 0:
            # Discharging
            discharge_current = abs(net_power) / max(18.0, nominal_v)
            self.battery_current = discharge_current
            self.battery_voltage = max(18.0, nominal_v - (discharge_current * 0.12))
        else:
            # Charging
            charge_current = net_power / max(18.0, nominal_v)
            self.battery_current = -charge_current
            self.battery_voltage = min(33.5, nominal_v + (charge_current * 0.08))
            
        return total_consumption


class ThermalSubsystem:
    def __init__(self):
        self.battery_temperature = 23.5     # °C
        self.cpu_temperature = 42.0         # °C
        self.internal_temperature = 20.0    # °C
        self.radiator_louver_open = 0.5     # 0.0 to 1.0 (50% nominal)
        self.aux_cooling_active = False
        self.cooling_efficiency = 1.0
        
    def step(self, dt_s: float, power_consumption: float, cpu_usage: float, battery_current: float):
        # Thermal generation
        # Battery Joule heating: I^2 * R
        battery_heat_w = (battery_current ** 2) * 0.18
        cpu_heat_w = 15.0 + (cpu_usage / 100.0) * 50.0
        internal_heat_w = (power_consumption * 0.25)
        
        # Radiative heat rejection capacity
        effective_cooling = (30.0 + self.radiator_louver_open * 40.0) * self.cooling_efficiency
        if self.aux_cooling_active:
            effective_cooling += 50.0
            
        # Differential equations for temperatures (thermal inertia approach)
        # Deep space background sink is ~ -10°C spacecraft skin equilibrium
        t_sink = -10.0
        
        # Battery thermal exchange with chassis and own dissipation
        battery_heat_balance = battery_heat_w - (effective_cooling * 0.35 * (self.battery_temperature - t_sink) / 50.0)
        self.battery_temperature += (battery_heat_balance / 450.0) * dt_s
        
        # CPU thermal exchange
        cpu_heat_balance = cpu_heat_w - (effective_cooling * 0.65 * (self.cpu_temperature - self.internal_temperature) / 25.0)
        self.cpu_temperature += (cpu_heat_balance / 120.0) * dt_s
        
        # Internal ambient
        chassis_balance = internal_heat_w - (effective_cooling * 0.4 * (self.internal_temperature - t_sink) / 40.0)
        self.internal_temperature += (chassis_balance / 600.0) * dt_s


class CommunicationSubsystem:
    def __init__(self):
        self.signal_strength = -82.0       # dBm (nominal -95 to -65 dBm)
        self.packet_loss = 0.4             # % (nominal < 2.5%)
        self.communication_latency = 195.0 # ms (nominal 120 to 380 ms)
        self.data_rate_kbps = 1024.0
        self.connection_status = "CONNECTED"
        self.antenna_tracking_error = 0.0  # degrees
        self.rf_interference = 0.0         # 0.0 to 1.0
        
    def step(self, dt_s: float):
        # Base RF performance influenced by antenna alignment and interference
        base_rssi = -78.0 - (self.antenna_tracking_error * 8.5) - (self.rf_interference * 35.0)
        self.signal_strength = max(-130.0, min(-55.0, base_rssi))
        
        if self.signal_strength < -110.0:
            self.packet_loss = min(100.0, self.packet_loss + 15.0 * dt_s)
            self.communication_latency = min(2000.0, self.communication_latency + 180.0 * dt_s)
            self.connection_status = "LOST" if self.packet_loss > 80.0 else "DEGRADED"
        elif self.signal_strength < -95.0:
            self.packet_loss = min(40.0, max(2.5, self.packet_loss + 2.0 * dt_s))
            self.communication_latency = min(800.0, max(350.0, self.communication_latency + 20.0 * dt_s))
            self.connection_status = "DEGRADED"
        else:
            # Return towards nominal
            self.packet_loss = max(0.1, self.packet_loss - 1.5 * dt_s)
            self.communication_latency = max(140.0, min(320.0, self.communication_latency - 10.0 * dt_s))
            self.connection_status = "CONNECTED"


class ProcessingSubsystem:
    def __init__(self):
        self.cpu_usage = 32.0              # %
        self.memory_usage = 44.0           # %
        self.processing_latency = 18.0     # ms
        self.process_leak_active = False
        self.cpu_throttle_active = False
        
    def step(self, dt_s: float, payload_activity: float):
        # Base CPU usage + payload processing load
        target_cpu = 18.0 + (payload_activity / 100.0) * 35.0
        if self.cpu_throttle_active:
            target_cpu *= 0.5
            
        if self.process_leak_active:
            target_cpu += 45.0
            self.memory_usage = min(98.5, self.memory_usage + 0.8 * dt_s)
        else:
            # Memory usage nominal baseline
            nominal_mem = 38.0 + (payload_activity / 100.0) * 15.0
            self.memory_usage += (nominal_mem - self.memory_usage) * 0.1 * dt_s
            
        self.cpu_usage += (target_cpu - self.cpu_usage) * 0.25 * dt_s
        self.cpu_usage = max(5.0, min(100.0, self.cpu_usage))
        self.processing_latency = 12.0 + (self.cpu_usage / 100.0) * 55.0


class StorageSubsystem:
    def __init__(self):
        self.storage_usage = 48.0          # %
        self.rw_speed_mbps = 145.0         # MB/s
        self.data_integrity_status = "VALID"
        self.storage_error_count = 0
        self.high_rate_logging = True
        
    def step(self, dt_s: float, data_rate_mb_s: float, comm_status: str):
        # Storage fills up with incoming payload data
        logging_rate = 0.05 if self.high_rate_logging else 0.01
        net_inflow_mb = (data_rate_mb_s + logging_rate) * dt_s
        
        # Downlink clears storage if comm is connected
        downlink_mb = (2.5 * dt_s) if comm_status == "CONNECTED" else 0.0
        net_storage_mb = net_inflow_mb - downlink_mb
        
        # 128 GB SSD total storage
        capacity_mb = 131072.0
        delta_pct = (net_storage_mb / capacity_mb) * 100.0
        self.storage_usage = max(10.0, min(100.0, self.storage_usage + delta_pct))
        
        if self.storage_usage > 95.0:
            self.storage_error_count += 1
            self.data_integrity_status = "DEGRADED"
        else:
            self.data_integrity_status = "VALID"


class PayloadSubsystem:
    def __init__(self):
        self.payload_activity = 45.0       # %
        self.payload_power = 75.0          # Watts (nominal 30 - 150W)
        self.sensor_status = "OPERATIONAL"
        self.data_collection_rate = 1.2    # MB/s
        self.malfunction = False
        
    def step(self, dt_s: float):
        if self.malfunction:
            self.sensor_status = "ERROR"
            self.payload_power = 185.0     # Power spike
            self.data_collection_rate = 0.05
            self.payload_activity = 95.0
        else:
            self.sensor_status = "OPERATIONAL"
            self.payload_power = 25.0 + (self.payload_activity / 100.0) * 90.0
            self.data_collection_rate = (self.payload_activity / 100.0) * 2.2

