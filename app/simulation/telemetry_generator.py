"""
Telemetry Data Generator for AI-SHMC.
Generates realistic normal and abnormal synthetic spacecraft telemetry.
Produces at least 10,000 records across 10 fault scenarios and nominal flight,
with reproducible train/val/test splits and zero data leakage.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

from app.config import FaultCategory, RANDOM_SEED
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.simulation.fault_injector import FaultInjector, SCENARIOS_CATALOG


class TelemetryGenerator:
    def __init__(self, seed: int = RANDOM_SEED):
        self.seed = seed
        self.random = random.Random(seed)
        np.random.seed(seed)
        
    def generate_dataset(
        self,
        total_records: int = 12000,
        nominal_ratio: float = 0.50,
        output_dir: str = "data/synthetic"
    ) -> pd.DataFrame:
        """
        Generates structured telemetry records across nominal operations
        with orbital day/night cycles and all 10 fault scenarios with episodic variety.
        """
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        
        records = []
        base_time = datetime(2026, 11, 1, 0, 0, 0)
        current_time = base_time
        
        nominal_steps = int(total_records * nominal_ratio)
        fault_steps_total = total_records - nominal_steps
        scenarios = list(SCENARIOS_CATALOG.keys())
        steps_per_scenario = fault_steps_total // len(scenarios)
        
        print(f"[TelemetryGenerator] Generating {nominal_steps} nominal records with day/night orbital cycles...")
        
        # 1. Generate realistic nominal flight with orbital cycles
        twin = SpacecraftTwin()
        orbit_period_s = 600.0  # 10 min accelerated orbit: 60% sunlit, 40% eclipse
        
        for i in range(nominal_steps):
            dt = 1.0
            orbital_phase = (twin.simulation_time % orbit_period_s) / orbit_period_s
            twin.power.sunlit = (orbital_phase < 0.60)
            
            # Natural payload operation changes
            if i % 120 == 0:
                twin.payload.payload_activity = self.random.uniform(25.0, 65.0)
                
            twin.step(dt)
            current_time += timedelta(seconds=dt)
            
            telemetry = twin.get_telemetry()
            telemetry["timestamp"] = current_time.isoformat()
            self._apply_sensor_noise(telemetry)
            records.append(telemetry)
            
        # 2. Generate scenario fault blocks in multiple episodes
        print(f"[TelemetryGenerator] Generating {len(scenarios)} fault scenarios ({steps_per_scenario} records each)...")
        episodes_per_scenario = 6
        steps_per_episode = steps_per_scenario // episodes_per_scenario
        
        for sc_id in scenarios:
            for ep in range(episodes_per_scenario):
                twin = SpacecraftTwin()
                injector = FaultInjector(twin)
                
                # Randomized baseline conditions for diversity
                twin.power.battery_charge = self.random.uniform(75.0, 95.0)
                twin.payload.payload_activity = self.random.uniform(25.0, 60.0)
                twin.thermal.battery_temperature = self.random.uniform(20.0, 26.0)
                
                # Pre-fault stabilization (15% of episode)
                pre_steps = max(5, steps_per_episode // 7)
                for _ in range(pre_steps):
                    twin.step(1.0)
                    current_time += timedelta(seconds=1.0)
                    telem = twin.get_telemetry()
                    telem["timestamp"] = current_time.isoformat()
                    self._apply_sensor_noise(telem)
                    records.append(telem)
                    
                # Inject fault
                intensity = self.random.uniform(0.9, 1.2)
                injector.inject_scenario(sc_id, intensity=intensity)
                
                # Active fault progression
                active_steps = steps_per_episode - pre_steps
                for _ in range(active_steps):
                    twin.step(1.0)
                    current_time += timedelta(seconds=1.0)
                    telem = twin.get_telemetry()
                    telem["timestamp"] = current_time.isoformat()
                    self._apply_sensor_noise(telem)
                    records.append(telem)
                    
        df = pd.DataFrame(records)
        
        # Filter and structure exact dataset fields
        columns_order = [
            "timestamp",
            "simulation_time",
            "battery_voltage",
            "battery_temperature",
            "battery_charge",
            "solar_current",
            "power_consumption",
            "cpu_temperature",
            "cpu_usage",
            "memory_usage",
            "signal_strength",
            "packet_loss",
            "communication_latency",
            "storage_usage",
            "payload_activity",
            "overall_health_score",
            "subsystem_status",
            "fault_label",
            "fault_severity"
        ]
        
        # Retain extra metadata if needed, but ensure required columns are present
        df = df[[col for col in columns_order if col in df.columns]]
        
        # Save raw synthetic dataset
        raw_csv_path = os.path.join(output_dir, "synthetic_spacecraft_telemetry.csv")
        df.to_csv(raw_csv_path, index=False)
        print(f"[TelemetryGenerator] Successfully generated {len(df)} records -> {raw_csv_path}")
        
        return df

    def _apply_sensor_noise(self, telem: Dict[str, Any]):
        """
        Adds realistic Gaussian measurement noise to floating point sensors.
        """
        telem["battery_voltage"] = round(telem["battery_voltage"] + self.random.gauss(0, 0.04), 2)
        telem["battery_temperature"] = round(telem["battery_temperature"] + self.random.gauss(0, 0.08), 2)
        telem["solar_current"] = round(max(0.0, telem["solar_current"] + self.random.gauss(0, 0.05)), 2)
        telem["cpu_temperature"] = round(telem["cpu_temperature"] + self.random.gauss(0, 0.12), 2)
        telem["cpu_usage"] = round(max(0.0, min(100.0, telem["cpu_usage"] + self.random.gauss(0, 0.5))), 2)
        telem["memory_usage"] = round(max(0.0, min(100.0, telem["memory_usage"] + self.random.gauss(0, 0.2))), 2)
        telem["signal_strength"] = round(telem["signal_strength"] + self.random.gauss(0, 0.3), 2)
        telem["communication_latency"] = round(max(50.0, telem["communication_latency"] + self.random.gauss(0, 1.5)), 2)

    def split_dataset(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        output_dir: str = "data/processed"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits dataset into reproducible train, validation, and test splits without data leakage.
        Uses stratified group sampling across fault scenarios to ensure equal representation.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        train_dfs = []
        val_dfs = []
        test_dfs = []
        
        # Group by fault label to ensure balanced split across all scenarios
        for fault_label, group in df.groupby("fault_label"):
            n = len(group)
            n_train = int(n * train_ratio)
            n_val = int(n * val_ratio)
            
            # Temporal contiguous chunks within each scenario block to avoid temporal leakage
            train_group = group.iloc[:n_train]
            val_group = group.iloc[n_train:n_train + n_val]
            test_group = group.iloc[n_train + n_val:]
            
            train_dfs.append(train_group)
            val_dfs.append(val_group)
            test_dfs.append(test_group)
            
        train_df = pd.concat(train_dfs).sample(frac=1.0, random_state=self.seed).reset_index(drop=True)
        val_df = pd.concat(val_dfs).sample(frac=1.0, random_state=self.seed).reset_index(drop=True)
        test_df = pd.concat(test_dfs).sample(frac=1.0, random_state=self.seed).reset_index(drop=True)
        
        train_df.to_csv(os.path.join(output_dir, "train_telemetry.csv"), index=False)
        val_df.to_csv(os.path.join(output_dir, "val_telemetry.csv"), index=False)
        test_df.to_csv(os.path.join(output_dir, "test_telemetry.csv"), index=False)
        
        print(f"[TelemetryGenerator] Splits saved: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
        return train_df, val_df, test_df


if __name__ == "__main__":
    generator = TelemetryGenerator()
    df = generator.generate_dataset(total_records=12000)
    train_df, val_df, test_df = generator.split_dataset(df)
