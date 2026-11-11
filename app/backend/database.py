"""
SQLite Database Layer for AI-SHMC.
Maintains persistent audit logs for:
- Telemetry records
- Anomaly events
- Fault diagnoses
- Predictive telemetry
- Risk assessments
- Recovery actions executed
- Human operator approvals
- Recovery verifications
- Mission event history
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    Boolean,
    desc
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

os.makedirs("data", exist_ok=True)
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TelemetryRecordDB(Base):
    __tablename__ = "telemetry_records"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    simulation_time = Column(Float)
    spacecraft_id = Column(String(50))
    overall_health_score = Column(Float)
    subsystem_status = Column(String(50))
    fault_label = Column(String(100), index=True)
    fault_severity = Column(Integer)
    battery_voltage = Column(Float)
    battery_temperature = Column(Float)
    battery_charge = Column(Float)
    solar_current = Column(Float)
    power_consumption = Column(Float)
    cpu_temperature = Column(Float)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    signal_strength = Column(Float)
    packet_loss = Column(Float)
    communication_latency = Column(Float)
    storage_usage = Column(Float)
    payload_activity = Column(Float)


class AnomalyEventDB(Base):
    __tablename__ = "anomaly_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    is_anomaly = Column(Boolean)
    anomaly_score = Column(Float)
    detection_status = Column(String(50))
    primary_parameter = Column(String(100), nullable=True)
    primary_subsystem = Column(String(100), nullable=True)
    primary_value = Column(Float, nullable=True)
    affected_parameters_json = Column(Text, nullable=True)
    summary = Column(Text)


class FaultDiagnosisDB(Base):
    __tablename__ = "fault_diagnoses"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    fault_category = Column(String(100), index=True)
    affected_subsystem = Column(String(100))
    confidence_pct = Column(Float)
    confidence_level = Column(String(50))
    severity_score = Column(Integer)
    severity_label = Column(String(50))
    explanation = Column(Text)


class PredictionDB(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    horizon_minutes = Column(Integer)
    overall_risk_trend = Column(String(50))
    predictions_json = Column(Text)
    summary = Column(Text)


class RiskAssessmentDB(Base):
    __tablename__ = "risk_assessments"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    fault_name = Column(String(100))
    fault_risk_score = Column(Integer)
    fault_risk_level = Column(String(50))
    action_name = Column(String(100))
    action_risk_level = Column(String(50))
    autonomy_level = Column(String(100))
    explanation = Column(Text)


class RecoveryActionDB(Base):
    __tablename__ = "recovery_actions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    action_name = Column(String(100), index=True)
    authorized_by = Column(String(100))
    status = Column(String(50))
    retry_attempt = Column(Integer, default=1)
    message = Column(Text)


class OperatorApprovalDB(Base):
    __tablename__ = "operator_approvals"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), unique=True, index=True)
    created_at = Column(String(50))
    detected_fault = Column(String(100))
    affected_subsystem = Column(String(100))
    recommended_action = Column(String(100))
    status = Column(String(50), index=True)
    operator_id = Column(String(50), nullable=True)
    operator_notes = Column(Text, nullable=True)
    decided_at = Column(String(50), nullable=True)


class RecoveryVerificationDB(Base):
    __tablename__ = "recovery_verifications"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    action_executed = Column(String(100))
    target_parameter = Column(String(100))
    outcome = Column(String(50), index=True)
    pre_value = Column(Float)
    post_value = Column(Float)
    health_score_gain = Column(Float)
    summary = Column(Text)


class MissionEventLogDB(Base):
    __tablename__ = "mission_event_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String(50), index=True)
    subsystem = Column(String(100), index=True)
    event_type = Column(String(100), index=True)   # ANOMALY, DIAGNOSIS, PREDICTION, RISK, RECOVERY, VERIFICATION, OPERATOR
    risk_level = Column(String(50), index=True)    # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text)
    details_json = Column(Text, nullable=True)


def init_db():
    """Initializes all database tables and seeds initial flight logs if empty."""
    Base.metadata.create_all(bind=engine)
    seed_initial_mission_logs()
    print("[Database] Schema initialized successfully.")


def seed_initial_mission_logs():
    """Seeds historical mission commissioning logs so flight event history is never blank."""
    db = SessionLocal()
    try:
        count = db.query(MissionEventLogDB).count()
        if count == 0:
            initial_events = [
                ("Power", "TELEMETRY", "LOW", "Mission Telemetry Link Established. Bus Voltage 28.5V, SoC 92.0% nominal."),
                ("Communication", "COMMISSIONING", "LOW", "S-band ground transponder locked with Madrid Deep Space Communications Complex."),
                ("Thermal", "TELEMETRY", "LOW", "Chassis and battery temperatures nominal at 23.5°C equilibrium."),
                ("Processing", "SYSTEM", "LOW", "Flight Computer Operational: Copilot Decision Engine v1.0.0 Online."),
                ("Payload", "TELEMETRY", "LOW", "Optical imaging spectrometer calibration sequence verified OK."),
                ("Safety", "AUTONOMY_GATE", "LOW", "Deterministic Safety Gate Active: Autonomy Level 1 Standby.")
            ]
            for sub, ev_type, risk, msg in initial_events:
                db.add(MissionEventLogDB(
                    timestamp=datetime.utcnow().isoformat(),
                    subsystem=sub,
                    event_type=ev_type,
                    risk_level=risk,
                    message=msg,
                    details_json=json.dumps({"source": "FLIGHT_COMMISSIONING_INITIALIZER"})
                ))
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Database Seed Warning] {e}")
    finally:
        db.close()


def log_mission_event(
    subsystem: str,
    event_type: str,
    risk_level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
):
    """Inserts a structured mission event entry."""
    db = SessionLocal()
    try:
        event = MissionEventLogDB(
            timestamp=datetime.utcnow().isoformat(),
            subsystem=subsystem,
            event_type=event_type,
            risk_level=risk_level,
            message=message,
            details_json=json.dumps(details) if details else None
        )
        db.add(event)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Database Error] Failed to log event: {e}")
    finally:
        db.close()

