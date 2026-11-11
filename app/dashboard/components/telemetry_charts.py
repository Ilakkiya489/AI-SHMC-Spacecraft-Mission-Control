"""
Plotly Chart Generators for AI-SHMC Aerospace Dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any, Optional


def create_telemetry_line_chart(
    df: pd.DataFrame,
    param_col: str,
    title: str,
    nominal_min: Optional[float] = None,
    nominal_max: Optional[float] = None,
    unit: str = ""
) -> go.Figure:
    """Creates a real-time dark aerospace line chart with nominal threshold bands."""
    fig = go.Figure()
    
    # Time axis (simulation time or record index)
    x_axis = df["simulation_time"] if "simulation_time" in df.columns else list(range(len(df)))
    
    # Main signal trace
    fig.add_trace(go.Scatter(
        x=x_axis,
        y=df[param_col],
        mode="lines",
        name=param_col.replace("_", " ").title(),
        line=dict(color="#58a6ff", width=2.5),
        hovertemplate=f"%{{y:.2f}} {unit}<extra></extra>"
    ))
    
    # Threshold lines if provided
    if nominal_max is not None:
        fig.add_hline(
            y=nominal_max,
            line_dash="dot",
            line_color="#f85149",
            annotation_text=f"Max Safe ({nominal_max} {unit})",
            annotation_position="top right"
        )
    if nominal_min is not None:
        fig.add_hline(
            y=nominal_min,
            line_dash="dot",
            line_color="#d29922",
            annotation_text=f"Min Safe ({nominal_min} {unit})",
            annotation_position="bottom right"
        )
        
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#e6edf3")),
        plot_bgcolor="#161b22",
        paper_bgcolor="#161b22",
        margin=dict(l=40, r=40, t=40, b=30),
        height=260,
        xaxis=dict(
            title="Simulation Elapsed (s)",
            gridcolor="#21262d",
            zerolinecolor="#21262d",
            tickfont=dict(color="#8b949e")
        ),
        yaxis=dict(
            title=unit,
            gridcolor="#21262d",
            zerolinecolor="#21262d",
            tickfont=dict(color="#8b949e")
        ),
        legend=dict(font=dict(color="#8b949e"))
    )
    return fig


def create_gauge_chart(
    value: float,
    title: str,
    min_val: float = 0.0,
    max_val: float = 100.0,
    unit: str = "%",
    threshold_warning: float = 70.0,
    threshold_critical: float = 85.0,
    reverse_color: bool = False
) -> go.Figure:
    """Creates a dark aerospace circular gauge indicator."""
    if not reverse_color:
        bar_color = "#3fb950" if value < threshold_warning else ("#d29922" if value < threshold_critical else "#f85149")
    else:
        bar_color = "#f85149" if value < threshold_critical else ("#d29922" if value < threshold_warning else "#3fb950")
        
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=f" {unit}", font=dict(color="#f0f6fc", size=22)),
        title=dict(text=title, font=dict(size=13, color="#8b949e")),
        gauge=dict(
            axis=dict(range=[min_val, max_val], tickcolor="#8b949e", tickfont=dict(color="#8b949e")),
            bar=dict(color=bar_color, thickness=0.75),
            bgcolor="#21262d",
            borderwidth=1,
            bordercolor="#30363d"
        )
    ))
    fig.update_layout(
        paper_bgcolor="#161b22",
        plot_bgcolor="#161b22",
        margin=dict(l=20, r=20, t=30, b=20),
        height=180
    )
    return fig


def create_prediction_comparison_plot(
    target_name: str,
    current_val: float,
    pred_val: float,
    horizon_min: int,
    unit: str
) -> go.Figure:
    """Visualizes trajectory from current telemetry to predicted value with horizon line."""
    fig = go.Figure()
    
    x_points = [0, horizon_min]
    y_points = [current_val, pred_val]
    
    fig.add_trace(go.Scatter(
        x=x_points,
        y=y_points,
        mode="lines+markers",
        line=dict(color="#38bdf8", width=3, dash="dash"),
        marker=dict(size=10, color=["#58a6ff", "#f85149" if pred_val > current_val else "#3fb950"]),
        name="Projected Trajectory"
    ))
    
    fig.update_layout(
        title=dict(text=f"{target_name} ({horizon_min}-min Forecast)", font=dict(size=13, color="#e6edf3")),
        plot_bgcolor="#161b22",
        paper_bgcolor="#161b22",
        margin=dict(l=35, r=35, t=35, b=30),
        height=200,
        xaxis=dict(
            title="Horizon (Minutes)",
            gridcolor="#21262d",
            tickvals=[0, horizon_min],
            ticktext=["Current (t0)", f"+{horizon_min}m"],
            tickfont=dict(color="#8b949e")
        ),
        yaxis=dict(
            title=unit,
            gridcolor="#21262d",
            tickfont=dict(color="#8b949e")
        )
    )
    return fig


def create_strategy_ranking_chart(strategies: List[Dict[str, Any]]) -> go.Figure:
    """Bar chart comparing candidate recovery strategy fitness scores."""
    df_strat = pd.DataFrame(strategies)
    fig = px.bar(
        df_strat,
        x="action",
        y="fitness_score",
        color="action_risk",
        color_discrete_map={
            "LOW": "#3fb950",
            "MEDIUM": "#d29922",
            "HIGH": "#f85149",
            "CRITICAL": "#da3633"
        },
        text="fitness_score",
        title="Digital Twin Candidate Strategy Evaluation & Fitness Ranking"
    )
    fig.update_layout(
        plot_bgcolor="#161b22",
        paper_bgcolor="#161b22",
        margin=dict(l=40, r=40, t=40, b=30),
        height=280,
        xaxis=dict(title="Candidate Recovery Action", tickfont=dict(color="#8b949e")),
        yaxis=dict(title="Fitness Score (0-100)", range=[0, 105], gridcolor="#21262d", tickfont=dict(color="#8b949e")),
        legend=dict(title="Action Risk", font=dict(color="#8b949e"))
    )
    return fig

