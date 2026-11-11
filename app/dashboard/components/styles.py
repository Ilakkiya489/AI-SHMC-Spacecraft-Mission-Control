"""
Aerospace Mission Control Dark Theme CSS Styles.
Custom styles for NASA/ESA flight control aesthetics.
"""

AEROSPACE_CSS = """
<style>
    /* Dark Deep-Space Background */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Top Header Bar */
    .mission-header {
        background: linear-gradient(90deg, #161b22 0%, #0d1117 100%);
        border-bottom: 2px solid #30363d;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* KPI Metric Cards */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        margin-bottom: 12px;
    }
    .metric-card:hover {
        border-color: #58a6ff;
    }
    .metric-title {
        color: #8b949e;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #f0f6fc;
        margin-top: 4px;
        font-family: monospace;
    }
    .metric-subtitle {
        font-size: 0.75rem;
        color: #8b949e;
        margin-top: 2px;
    }
    
    /* Badges & Status Pills */
    .badge-nominal {
        background-color: rgba(35, 134, 54, 0.2);
        color: #3fb950;
        border: 1px solid #238636;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-warning {
        background-color: rgba(210, 153, 34, 0.2);
        color: #d29922;
        border: 1px solid #9e6a03;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-critical {
        background-color: rgba(248, 81, 73, 0.2);
        color: #f85149;
        border: 1px solid #da3633;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-cyan {
        background-color: rgba(56, 189, 248, 0.2);
        color: #38bdf8;
        border: 1px solid #0284c7;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Panel container */
    .terminal-box {
        background-color: #0b0f19;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #58a6ff;
        margin-bottom: 15px;
    }
</style>
"""

