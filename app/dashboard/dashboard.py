"""
AI-SHMC: AI-Based Self-Healing Mission Control Copilot
Interactive Flight Operations Dashboard (Streamlit + Plotly).
Features 10 comprehensive aerospace mission control views.
"""

import os
import sys
import time
import json
import pandas as pd
import streamlit as st

# Ensure dependencies and project root are in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_deps_path = os.path.join(_project_root, ".deps")
if sys.version_info[:2] == (3, 8):
    if os.path.exists(_deps_path) and _deps_path not in sys.path:
        sys.path.insert(0, _deps_path)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.config import (
    SubsystemName,
    FaultCategory,
    RiskLevel,
    AutonomyLevel,
    TELEMETRY_SPECS
)
from app.simulation.spacecraft_twin import SpacecraftTwin
from app.simulation.fault_injector import FaultInjector, SCENARIOS_CATALOG
from app.ai_models.anomaly_detection import AnomalyDetector
from app.ai_models.fault_diagnosis import FaultDiagnoser
from app.ai_models.prediction import TelemetryPredictor
from app.intelligence.decision_engine import MissionControlDecisionEngine
from app.recovery.human_approval import OperatorDecision
from app.backend.database import (
    SessionLocal,
    init_db,
    seed_initial_mission_logs,
    TelemetryRecordDB,
    MissionEventLogDB,
    log_mission_event
)
from app.dashboard.components.styles import AEROSPACE_CSS
from app.dashboard.components.telemetry_charts import (
    create_telemetry_line_chart,
    create_gauge_chart,
    create_prediction_comparison_plot,
    create_strategy_ranking_chart
)

# Page configuration
st.set_page_config(
    page_title="AI-SHMC | Spacecraft Mission Control",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Aerospace Dark Theme CSS
st.markdown(AEROSPACE_CSS, unsafe_allow_html=True)

# Initialize Session State Singletons
if "twin" not in st.session_state:
    init_db()
    st.session_state.twin = SpacecraftTwin()
    st.session_state.injector = FaultInjector(st.session_state.twin)
    
    # Load AI models
    st.session_state.detector = AnomalyDetector()
    st.session_state.detector.load("models/anomaly_detector.joblib")
    
    st.session_state.diagnoser = FaultDiagnoser()
    st.session_state.diagnoser.load("models/fault_diagnoser.joblib")
    
    st.session_state.predictor = TelemetryPredictor()
    st.session_state.predictor.load("models/telemetry_predictor.joblib")
    
    # Copilot Engine
    st.session_state.copilot = MissionControlDecisionEngine(
        st.session_state.twin,
        st.session_state.detector,
        st.session_state.diagnoser,
        st.session_state.predictor
    )
    
    # Live telemetry buffer for real-time charting
    st.session_state.telemetry_history = []
    for _ in range(15):
        telem = st.session_state.twin.step(1.0)
        st.session_state.telemetry_history.append(telem)

twin: SpacecraftTwin = st.session_state.twin
copilot: MissionControlDecisionEngine = st.session_state.copilot
injector: FaultInjector = st.session_state.injector


# =====================================================================
# SIDEBAR: NAVIGATION & SPACECRAFT TELECOMMAND CONTROLS
# =====================================================================

with st.sidebar:
    st.markdown("### 🛰️ **AI-SHMC MISSION CONTROL**")
    st.caption("Self-Healing Spacecraft Copilot v1.0.0")
    st.markdown("---")
    
    page = st.radio(
        "MISSION CONSOLE VIEW",
        [
            "1. Mission Overview",
            "2. Live Telemetry",
            "3. AI Anomaly Detection",
            "4. Fault Diagnosis",
            "5. Predictive Analytics",
            "6. Digital Twin What-If",
            "7. Risk & Safety Center",
            "8. Human Approval Center",
            "9. Recovery Operations",
            "10. Mission Event Logs"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("#### ⚡ **SIMULATION CONTROLS**")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("▶ Step Sim", use_container_width=True):
            new_telem = twin.step(1.0)
            st.session_state.telemetry_history.append(new_telem)
            if len(st.session_state.telemetry_history) > 60:
                st.session_state.telemetry_history.pop(0)
            st.rerun()
            
    with col_s2:
        if st.button("🧠 Copilot Cycle", use_container_width=True):
            cycle_res = copilot.run_copilot_cycle(auto_execute_level_1=True)
            st.session_state.telemetry_history.append(cycle_res["telemetry"])
            if len(st.session_state.telemetry_history) > 60:
                st.session_state.telemetry_history.pop(0)
            st.rerun()

    speed_factor = st.select_slider("Simulation Acceleration", options=[1.0, 2.0, 5.0, 10.0], value=twin.time_acceleration)
    twin.time_acceleration = speed_factor

    if st.button("🔄 Reset Spacecraft Simulation", use_container_width=True):
        st.session_state.twin = SpacecraftTwin()
        st.session_state.injector = FaultInjector(st.session_state.twin)
        st.session_state.copilot = MissionControlDecisionEngine(
            st.session_state.twin,
            st.session_state.detector,
            st.session_state.diagnoser,
            st.session_state.predictor
        )
        st.session_state.telemetry_history = [st.session_state.twin.get_telemetry()]
        st.success("Simulation reset to nominal flight envelope.")
        st.rerun()
        
    st.markdown("---")
    st.markdown("#### ⚡ **PRECISION FAULT INJECTION**")
    
    inject_mode = st.radio("Injection Mode", ["Preset Scenarios", "Custom Parameter Tuning"], horizontal=True)
    
    if inject_mode == "Preset Scenarios":
        scenario_choice = st.selectbox(
            "Select Scenario",
            options=list(SCENARIOS_CATALOG.keys()),
            format_func=lambda x: f"{x}: {SCENARIOS_CATALOG[x]['name']}"
        )
        fault_intensity = st.slider("Fault Intensity / Severity", min_value=0.5, max_value=2.5, value=1.0, step=0.1)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("🚨 Inject Scenario", type="primary", use_container_width=True):
                res = injector.inject_scenario(scenario_choice, intensity=fault_intensity)
                # Automatically run copilot cycle so diagnosis, what-if, and approvals update immediately
                cycle_res = copilot.run_copilot_cycle(auto_execute_level_1=False)
                log_mission_event(
                    subsystem=res.get("affected_subsystem", "Simulation"),
                    event_type="FAULT_INJECTION",
                    risk_level="HIGH" if scenario_choice in [1, 2, 4, 10] else "MEDIUM",
                    message=f"Injected Scenario {scenario_choice}: {res['name']} (Intensity {fault_intensity}x)",
                    details=res
                )
                st.session_state.telemetry_history.append(twin.get_telemetry())
                st.warning(f"Injected: {res['name']} ({fault_intensity}x)")
                st.rerun()
        with col_f2:
            if st.button("🧹 Clear All", use_container_width=True):
                injector.clear_all_faults()
                log_mission_event("Simulation", "FAULT_CLEAR", "LOW", "All active simulated faults cleared.")
                st.session_state.telemetry_history.append(twin.get_telemetry())
                st.success("All faults cleared.")
                st.rerun()
    else:
        st.caption("Tune individual physical sensors directly:")
        custom_param = st.selectbox("Parameter", [
            "battery_temperature",
            "battery_voltage",
            "solar_current",
            "cpu_usage",
            "memory_usage",
            "packet_loss",
            "signal_strength",
            "storage_usage",
            "payload_power"
        ])
        
        spec = TELEMETRY_SPECS.get(custom_param, {})
        min_p = float(spec.get("critical_min", 0.0)) - 10.0
        max_p = float(spec.get("critical_max", 100.0)) + 15.0
        cur_p = float(current_telem.get(custom_param, (min_p + max_p) / 2.0))
        
        target_val = st.slider(f"Target Value ({spec.get('unit', '')})", min_value=float(min_p), max_value=float(max_p), value=float(cur_p))
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("⚡ Apply Override", type="primary", use_container_width=True):
                injector.inject_precision_override({custom_param: target_val})
                copilot.run_copilot_cycle(auto_execute_level_1=False)
                log_mission_event(
                    subsystem="Simulation",
                    event_type="PRECISION_OVERRIDE",
                    risk_level="HIGH" if target_val > spec.get("nominal_max", 9e9) else "MEDIUM",
                    message=f"Manual sensor override applied: {custom_param} = {target_val}{spec.get('unit', '')}"
                )
                st.session_state.telemetry_history.append(twin.get_telemetry())
                st.warning(f"Override applied: {custom_param} = {target_val}")
                st.rerun()
        with col_p2:
            if st.button("Reset Sensor", use_container_width=True):
                injector.clear_all_faults()
                st.session_state.telemetry_history.append(twin.get_telemetry())
                st.success("Restored nominal.")
                st.rerun()
            
    # Active Faults Display
    active_f = twin.active_faults
    if active_f:
        st.markdown("**Currently Active Faults:**")
        for f_name, f_meta in active_f.items():
            st.error(f"• {f_name} (Intensity: {f_meta.get('intensity', 1.0)}x)")
    else:
        st.caption("No active faults currently active.")
            
    st.markdown("---")
    st.caption("Active Target: SAT-AI-SHMC-01 (LEO Orbit 550km)")


# Ingest latest telemetry
current_telem = twin.get_telemetry()
df_history = pd.DataFrame(st.session_state.telemetry_history)


# =====================================================================
# PAGE 1: MISSION OVERVIEW
# =====================================================================
if page == "1. Mission Overview":
    st.markdown(f"""
    <div class="mission-header">
        <div>
            <h2 style="margin: 0; color: #58a6ff;">🛰️ AI-SHMC MISSION CONTROL OVERVIEW</h2>
            <span style="color: #8b949e; font-size: 0.85rem;">Spacecraft Health Monitoring & Self-Healing Copilot Console</span>
        </div>
        <div>
            <span class="badge-cyan">SIM TIME: {current_telem['simulation_time']}s</span>
            <span class="{'badge-nominal' if current_telem['subsystem_status'] == 'NOMINAL' else ('badge-warning' if current_telem['subsystem_status'] == 'DEGRADED' else 'badge-critical')}">
                {current_telem['subsystem_status']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Metrics Row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        health = current_telem["overall_health_score"]
        h_color = "#3fb950" if health > 80 else ("#d29922" if health > 50 else "#f85149")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Health Score</div>
            <div class="metric-value" style="color: {h_color};">{health}%</div>
            <div class="metric-subtitle">Aggregate System Vitality</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k2:
        active_f = len(current_telem["active_faults"])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Active Faults</div>
            <div class="metric-value" style="color: {'#f85149' if active_f > 0 else '#3fb950'};">{active_f}</div>
            <div class="metric-subtitle">{current_telem['fault_label']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k3:
        anom_res = st.session_state.detector.detect(current_telem)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">AI Anomaly Status</div>
            <div class="metric-value" style="color: {'#f85149' if anom_res['is_anomaly'] else '#3fb950'};">
                {anom_res['detection_status']}
            </div>
            <div class="metric-subtitle">Score: {anom_res['anomaly_score']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k4:
        # Check current autonomy level
        auto_eval = copilot.run_copilot_cycle(auto_execute_level_1=False)
        level_str = auto_eval["autonomy_decision"]["autonomy_level"].split(":")[0]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Autonomy Gate</div>
            <div class="metric-value" style="color: #38bdf8; font-size: 1.3rem;">{level_str}</div>
            <div class="metric-subtitle">{auto_eval['autonomy_decision']['decision_code']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k5:
        verif_history = copilot.verifier.verification_history
        success_count = sum(1 for v in verif_history if v["outcome"] == "RECOVERY_SUCCESSFUL")
        rate = round((success_count / max(1, len(verif_history))) * 100.0, 1) if verif_history else 100.0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Recovery Success</div>
            <div class="metric-value" style="color: #3fb950;">{rate}%</div>
            <div class="metric-subtitle">{success_count}/{len(verif_history)} Operations</div>
        </div>
        """, unsafe_allow_html=True)

    # High-Risk Human-in-the-Loop Urgent Alert Banner
    if auto_eval['autonomy_decision']['requires_human_approval'] and auto_eval['fault_diagnosis']['fault'] != "Nominal":
        f_name = auto_eval['fault_diagnosis']['fault']
        rec_act = auto_eval['autonomy_decision'].get('proposed_action', 'UNKNOWN')
        auto_lvl = auto_eval['autonomy_decision'].get('autonomy_level', 'LEVEL 3: HUMAN APPROVAL REQUIRED')
        st.error(f"""
        ### 🚨 HIGH-RISK HAZARD DETECTED: {f_name.upper()}
        **Safety Gate:** `{auto_lvl}`  
        Autonomous recovery is **BLOCKED** by flight safety rules. Human operator authorization is mandatory.  
        **Recommended Strategy:** `{rec_act}` | **AI Confidence:** `{auto_eval['fault_diagnosis']['confidence_pct']}%`
        """)
        
        col_qb1, col_qb2 = st.columns([1, 2])
        with col_qb1:
            if st.button("✅ QUICK APPROVE RECOVERY", type="primary", use_container_width=True):
                exec_res = copilot.recovery_engine.execute_recovery(rec_act, authorized_by="OVERVIEW_QUICK_SIGN_OFF")
                verif_res = copilot.verifier.verify_recovery(rec_act, "battery_temperature", exec_res["pre_telemetry"])
                log_mission_event("Overview", "OPERATOR_APPROVAL", "HIGH", f"Quick-approved recovery '{rec_act}' on overview page.")
                st.session_state.telemetry_history.append(twin.get_telemetry())
                st.success(f"Recovery executed! Status: {verif_res['outcome']}")
                st.rerun()
        with col_qb2:
            st.info("👉 To inspect the complete What-If simulation trade-offs, navigate to **8. Human Approval Center** in the sidebar.")

    # Subsystem Health Matrix
    st.markdown("#### ⚡ **SUBSYSTEM STATUS MATRIX**")
    cols = st.columns(6)
    subsystems = [
        ("Power", "battery_voltage", "V", SubsystemName.POWER.value),
        ("Thermal", "battery_temperature", "°C", SubsystemName.THERMAL.value),
        ("Communication", "signal_strength", "dBm", SubsystemName.COMMUNICATION.value),
        ("Processing", "cpu_usage", "%", SubsystemName.PROCESSING.value),
        ("Storage", "storage_usage", "%", SubsystemName.STORAGE.value),
        ("Payload", "payload_activity", "%", SubsystemName.PAYLOAD.value)
    ]
    for idx, (sub_name, param, unit, enum_val) in enumerate(subsystems):
        status = current_telem["subsystem_health"].get(enum_val, "NOMINAL")
        badge = "badge-nominal" if status == "NOMINAL" else ("badge-warning" if status == "DEGRADED" else "badge-critical")
        with cols[idx]:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <div class="metric-title">{sub_name}</div>
                <div style="margin: 8px 0;"><span class="{badge}">{status}</span></div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #58a6ff;">{current_telem[param]} {unit}</div>
                <div class="metric-subtitle">{param.replace('_', ' ')}</div>
            </div>
            """, unsafe_allow_html=True)
            
    # Workflow Architecture schematic
    st.markdown("#### 🔄 **AI-SHMC CORE WORKFLOW LIFECYCLE**")
    st.markdown("""
    ```
    [ 1. DETECT ]    --> Ingest live telemetry; evaluate Isolation Forest & 3σ thresholds.
          ↓
    [ 2. DIAGNOSE ]  --> Multiclass Random Forest identifies fault category, affected subsystem & confidence.
          ↓
    [ 3. PREDICT ]   --> Multi-horizon regressors forecast parameter trends (1m, 3m, 5m, 10m).
          ↓
    [ 4. SIMULATE ]  --> Digital Twin clones spacecraft state; runs isolated forward What-If simulations.
          ↓
    [ 5. ASSESS ]    --> Independent FMEA Fault Risk (S x P) & Recovery Action Risk evaluation.
          ↓
    [ 6. DECIDE ]    --> Deterministic Safety Gate assigns Autonomy Level (Level 1, 2, 3, or 4).
          ↓
    [ 7. RECOVER ]   --> Execute authorized recovery command or request Human-in-the-Loop operator sign-off.
          ↓
    [ 8. VERIFY ]    --> Collect post-recovery telemetry; confirm empirical delta improvement or escalate.
    ```
    """)


# =====================================================================
# PAGE 2: LIVE TELEMETRY
# =====================================================================
elif page == "2. Live Telemetry":
    st.markdown("### 📊 **REAL-TIME SPACECRAFT TELEMETRY STREAMS**")
    st.caption("Synchronous 1 Hz telemetry channels across all six mission-critical subsystems.")
    
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        fig1 = create_telemetry_line_chart(
            df_history, "battery_voltage", "Battery Voltage (Power Subsystem)",
            nominal_min=TELEMETRY_SPECS["battery_voltage"]["nominal_min"],
            nominal_max=TELEMETRY_SPECS["battery_voltage"]["nominal_max"],
            unit="V"
        )
        st.plotly_chart(fig1, use_container_width=True)
    with row1_c2:
        fig2 = create_telemetry_line_chart(
            df_history, "battery_temperature", "Battery Temperature (Thermal Subsystem)",
            nominal_min=TELEMETRY_SPECS["battery_temperature"]["nominal_min"],
            nominal_max=TELEMETRY_SPECS["battery_temperature"]["nominal_max"],
            unit="°C"
        )
        st.plotly_chart(fig2, use_container_width=True)
        
    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        fig3 = create_telemetry_line_chart(
            df_history, "cpu_usage", "CPU Utilization (Processing Subsystem)",
            nominal_min=TELEMETRY_SPECS["cpu_usage"]["nominal_min"],
            nominal_max=TELEMETRY_SPECS["cpu_usage"]["nominal_max"],
            unit="%"
        )
        st.plotly_chart(fig3, use_container_width=True)
    with row2_c2:
        fig4 = create_telemetry_line_chart(
            df_history, "signal_strength", "Signal Strength (Communication Subsystem)",
            nominal_min=TELEMETRY_SPECS["signal_strength"]["nominal_min"],
            nominal_max=TELEMETRY_SPECS["signal_strength"]["nominal_max"],
            unit="dBm"
        )
        st.plotly_chart(fig4, use_container_width=True)
        
    row3_c1, row3_c2 = st.columns(2)
    with row3_c1:
        fig5 = create_telemetry_line_chart(
            df_history, "power_consumption", "Total Bus Power Consumption (Power Subsystem)",
            nominal_min=TELEMETRY_SPECS["power_consumption"]["nominal_min"],
            nominal_max=TELEMETRY_SPECS["power_consumption"]["nominal_max"],
            unit="W"
        )
        st.plotly_chart(fig5, use_container_width=True)
    with row3_c2:
        fig6 = create_telemetry_line_chart(
            df_history, "packet_loss", "Downlink Packet Loss Rate (Comm Subsystem)",
            nominal_min=TELEMETRY_SPECS["packet_loss"]["nominal_min"],
            nominal_max=TELEMETRY_SPECS["packet_loss"]["nominal_max"],
            unit="%"
        )
        st.plotly_chart(fig6, use_container_width=True)


# =====================================================================
# PAGE 3: AI ANOMALY DETECTION
# =====================================================================
elif page == "3. AI Anomaly Detection":
    st.markdown("### 🔍 **AI ANOMALY DETECTION ENGINE**")
    st.caption("Unsupervised Isolation Forest combined with 3-Sigma Gaussian Threshold Baselines.")
    
    anom_res = st.session_state.detector.detect(current_telem)
    
    col_a1, col_a2 = st.columns([1, 2])
    with col_a1:
        fig_score = create_gauge_chart(
            value=anom_res["anomaly_score"],
            title="Isolation Forest Anomaly Score",
            min_val=0.0,
            max_val=1.0,
            unit="",
            threshold_warning=0.45,
            threshold_critical=0.70
        )
        st.plotly_chart(fig_score, use_container_width=True)
        
        status_badge = "badge-critical" if anom_res["is_anomaly"] else "badge-nominal"
        st.markdown(f"""
        <div class="terminal-box">
            <b>DETECTION STATUS:</b> <span class="{status_badge}">{anom_res['detection_status']}</span><br>
            <b>MODEL DECISION:</b> {anom_res['if_model_decision']}<br>
            <b>PRIMARY ATTRIBUTION:</b> {anom_res['primary_parameter'] or 'None'}<br>
            <b>PRIMARY SUBSYSTEM:</b> {anom_res['primary_subsystem']}<br>
            <b>OBSERVED READING:</b> {anom_res['primary_value']}{anom_res['primary_unit']}
        </div>
        """, unsafe_allow_html=True)
        
    with col_a2:
        st.markdown("#### 📋 **AFFECTED PARAMETERS ATTRIBUTION**")
        affected = anom_res["affected_parameters"]
        if affected:
            df_aff = pd.DataFrame(affected)
            st.dataframe(df_aff, use_container_width=True)
        else:
            st.success("All 13 monitored telemetry parameters are within nominal statistical bounds.")
            
        st.markdown("#### ℹ️ **DETECTION SUMMARY**")
        st.info(anom_res["summary"])


# =====================================================================
# PAGE 4: FAULT DIAGNOSIS
# =====================================================================
elif page == "4. Fault Diagnosis":
    st.markdown("### 🩺 **AI FAULT DIAGNOSIS ENGINE**")
    st.caption("Supervised Multiclass Random Forest Classifier with Calibrated Posterior Probabilities.")
    
    diag_res = st.session_state.diagnoser.diagnose(current_telem)
    
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        fig_conf = create_gauge_chart(
            value=diag_res["confidence_pct"],
            title="Diagnostic Confidence",
            min_val=0.0,
            max_val=100.0,
            unit="%",
            threshold_warning=75.0,
            threshold_critical=90.0,
            reverse_color=True
        )
        st.plotly_chart(fig_conf, use_container_width=True)
        
    with col_d2:
        st.markdown(f"""
        <div class="terminal-box">
            <h3 style="margin-top: 0; color: #58a6ff;">{diag_res['fault']}</h3>
            <b>AFFECTED SUBSYSTEM:</b> {diag_res['affected_subsystem']}<br>
            <b>DIAGNOSIS CONFIDENCE:</b> {diag_res['confidence_pct']}% ({diag_res['confidence_level']})<br>
            <b>SEVERITY LEVEL:</b> {diag_res['severity_score']}/5 ({diag_res['severity_label']})<br>
            <b>EXPLANATION:</b> {diag_res['explanation']}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🔬 **ALTERNATIVE DIAGNOSTIC HYPOTHESES**")
        alts = diag_res.get("alternates", [])
        if alts:
            df_alts = pd.DataFrame(alts)
            st.dataframe(df_alts, use_container_width=True)
        else:
            st.caption("No secondary fault hypotheses meet the minimum 2% threshold.")


# =====================================================================
# PAGE 5: PREDICTIVE ANALYTICS
# =====================================================================
elif page == "5. Predictive Analytics":
    st.markdown("### 📈 **MULTI-HORIZON TELEMETRY FORECASTING**")
    st.caption("Lightweight CPU-optimized Random Forest Regressors predicting subsystem trajectories.")
    
    horizon = st.select_slider(
        "Forecast Horizon",
        options=[1, 3, 5, 10],
        value=3,
        format_func=lambda x: f"+{x} Minutes"
    )
    
    pred_res = st.session_state.predictor.predict(current_telem, horizon_minutes=horizon)
    
    st.markdown(f"**OVERALL RISK TREND:** `{pred_res['overall_risk_trend']}`")
    st.info(pred_res["summary"])
    
    preds = pred_res["predictions"]
    p_cols = st.columns(3)
    
    with p_cols[0]:
        fig_bt = create_prediction_comparison_plot(
            "Battery Temperature",
            preds["battery_temperature"]["current_value"],
            preds["battery_temperature"]["predicted_value"],
            horizon,
            preds["battery_temperature"]["unit"]
        )
        st.plotly_chart(fig_bt, use_container_width=True)
        
    with p_cols[1]:
        fig_bv = create_prediction_comparison_plot(
            "Battery Voltage",
            preds["battery_voltage"]["current_value"],
            preds["battery_voltage"]["predicted_value"],
            horizon,
            preds["battery_voltage"]["unit"]
        )
        st.plotly_chart(fig_bv, use_container_width=True)
        
    with p_cols[2]:
        fig_ct = create_prediction_comparison_plot(
            "CPU Temperature",
            preds["cpu_temperature"]["current_value"],
            preds["cpu_temperature"]["predicted_value"],
            horizon,
            preds["cpu_temperature"]["unit"]
        )
        st.plotly_chart(fig_ct, use_container_width=True)
        
    # Model evaluation metrics from test set
    st.markdown("#### 📊 **HOLDOUT VALIDATION BENCHMARK (TEST SET)**")
    metrics_path = "models/evaluation_metrics.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            eval_metrics = json.load(f)
        pred_metrics = eval_metrics.get("predictive_analytics", {}).get(f"horizon_{horizon}m", {})
        if pred_metrics:
            df_metrics = pd.DataFrame(pred_metrics).T
            st.dataframe(df_metrics, use_container_width=True)


# =====================================================================
# PAGE 6: DIGITAL TWIN WHAT-IF SIMULATION
# =====================================================================
elif page == "6. Digital Twin What-If":
    st.markdown("### 🧪 **DIGITAL TWIN WHAT-IF SIMULATION ENGINE**")
    st.caption("Deep-cloned sandbox state evaluation. Simulates multiple recovery actions before committing to flight.")
    
    diag_res = st.session_state.diagnoser.diagnose(current_telem)
    fault_to_eval = diag_res["fault"] if diag_res["fault"] != "Nominal" else FaultCategory.BATTERY_OVERHEATING.value
    
    st.markdown(f"**Target Fault for What-If Analysis:** `{fault_to_eval}`")
    
    what_if_res = copilot.what_if_sim.evaluate_candidates(twin, fault_to_eval)
    
    # Strategy Ranking Chart
    fig_strat = create_strategy_ranking_chart(what_if_res["evaluated_strategies"])
    st.plotly_chart(fig_strat, use_container_width=True)
    
    st.markdown("#### 🏆 **ALGORITHMIC STRATEGY SELECTION**")
    st.success(what_if_res["selection_reason"])
    
    st.markdown("#### 📋 **CANDIDATE RECOVERY STRATEGIES COMPARISON TABLE**")
    df_eval = pd.DataFrame(what_if_res["evaluated_strategies"])[
        ["action", "fitness_score", "action_risk", "mission_disruption",
         "projected_battery_temp", "projected_battery_voltage", "projected_health_score"]
    ]
    st.dataframe(df_eval, use_container_width=True)


# =====================================================================
# PAGE 7: RISK & SAFETY CENTER
# =====================================================================
elif page == "7. Risk & Safety Center":
    st.markdown("### 🛡️ **RISK ASSESSMENT & SAFETY AUTONOMY MANAGER**")
    st.caption("Independent Fault Risk (FMEA S x P), Recovery Action Risk, and Deterministic Autonomy Gating.")
    
    cycle_res = copilot.run_copilot_cycle(auto_execute_level_1=False)
    auto_dec = cycle_res["autonomy_decision"]
    
    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
    with r_col1:
        f_risk = auto_dec["fault_risk_level"]
        f_color = "#3fb950" if f_risk == "LOW" else ("#d29922" if f_risk == "MEDIUM" else "#f85149")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Fault Risk (FMEA)</div>
            <div class="metric-value" style="color: {f_color};">{f_risk}</div>
            <div class="metric-subtitle">Severity x Likelihood</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r_col2:
        a_risk = auto_dec["action_risk_level"]
        a_color = "#3fb950" if a_risk == "LOW" else ("#d29922" if a_risk == "MEDIUM" else "#f85149")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Action Risk</div>
            <div class="metric-value" style="color: {a_color};">{a_risk}</div>
            <div class="metric-subtitle">Independent Hazard</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r_col3:
        conf = auto_dec["confidence_pct"]
        c_color = "#3fb950" if conf >= 90 else ("#d29922" if conf >= 75 else "#f85149")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">AI Confidence</div>
            <div class="metric-value" style="color: {c_color};">{conf}%</div>
            <div class="metric-subtitle">Autonomy Threshold: 75%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Permitted Autonomy</div>
            <div class="metric-value" style="color: #38bdf8; font-size: 1.25rem;">
                {auto_dec['autonomy_level'].split(':')[0]}
            </div>
            <div class="metric-subtitle">{auto_dec['decision_code']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("#### ⚖️ **SAFETY GATE AUDIT & RATIONALE**")
    st.markdown(f"""
    <div class="terminal-box">
        <b>DECISION CODE:</b> {auto_dec['decision_code']}<br>
        <b>AUTONOMY LEVEL:</b> {auto_dec['autonomy_level']}<br>
        <b>CAN EXECUTE AUTONOMOUSLY:</b> {auto_dec['can_execute_autonomously']}<br>
        <b>REQUIRES HUMAN APPROVAL:</b> {auto_dec['requires_human_approval']}<br>
        <b>EMERGENCY ESCALATION:</b> {auto_dec['is_escalated']}<br>
        <b>BOUNDS PASSED:</b> {auto_dec['bounds_passed']}<br>
        <b>VIOLATIONS:</b> {auto_dec['bound_violations'] or 'None'}<br>
        <b>DETERMINISTIC REASONING:</b> {auto_dec['decision_reason']}
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# PAGE 8: HUMAN APPROVAL CENTER
# =====================================================================
elif page == "8. Human Approval Center":
    st.markdown("### 🧑‍🚀 **HUMAN-IN-THE-LOOP OPERATOR APPROVAL CENTER**")
    st.caption("Level 3 High-Risk Operational Sign-Off Interface. Operator verification mandatory before execution.")
    
    # Auto-evaluate active twin state if an active fault is injected
    if twin.active_faults and not copilot.approval_manager.get_pending_requests():
        copilot.run_copilot_cycle(auto_execute_level_1=False)
        
    pending_reqs = copilot.approval_manager.get_pending_requests()
    
    if not pending_reqs:
        st.info("ℹ️ No high-risk operations currently awaiting operator authorization. Spacecraft autonomy is standing by.")
        st.markdown("#### 🧪 **INTERACTIVE HUMAN-IN-THE-LOOP DEMONSTRATOR**")
        st.caption("Click below to simulate a high-risk battery thermal runaway hazard and inspect the operator sign-off dossier:")
        if st.button("🚨 Simulate High-Risk Hazard (Battery Overheating Dossier)", type="primary"):
            injector.inject_scenario(1, intensity=1.2)
            copilot.run_copilot_cycle(auto_execute_level_1=False)
            st.session_state.telemetry_history.append(twin.get_telemetry())
            st.rerun()
    else:
        for req in pending_reqs:
            req_id = req["request_id"]
            st.markdown(f"""
            <div class="terminal-box" style="border-color: #f85149; background-color: #1a0f12;">
                <h4 style="margin: 0; color: #f85149;">🚨 APPROVAL REQUEST: #{req_id}</h4>
                <b>DETECTED FAULT:</b> <span style="color: #ff7b72; font-size: 1.1rem;">{req['detected_fault']}</span> (Subsystem: <b>{req['affected_subsystem']}</b>)<br>
                <b>FAULT RISK SCORE:</b> <span class="badge-critical">{req['fault_risk_score']}</span> | <b>ACTION RISK:</b> <span class="badge-warning">{req['recovery_action_risk']}</span><br>
                <b>AI DIAGNOSTIC CONFIDENCE:</b> <span style="color: #3fb950; font-weight: bold;">{req['ai_confidence_pct']}%</span> (Bayesian Posterior Calibration)<br>
                <b>RECOMMENDED COMMAND:</b> <code style="color: #38bdf8; font-size: 1.1rem; font-weight: bold;">{req['recommended_recovery_action']}</code><br>
                <b>PROJECTED CONSEQUENCES:</b> {req['predicted_consequences']}<br>
                <b>ALGORITHMIC REASONING:</b> {req['reason_for_recommendation']}
            </div>
            """, unsafe_allow_html=True)
            
            # Show What-If Strategies Comparison Table right inside the dossier!
            if req.get("available_recovery_strategies"):
                st.markdown("##### 🔬 **Digital Twin What-If Sandbox Evaluation for this Request:**")
                df_strats = pd.DataFrame(req["available_recovery_strategies"])[
                    ["action", "fitness_score", "action_risk", "mission_disruption", "projected_battery_temp", "projected_health_score"]
                ]
                st.dataframe(df_strats, use_container_width=True)
            
            op_notes = st.text_input(f"Operator Flight Notes (#{req_id})", key=f"notes_{req_id}", value="Approved after reviewing Digital Twin thermal projection.")
            
            c_a1, c_a2, c_a3 = st.columns(3)
            with c_a1:
                if st.button(f"✅ AUTHORIZE RECOVERY (#{req_id})", type="primary", use_container_width=True):
                    copilot.approval_manager.submit_decision(req_id, OperatorDecision.APPROVED, operator_notes=op_notes)
                    # Dispatch to recovery engine
                    exec_res = copilot.recovery_engine.execute_recovery(req["recommended_recovery_action"], authorized_by="OPERATOR_CONSOLE")
                    verif_res = copilot.verifier.verify_recovery(req["recommended_recovery_action"], "battery_temperature", exec_res["pre_telemetry"])
                    log_mission_event(
                        subsystem=req["affected_subsystem"],
                        event_type="OPERATOR_APPROVAL",
                        risk_level="HIGH",
                        message=f"Operator AUTHORIZED recovery '{req['recommended_recovery_action']}' for request #{req_id}.",
                        details={"request": req, "verification": verif_res}
                    )
                    st.session_state.telemetry_history.append(twin.get_telemetry())
                    st.success(f"Recovery executed! Verification: {verif_res['outcome']}")
                    st.rerun()
            with c_a2:
                if st.button(f"❌ REJECT RECOVERY (#{req_id})", use_container_width=True):
                    copilot.approval_manager.submit_decision(req_id, OperatorDecision.REJECTED, operator_notes=op_notes)
                    log_mission_event(
                        subsystem=req["affected_subsystem"],
                        event_type="OPERATOR_REJECTION",
                        risk_level="MEDIUM",
                        message=f"Operator REJECTED recovery '{req['recommended_recovery_action']}' for request #{req_id}."
                    )
                    st.warning(f"Action '{req['recommended_recovery_action']}' was BLOCKED by flight operator.")
                    st.rerun()
            with c_a3:
                if st.button(f"🔬 REQUEST ADDITIONAL SIMULATION (#{req_id})", use_container_width=True):
                    copilot.approval_manager.submit_decision(req_id, OperatorDecision.SIMULATE_MORE, operator_notes=op_notes)
                    st.info("Additional What-If simulation cycles dispatched to background simulator.")
                    st.rerun()
                    
    st.markdown("---")
    st.markdown("#### 📜 **OPERATOR DECISION AUDIT TRAIL**")
    history = copilot.approval_manager.decision_history
    if history:
        df_hist = pd.DataFrame(history)[["request_id", "status", "recommended_recovery_action", "operator_id", "decided_at", "operator_notes"]]
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.caption("No historical decisions recorded in current session.")


# =====================================================================
# PAGE 9: RECOVERY OPERATIONS
# =====================================================================
elif page == "9. Recovery Operations":
    st.markdown("### 🔧 **AUTONOMOUS RECOVERY & VERIFICATION OPERATIONS**")
    st.caption("Audited execution trail of flight recovery procedures and empirical post-recovery verification.")
    
    exec_history = copilot.recovery_engine.execution_log
    verif_history = copilot.verifier.verification_history
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("#### 🚀 **COMMAND DISPATCH LOG**")
        if exec_history:
            df_exec = pd.DataFrame(exec_history)[["timestamp", "action", "authorized_by", "status", "retry_attempt"]]
            st.dataframe(df_exec, use_container_width=True)
        else:
            st.caption("No recovery commands dispatched in current flight window.")
            
    with col_r2:
        st.markdown("#### 🎯 **EMPIRICAL VERIFICATION RESULTS**")
        if verif_history:
            df_verif = pd.DataFrame(verif_history)[["timestamp", "action_executed", "outcome", "pre_value", "post_value", "improved"]]
            st.dataframe(df_verif, use_container_width=True)
        else:
            st.caption("No verification events logged yet.")
            
    # Manual Rollback Tool
    st.markdown("#### ⏪ **SAFETY ROLLBACK CONTROLS**")
    active_actions = copilot.recovery_engine.active_actions
    if active_actions:
        action_to_rollback = st.selectbox("Select Action to Roll Back", options=active_actions)
        if st.button("Trigger State Rollback", use_container_width=True):
            rb_res = copilot.recovery_engine.rollback_action(action_to_rollback)
            st.warning(rb_res["message"])
            st.rerun()
    else:
        st.caption("No active reversible recovery actions eligible for rollback.")


# =====================================================================
# PAGE 10: MISSION EVENT LOGS
# =====================================================================
elif page == "10. Mission Event Logs":
    st.markdown("### 🗄️ **FLIGHT EVENT LOG ARCHIVE**")
    st.caption("Persistent SQLite flight log database supporting full mission auditability.")
    
    # Ensure database has at least baseline flight logs
    seed_initial_mission_logs()
    
    db = SessionLocal()
    try:
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            f_sub = st.selectbox("Filter Subsystem", options=["All", "Power", "Thermal", "Communication", "Processing", "Storage", "Payload", "Safety", "Simulation", "Overview"])
        with col_f2:
            f_risk = st.selectbox("Filter Risk Level", options=["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
        with col_f3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Refresh Logs", use_container_width=True):
                st.rerun()
        
        query = db.query(MissionEventLogDB)
        if f_sub != "All":
            query = query.filter(MissionEventLogDB.subsystem.ilike(f"%{f_sub}%"))
        if f_risk != "All":
            query = query.filter(MissionEventLogDB.risk_level == f_risk)
            
        logs = query.order_by(MissionEventLogDB.id.desc()).limit(100).all()
        
        if logs:
            df_logs = pd.DataFrame([{
                "ID": l.id,
                "Timestamp": l.timestamp,
                "Subsystem": l.subsystem,
                "Type": l.event_type,
                "Risk": l.risk_level,
                "Message": l.message
            } for l in logs])
            st.dataframe(df_logs, use_container_width=True)
            
            csv_data = df_logs.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Flight Logs CSV",
                data=csv_data,
                file_name="ai_shmc_flight_logs.csv",
                mime="text/csv"
            )
        else:
            st.info("No mission events match the selected filter criteria. Try selecting 'All' above.")
    finally:
        db.close()

