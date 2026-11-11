# Final-Year B.Tech Major Project Report Draft
# AI-Based Self-Healing Mission Control Copilot for Autonomous Spacecraft Operations (AI-SHMC)

---

## Abstract

Modern spacecraft generate high-velocity, interconnected telemetry across power, thermal, communication, onboard data handling, storage, and science payload subsystems. Traditional mission operations rely predominantly on static out-of-limit threshold alarms, requiring human ground controllers to diagnose root causes and select corrective procedures. However, high orbital latency, deep space communication blackouts, and complex inter-subsystem dynamics render threshold monitoring inadequate for mission-critical anomalies.

This project designs and implements the **AI-Based Self-Healing Mission Control Copilot (AI-SHMC)**, a closed-loop autonomous flight health management system. The architecture integrates an unsupervised Isolation Forest for early anomaly detection, a multiclass Random Forest for fault diagnosis with calibrated confidence, multi-horizon regressors for prognostic consequence forecasting, and a **Digital Twin What-If simulation engine** that forward-evaluates recovery candidates in an isolated cloned state prior to flight execution. To guarantee spacecraft safety, an independent FMEA-based Risk Assessment engine and a four-level Safety Autonomy Manager enforce deterministic decision gates, requiring explicit human operator approval for high-risk interventions while autonomously executing eligible low-risk actions. A complete prototype featuring a Python Digital Twin, FastAPI backend, SQLite persistence, and a Streamlit flight console demonstrates self-healing across three canonical flight regimes: low-risk autonomous recovery, high-risk human-in-the-loop authorization, and critical safe-state escalation.

---

## 1. Introduction and Problem Statement

### 1.1 Background
Spacecraft are complex autonomous systems operating in unforgiving radiation, vacuum, and thermal environments. As exploration extends beyond Low Earth Orbit (LEO) to lunar, Martian, and deep-space missions, round-trip communication latency expands from seconds to hours. Under these operational constraints, traditional ground-in-the-loop commanding cannot intervene in time to prevent progressive hardware damage.

### 1.2 Problem Statement
Existing telemetry monitoring architectures suffer from three fundamental limitations:
1. **Lack of Severity & Context:** Static threshold monitoring detects that a parameter has drifted outside boundaries, but cannot infer whether the deviation is transient noise or a fatal precursor.
2. **Blind Recovery Execution:** Conventional rule engines attempt predefined scripts without forward-simulating side effects on coupled subsystems (e.g., turning on auxiliary cooling might inadvertently drain emergency battery reserves).
3. **Absence of Independent Risk & Confidence Gating:** Systems often treat model classification output as absolute ground truth, risking erroneous autonomous execution under out-of-distribution uncertainty.

### 1.3 Project Objectives
- Build a 6-subsystem stateful Spacecraft Digital Twin modeling realistic power, thermal, RF, CPU, flash memory, and spectrometer dynamics.
- Develop CPU-efficient AI/ML pipelines for anomaly detection, fault diagnosis, and predictive telemetry analytics.
- Create an isolated Digital Twin What-If forward simulation engine to compare recovery strategies.
- Implement an independent FMEA risk assessment engine and a 4-level deterministic safety gate.
- Build a functional Human-in-the-Loop operator sign-off interface and an empirical post-recovery verification engine.

---

## 2. Literature Review & Existing Systems

### 2.1 Existing Ground Control Paradigms
- **Out-of-Limit (OOL) Alarms:** Check if $V_{min} \le V(t) \le V_{max}$. While computationally trivial, OOL systems suffer from high false alarm rates and complete blindness to correlated subsystem drift.
- **Expert Systems / Rule Tables:** Utilize static tree scripts. They fail when unexpected compound failures occur and lack probabilistic confidence calibration.

### 2.2 Machine Learning in Spacecraft Health Management
- Unsupervised anomaly detection methods (e.g., Isolation Forest, One-Class SVM) map the nominal telemetry manifold, detecting anomalies before thresholds are breached.
- Supervised decision tree ensembles provide transparent, explainable feature attribution without the black-box opacity of deep neural networks.

---

## 3. System Architecture & Methodology

AI-SHMC implements an eight-stage closed-loop operational pipeline:

$$\text{DETECT} \longrightarrow \text{DIAGNOSE} \longrightarrow \text{PREDICT} \longrightarrow \text{SIMULATE} \longrightarrow \text{ASSESS RISK} \longrightarrow \text{DECIDE} \longrightarrow \text{SELF-HEAL} \longrightarrow \text{VERIFY}$$

### Stage 1: Detection
Ingests real-time telemetry frame $\mathbf{x}_t \in \mathbb{R}^{13}$. Isolation Forest calculates path length anomaly score $s(\mathbf{x}_t)$, supplemented by quantitative deviation metrics against critical flight boundaries.

### Stage 2: Diagnosis
Multiclass Random Forest predicts probable failure category $\hat{y}$ from 10 distinct fault modes with calibrated posterior probability $P(\hat{y}|\mathbf{x}_t)$.

### Stage 3: Predictive Analytics
Multi-horizon regressors predict target vector $\mathbf{y}_{t+h}$ for horizons $h \in \{1, 3, 5, 10\}$ minutes, detecting whether subsystem trends are escalating toward catastrophic boundaries.

### Stage 4: Digital Twin What-If Sandbox
The active spacecraft twin state $\mathcal{S}_t$ is deep-copied into isolated clone $\mathcal{S}_t'$. Candidate recovery actions $a_k \in \mathcal{A}$ are executed inside the clone and stepped forward by $T = 60\text{ s}$ to evaluate projected health gain, recovery latency, and secondary failure risks.

### Stage 5: Independent Risk Assessment
- **Fault Risk:** FMEA Risk Score $R_{fault} = S \times P \in [1, 25]$.
- **Action Risk:** Evaluates reversibility, subsystem criticality, and What-If secondary hazards independently from the fault risk.
- **AI Confidence Gating:** Confidence $< 75\%$ enforces epistemic uncertainty blocks.

### Stage 6: Deterministic Safety Autonomy Manager
Assigns autonomy level:
- **Level 1 (Autonomous):** Low fault risk + Low action risk + Confidence $\ge 75\%$.
- **Level 2 (Conditional):** Medium risk + Pre-approved action + Validated Digital Twin simulation.
- **Level 3 (Human Approval):** High fault risk or High action risk $\rightarrow$ Enters operator approval queue.
- **Level 4 (Safe-State Escalation):** Critical compound failure or Failed constraints or Low confidence $\rightarrow$ Blocks unsafe actions and engages protective safe hold.

### Stage 7: Autonomous / Authorized Recovery
Executes bounded commands on active twin with retry limits and pre-execution snapshots for state rollback.

### Stage 8: Empirical Verification
Gathers post-recovery settled telemetry. Requires quantifiable parameter delta improvement and health score gain before certifying `RECOVERY_SUCCESSFUL`.

---

## 4. Experimental Results and Discussion

### 4.1 Machine Learning Model Performance
Models were evaluated on a holdout test split of 1,806 synthetic telemetry records generated across nominal flight and 10 fault scenarios:

| Module | Algorithm | Metric | Test Score |
|---|---|---|---|
| Anomaly Detection | Isolation Forest | Precision | 0.812 |
| Anomaly Detection | Isolation Forest | Recall | 0.511 |
| Anomaly Detection | Isolation Forest | **F1-Score** | **0.627** |
| Fault Diagnosis | Random Forest (100 trees) | Accuracy | 0.724 |
| Fault Diagnosis | Random Forest (100 trees) | **Weighted F1** | **0.719** |
| Telemetry Predictor | Random Forest Regressor | Battery Temp MAE (3m) | 0.84 °C |
| Telemetry Predictor | Random Forest Regressor | Battery Voltage MAE (3m)| 0.12 V |

### 4.2 Demonstration Validation Cases
1. **Case A (Low Risk - Comm Packet Loss):**
   - Injected Scenario 5 (Packet loss spikes to 16%).
   - Diagnosis: Communication Packet Loss (Confidence: High).
   - Autonomy: Classified as **LEVEL 1: AUTONOMOUS RECOVERY**.
   - Outcome: `RETRY_COMM_TRANSMISSION` automatically executed; verified packet loss reduced to 0.2%.
2. **Case B (High Risk - Battery Overheating):**
   - Injected Scenario 1 (Battery temperature rises to 49°C).
   - Diagnosis: Battery Overheating (Confidence: 94%, FMEA Score: 16 - HIGH).
   - What-If Engine: Forward-simulated 5 recovery candidates; selected `REDUCE_PAYLOAD_ACTIVITY`.
   - Autonomy: Classified as **LEVEL 3: HUMAN APPROVAL REQUIRED**.
   - Outcome: Autonomous execution blocked; approval request generated in flight console. Upon explicit operator sign-off, recovery executed and temperature reduction to 24°C verified.
3. **Case C (Critical / Uncertain - Compound Fault):**
   - Injected Scenario 10 (Simultaneous battery overheating and solar panel degradation).
   - Autonomy: Inviolable compound hazard detected $\rightarrow$ Classified as **LEVEL 4: SAFE-STATE ESCALATION**.
   - Outcome: Unsafe recovery commands blocked; emergency protective safe-hold engaged.

---

## 5. Conclusion and Future Scope

### 5.1 Conclusion
The AI-SHMC prototype demonstrates that intelligent, predictive, risk-gated autonomy is achievable within lightweight, CPU-efficient computational budgets suitable for onboard spacecraft computers and ground stations. By separating fault diagnosis from independent action risk evaluation and forward-simulating recovery candidates via Digital Twins, the system provides transparent, explainable, and verifiable spacecraft self-healing.

### 5.2 Future Scope
- Hardware-in-the-loop (HIL) testing on embedded flight computers (e.g., ARM Cortex-R / RISC-V radiation-hardened boards).
- Reinforcement learning agents for adaptive orbital maneuvering and solar array tracking under non-stationary space weather.
- Formal verification of safety state-machine transitions using temporal logic model checking.

---

## Academic References

1. NASA Systems Engineering Handbook (NASA/SP-2016-6105 Rev 2).
2. Castet, J. F., & Saleh, J. H. (2009). Beyond reliability, a review of spacecraft anomaly and failure studies. *Reliability Engineering & System Safety*, 94(6), 1118-1128.
3. Hundman, K., Constantinou, V., Laporte, C., Colwell, I., & Soderstrom, T. (2018). Detecting spacecraft anomalies using LSTMs and nonparametric dynamic thresholding. *KDD 2018*, 387-395.
4. Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation forest. *ICDM 2008*, 413-422.
5. Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5-32.
6. Schwabacher, M. A. (2005). A survey of artificial intelligence for prognostics. *AAAI Fall Symposium on AI for Prognostics*.

