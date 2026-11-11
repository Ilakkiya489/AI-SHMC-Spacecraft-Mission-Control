# AI-SHMC: AI-Based Self-Healing Mission Control Copilot for Autonomous Spacecraft Operations

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)]()

> **Core Philosophy:**  
> *"Detect intelligently. Predict proactively. Simulate before acting. Assess risk independently. Recover autonomously when safe. Involve humans when necessary. Verify every recovery."*

---

## 1. Project Overview

**AI-SHMC** is a comprehensive, production-grade final-year major project prototype demonstrating an AI-powered ground control and autonomous spacecraft health management copilot. 

Traditional spacecraft health monitoring systems depend heavily on fixed out-of-limit threshold alarms. However, detecting an abnormal parameter deviation alone cannot determine root causes, forecast progressive cascading failures, or identify safe recovery procedures.

AI-SHMC addresses this challenge through an 8-stage closed-loop operational pipeline:

```
DETECT ──> DIAGNOSE ──> PREDICT ──> SIMULATE ──> ASSESS RISK ──> DECIDE ──> SELF-HEAL ──> VERIFY
```

### Key Technical Contributions
1. **6-Subsystem Spacecraft Digital Twin:** Stateful, coupled simulation of Power, Thermal, Communication, Processing, Storage, and Payload subsystems with day/night orbital cycles and realistic physics.
2. **AI/ML Intelligence Suite:**
   - **Anomaly Detection:** Unsupervised Isolation Forest paired with statistical 3-sigma dynamic threshold baselines.
   - **Fault Diagnosis:** Multiclass Random Forest classifier isolating 10 distinct fault categories with calibrated diagnostic confidence.
   - **Predictive Analytics:** Multi-horizon regressors forecasting parameter trajectories (1, 3, 5, 10 minutes) to anticipate hazardous trends.
3. **Digital Twin What-If Sandbox:** Deep-clones the running spacecraft state to forward-simulate candidate recovery actions in an isolated sandbox, ranking strategies without risking the live spacecraft.
4. **Independent FMEA Risk Engine & Safety Gateway:**
   - Evaluates **Fault Risk** ($S \times P$: 1–25) and **Recovery Action Risk** independently.
   - Four-level autonomy gate (**Level 1: Autonomous**, **Level 2: Conditional**, **Level 3: Human Approval**, **Level 4: Safe-State Escalation**).
5. **Human-in-the-Loop Interface:** Interactive operator review and sign-off queue for high-risk operations.
6. **Empirical Recovery Verification:** Collects post-recovery telemetry to verify quantifiable parameter improvements before certifying success.
7. **Aerospace Mission Control Console:** Dark aerospace-themed multi-view dashboard built with Streamlit and Plotly across 10 functional console pages.

---

## 2. Project Folder Structure

```
Major project/
│
├── app/
│   ├── __init__.py                     # Package bootstrap & dependency configuration
│   ├── main.py                         # Master FastAPI server entry point
│   ├── config.py                       # Physical specs, nominal ranges, and recovery metadata
│   │
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── spacecraft_twin.py          # Spacecraft state machine & deep-cloning engine
│   │   ├── subsystem_models.py         # Power, Thermal, Comm, CPU, Storage, Payload models
│   │   ├── fault_injector.py           # 10 scenario injection catalog & profiles
│   │   └── telemetry_generator.py      # Synthetic telemetry generator (12,000+ records)
│   │
│   ├── ai_models/
│   │   ├── __init__.py
│   │   ├── anomaly_detection.py        # Isolation Forest & 3-sigma attribution
│   │   ├── fault_diagnosis.py          # Multiclass Random Forest fault classifier
│   │   ├── prediction.py               # Multi-horizon telemetry regressors (1m, 3m, 5m, 10m)
│   │   ├── train_models.py             # Automated end-to-end training pipeline
│   │   └── model_evaluation.py         # Holdout test metrics & baseline benchmarks
│   │
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── what_if_simulator.py        # Isolated Digital Twin forward simulation sandbox
│   │   ├── decision_engine.py          # 8-stage autonomous copilot orchestrator
│   │   └── mission_objectives.py       # Multi-objective optimization fitness scoring
│   │
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── risk_assessment.py          # FMEA Fault Risk (S x P) & AI confidence evaluation
│   │   ├── action_risk_evaluator.py    # Independent recovery action risk & reversibility
│   │   ├── safety_constraints.py       # Inviolable physical limits & mutual exclusion
│   │   └── safety_autonomy_manager.py  # 8-step deterministic safety gate (Levels 1-4)
│   │
│   ├── recovery/
│   │   ├── __init__.py
│   │   ├── recovery_engine.py          # Bounded command dispatch, retries & rollback
│   │   ├── human_approval.py           # Operator sign-off queue & decision audit trail
│   │   └── recovery_verification.py    # Empirical delta improvement verification
│   │
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── api.py                      # 25 FastAPI REST API endpoints
│   │   ├── schemas.py                  # Pydantic validation schemas
│   │   └── database.py                 # SQLite ORM models (9 persistent audit tables)
│   │
│   └── dashboard/
│       ├── __init__.py
│       ├── dashboard.py                # 10-page Streamlit Mission Control application
│       └── components/
│           ├── styles.py               # NASA/ESA aerospace dark theme CSS
│           └── telemetry_charts.py     # Plotly line charts, gauges & radar plots
│
├── data/
│   ├── synthetic/                      # Generated synthetic telemetry (12,000 records)
│   ├── processed/                      # Reproducible Train (70%), Val (15%), Test (15%) splits
│   └── ai_shmc.db                      # SQLite flight audit database
│
├── models/
│   ├── anomaly_detector.joblib         # Serialized Isolation Forest model
│   ├── fault_diagnoser.joblib          # Serialized Random Forest classifier
│   ├── telemetry_predictor.joblib      # Serialized multi-horizon regressors
│   └── evaluation_metrics.json         # Holdout test evaluation benchmark results
│
├── tests/
│   ├── test_simulation.py              # Subsystems, physics propagation & clone isolation
│   ├── test_anomaly_detection.py       # Isolation Forest & parameter attribution
│   ├── test_risk_and_safety.py         # FMEA scoring, action risk & autonomy levels
│   ├── test_recovery_and_verification.py # Execution, retries, rollback & verification
│   └── test_integration.py             # Mandatory Cases A, B, and C end-to-end tests
│
├── documentation/
│   ├── SYSTEM_ARCHITECTURE.md          # Comprehensive architectural & mathematical specs
│   └── ACADEMIC_REPORT_DRAFT.md        # Academic thesis draft (Chapters 1 to 10)
│
├── requirements.txt                    # Pinned lightweight dependencies
├── .env.example                        # Environment configuration template
├── .gitignore                          # Git ignore rules
└── README.md                           # Master project guide
```

---

## 3. Ubuntu Linux Installation Guide

### Prerequisites
- Ubuntu 20.04 LTS or 22.04 LTS
- Python 3.8+ (`python3`, `python3-pip`)
- Standard CPU (no GPU required; optimized for AMD Ryzen / Intel i3/i5/i7)

### Step 1: Clone or Navigate to Project
```bash
cd "/home/rguktrkvalley/Desktop/Major project"
```

### Step 2: Install Python Dependencies
```bash
# Option A: Install via pip
pip3 install --user -r requirements.txt

# Or install dependencies into local workspace directory
pip3 install --target .deps -r requirements.txt
```

---

## 4. Model Training & Evaluation

To generate 12,000 synthetic telemetry records across nominal flight and 10 fault scenarios, split data without leakage, and train all AI models:

```bash
python3 app/ai_models/train_models.py
```

### Output Artefacts
- `data/synthetic/synthetic_spacecraft_telemetry.csv` (12,000 records)
- `data/processed/train_telemetry.csv` (8,398 train samples)
- `data/processed/val_telemetry.csv` (1,796 validation samples)
- `data/processed/test_telemetry.csv` (1,806 test samples)
- `models/anomaly_detector.joblib`
- `models/fault_diagnoser.joblib`
- `models/telemetry_predictor.joblib`
- `models/evaluation_metrics.json`

---

## 5. Running the Application

### 5.1 Launch the FastAPI Backend
Start the REST API server:
```bash
python3 app/main.py
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger UI Docs: `http://localhost:8000/docs`
- ReDoc Docs: `http://localhost:8000/redoc`

### 5.2 Launch the Mission Control Dashboard
In a new terminal window:
```bash
python3 -m streamlit run app/dashboard/dashboard.py --server.port 8501 --server.address 0.0.0.0
```
- Mission Control Web Console: `http://localhost:8501`

---

## 6. Running Automated Tests

Run the full automated test suite containing 17 unit and integration tests:

```bash
python3 -m pytest tests/ -v
```

### Test Suite Summary
| Test Module | Coverage Scope | Status |
|---|---|---|
| `test_simulation.py` | Physics propagation, 6 subsystems, clone isolation | **PASSED** (4/4) |
| `test_anomaly_detection.py` | Isolation Forest detection, quantitative attribution, diagnosis | **PASSED** (3/3) |
| `test_risk_and_safety.py` | FMEA S x P (1–25), action risk, autonomy level gating | **PASSED** (4/4) |
| `test_recovery_and_verification.py`| Command dispatch, retry limits, rollback, empirical verification | **PASSED** (3/3) |
| `test_integration.py` | Mandatory Cases A, B, and C end-to-end workflows | **PASSED** (3/3) |
| **Total** | **Comprehensive End-to-End Test Suite** | **17 / 17 PASSED** |

---

## 7. Demonstration Guide: The 3 Canonical Flight Cases

### CASE A: LOW RISK (Autonomous Self-Healing)
- **Scenario:** Communication Packet Loss (Scenario 5)
- **Procedure:**
  1. In the sidebar under **Fault Injection Suite**, select `5: Communication Packet Loss` and click **Inject Fault**.
  2. Click **🧠 Copilot Cycle**.
  3. Navigate to **3. AI Anomaly Detection**: Observe anomaly detected in Communication subsystem (`packet_loss`).
  4. Navigate to **7. Risk & Safety Center**: Fault risk is classified as **LOW** (Score 4/25), Action risk is **LOW**, and AI Confidence is **HIGH**.
  5. The safety gate assigns **LEVEL 1: AUTONOMOUS RECOVERY**.
  6. Navigate to **9. Recovery Operations**: `RETRY_COMM_TRANSMISSION` was automatically executed without waiting for human input. Post-recovery verification confirms packet loss reduced to $<0.5\%$.

### CASE B: HIGH RISK (Human-in-the-Loop Approval)
- **Scenario:** Battery Overheating (Scenario 1)
- **Procedure:**
  1. Select `1: Battery Overheating` and click **Inject Fault**.
  2. Click **Step Sim** for 3–5 ticks, then click **🧠 Copilot Cycle**.
  3. Navigate to **4. Fault Diagnosis**: Model diagnoses `Battery Overheating` with high confidence.
  4. Navigate to **6. Digital Twin What-If**: Forward simulation ranks 5 recovery candidates in an isolated sandbox clone, selecting `REDUCE_PAYLOAD_ACTIVITY`.
  5. Navigate to **7. Risk & Safety Center**: Fault risk is classified as **HIGH** (Score 16/25).
  6. The safety gate assigns **LEVEL 3: HUMAN APPROVAL REQUIRED**. Autonomous execution is **BLOCKED**.
  7. Navigate to **8. Human Approval Center**: View the pending approval dossier. Enter operator notes and click **✅ APPROVE RECOVERY**.
  8. Action executes post-approval; verify temperature drops back to nominal 24°C in **9. Recovery Operations**.

### CASE C: CRITICAL / UNCERTAIN (Safe-State Escalation)
- **Scenario:** Multiple Simultaneous Subsystem Faults (Scenario 10)
- **Procedure:**
  1. Select `10: Multiple Simultaneous Subsystem Faults` and click **Inject Fault**.
  2. Click **🧠 Copilot Cycle**.
  3. Navigate to **7. Risk & Safety Center**: Compound multi-subsystem hazard detected (Battery Overheating + Solar Degradation).
  4. The safety gate assigns **LEVEL 4: SAFE-STATE ESCALATION**.
  5. Unsafe non-emergency recovery actions are blocked. The system automatically triggers the emergency safe-hold configuration (`ENTER_SAFE_HOLD`), locking sun-pointing, shedding non-essential loads, and raising high-priority flight alerts.

---

## 8. Known Limitations & Future Enhancements

1. **Software Simulation Boundary:** This is an aerospace research software prototype developed for academic demonstration; it does not directly drive physical satellite hardware or claim flight certification.
2. **Deterministic Orbit Simplification:** Orbital day/night cycles use a simplified 10-minute accelerated period rather than full 90-minute Keplerian SGP4 propagation.
3. **Future Hardware-in-the-Loop (HIL):** Future work will deploy the Python decision engine onto radiation-tolerant ARM/RISC-V embedded flight hardware connected over a CAN/SpaceWire bus emulator.

---

## 9. Academic Citation

If using this project for academic research or thesis work, please cite:
```bibtex
@btechthesis{ai_shmc_2026,
  author       = {Department of Computer Science and Engineering},
  title        = {AI-Based Self-Healing Mission Control Copilot for Autonomous Spacecraft Operations (AI-SHMC)},
  year         = {2026},
  school       = {Major Project Final Year B.Tech Dissertation}
}
```

