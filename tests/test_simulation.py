"""
Unit tests for Spacecraft Digital Twin and Subsystems.
"""

import pytest
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.simulation.fault_injector import FaultInjector
from app.config import SubsystemName, FaultCategory


def test_spacecraft_initialization():
    twin = SpacecraftTwin()
    telem = twin.get_telemetry()
    
    assert telem["overall_health_score"] == 100.0
    assert telem["subsystem_status"] == "NOMINAL"
    assert 26.0 <= telem["battery_voltage"] <= 32.0
    assert 10.0 <= telem["battery_temperature"] <= 35.0
    assert telem["signal_strength"] > -95.0


def test_spacecraft_physics_propagation():
    twin = SpacecraftTwin()
    initial_time = twin.simulation_time
    
    for _ in range(5):
        twin.step(1.0)
        
    assert twin.simulation_time == initial_time + 5.0
    telem = twin.get_telemetry()
    assert "battery_voltage" in telem
    assert "power_consumption" in telem


def test_fault_injection_and_clearing():
    twin = SpacecraftTwin()
    injector = FaultInjector(twin)
    
    # Inject battery overheating
    res = injector.inject_scenario(1)
    assert res["status"] == "INJECTED"
    assert FaultCategory.BATTERY_OVERHEATING.value in twin.active_faults
    
    # Step under fault
    twin.step(5.0)
    telem = twin.get_telemetry()
    assert telem["fault_label"] == FaultCategory.BATTERY_OVERHEATING.value
    assert telem["battery_temperature"] > 25.0
    
    # Clear fault
    injector.clear_all_faults()
    assert len(twin.active_faults) == 0


def test_spacecraft_clone_isolation():
    """
    CRITICAL INVARIANT: Digital Twin clone must be completely independent.
    Mutating the clone must NEVER modify the live spacecraft!
    """
    live_twin = SpacecraftTwin()
    clone_twin = live_twin.clone()
    
    # Mutate clone
    clone_twin.thermal.battery_temperature = 99.9
    clone_twin.inject_fault(FaultCategory.BATTERY_OVERHEATING.value)
    clone_twin.step(10.0)
    
    # Live twin must remain unmutated!
    live_telem = live_twin.get_telemetry()
    assert live_telem["battery_temperature"] < 40.0
    assert len(live_twin.active_faults) == 0
    assert live_telem["subsystem_status"] == "NOMINAL"

