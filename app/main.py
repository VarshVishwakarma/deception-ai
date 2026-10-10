import streamlit as st
import time
import re
import datetime
import requests
import os
import plotly.graph_objects as go
from typing import Dict, Any, List

# --- WIRE UP MODULAR UTILITIES ---
from app.utils import (
    call_analysis_api,
    validate_input,
    extract_keywords,
    get_threat_level,
    generate_explanation,
    submit_feedback  # <-- Imported the feedback function!
)

# --- CONFIGURATION ---
# Use environment variables to support both local and Docker networking seamlessly
API_BASE = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1/analyze").replace("/api/v1/analyze", "")
HEALTH_URL = f"{API_BASE}/health"
HISTORY_URL = f"{API_BASE}/api/v1/history"
APP_TITLE = "DeceptionAI"

# Set up the API Key for the History tab
API_KEY = os.getenv("API_KEY", "dai-secret-key-2026")
HEADERS = {"X-API-Key": API_KEY}

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
def inject_custom_css():
    """Injects the ultra-premium dark mode SaaS styling."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

    /* ===================== ROOT VARIABLES ===================== */
    :root {
        --bg-base: #07070d;
        --bg-surface: #0d0d18;
        --bg-elevated: #12121f;
        --bg-card: #161626;
        --border-subtle: rgba(255,255,255,0.055);
        --border-active: rgba(139,92,246,0.45);
        --accent-violet: #8B5CF6;
        --accent-violet-dim: rgba(139,92,246,0.15);
        --accent-violet-glow: rgba(139,92,246,0.25);
        --accent-red: #F43F5E;
        --accent-red-dim: rgba(244,63,94,0.12);
        --accent-green: #10B981;
        --accent-green-dim: rgba(16,185,129,0.12);
        --accent-amber: #F59E0B;
        --accent-blue: #3B82F6;
        --text-primary: #F1F0F9;
        --text-secondary: #8E8EAA;
        --text-muted: #4E4E6A;
        --font-display: 'Syne', sans-serif;
        --font-mono: 'DM Mono', monospace;
        --font-body: 'Inter', sans-serif;
        --radius-sm: 8px;
        --radius-md: 14px;
        --radius-lg: 20px;
        --radius-xl: 28px;
    }

    /* ===================== GLOBAL RESET ===================== */
    html, body, [class*="css"] {
        font-family: var(--font-body) !important;
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
    }

    /* Noise texture overlay for depth */
    body::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
        pointer-events: none;
        z-index: 0;
        opacity: 0.6;
    }

    /* ===================== LAYOUT ===================== */
    .block-container {
        width: 100% !important;
        max-width: 100% !important;
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        margin: 0 !important;
    }

    section.main > div {
        max-width: 100% !important;
        width: 100% !important;
    }

    /* ===================== SIDEBAR ===================== */
    [data-testid="stSidebar"] {
        background: var(--bg-surface) !important;
        border-right: 1px solid var(--border-subtle) !important;
        min-width: 210px !important;
        max-width: 210px !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem !important;
    }

    /* ===================== TYPOGRAPHY ===================== */
    h1, h2, h3 {
        font-family: var(--font-display) !important;
        letter-spacing: -0.02em !important;
    }
    h1 { font-size: clamp(2rem, 3.5vw, 3.2rem) !important; font-weight: 800 !important; }
    h2 { font-size: clamp(1.3rem, 2.2vw, 1.75rem) !important; font-weight: 700 !important; }
    h3 { font-size: clamp(1rem, 1.5vw, 1.2rem) !important; font-weight: 600 !important; }

    /* ===================== BUTTONS ===================== */
    .stButton > button {
        width: 100% !important;
        height: 3.6rem !important;
        font-size: 1rem !important;
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
        border-radius: var(--radius-md) !important;
        background: linear-gradient(135deg, var(--accent-violet), #6D28D9) !important;
        color: #fff !important;
        border: 1px solid rgba(139,92,246,0.4) !important;
        box-shadow: 0 0 20px rgba(139,92,246,0.2), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        transition: all 0.2s ease !important;
        text-transform: uppercase !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #9D6FF8, #7C3AED) !important;
        box-shadow: 0 0 35px rgba(139,92,246,0.4), inset 0 1px 0 rgba(255,255,255,0.15) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Secondary buttons for Feedback columns */
    div[data-testid="column"] .stButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        box-shadow: none !important;
        text-transform: none !important;
        color: var(--text-primary) !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        border-color: var(--border-active) !important;
        background: var(--bg-elevated) !important;
    }

    /* ===================== TEXT AREA ===================== */
    textarea {
        font-family: var(--font-mono) !important;
        font-size: 0.9rem !important;
        background-color: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        padding: 18px !important;
        line-height: 1.7 !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
        resize: vertical !important;
    }
    textarea:focus {
        border-color: var(--border-active) !important;
        box-shadow: 0 0 0 3px var(--accent-violet-dim), 0 0 20px var(--accent-violet-glow) !important;
        outline: none !important;
    }
    textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* ===================== TOGGLE / CONTROLS ===================== */
    [data-testid="stToggle"] span {
        background-color: var(--accent-violet) !important;
    }

    /* ===================== DIVIDERS ===================== */
    hr {
        border: none !important;
        height: 1px !important;
        background: var(--border-subtle) !important;
        margin: 1.5rem 0 !important;
    }

    /* ===================== PROGRESS BAR ===================== */
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, var(--accent-violet), var(--accent-blue)) !important;
        border-radius: 999px !important;
    }
    [data-testid="stProgressBar"] > div {
        background: var(--bg-elevated) !important;
        border-radius: 999px !important;
    }

    /* ===================== CUSTOM COMPONENTS ===================== */

    /* Hero */
    .dai-hero {
        padding: 5rem 6rem;
        border-radius: var(--radius-xl);
        background: linear-gradient(135deg, #0d0d20 0%, #111130 50%, #0d0d1d 100%);
        border: 1px solid var(--border-subtle);
        text-align: center;
        position: relative;
        overflow: hidden;
        margin-bottom: 2rem;
    }
    .dai-hero::before {
        content: '';
        position: absolute;
        top: -60px; left: 50%;
        transform: translateX(-50%);
        width: 500px; height: 200px;
        background: radial-gradient(ellipse, rgba(139,92,246,0.18) 0%, transparent 70%);
        pointer-events: none;
    }
    .dai-hero::after {
        content: '';
        position: absolute;
        bottom: -40px; left: 50%;
        transform: translateX(-50%);
        width: 300px; height: 100px;
        background: radial-gradient(ellipse, rgba(59,130,246,0.1) 0%, transparent 70%);
        pointer-events: none;
    }
    .dai-hero-eyebrow {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--accent-violet);
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .dai-hero-eyebrow::before,
    .dai-hero-eyebrow::after {
        content: '';
        display: inline-block;
        width: 32px; height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent-violet));
    }
    .dai-hero-eyebrow::after {
        background: linear-gradient(90deg, var(--accent-violet), transparent);
    }
    .dai-hero-title {
        font-family: var(--font-display) !important;
        font-size: clamp(2.8rem, 5vw, 5rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        line-height: 1 !important;
        background: linear-gradient(135deg, #fff 30%, rgba(139,92,246,0.85) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 1rem !important;
    }
    .dai-hero-sub {
        font-family: var(--font-body);
        font-size: 1.1rem;
        color: var(--text-secondary);
        width: 100%;
        max-width: 900px;
        margin: 0 auto 1.8rem;
        line-height: 1.8;
    }
    .dai-hero-badges {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .dai-pill {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        padding: 5px 12px;
        border-radius: 999px;
        border: 1px solid var(--border-subtle);
        background: var(--bg-card);
        color: var(--text-secondary);
        letter-spacing: 0.05em;
    }
    .dai-pill.active {
        border-color: rgba(16,185,129,0.3);
        background: rgba(16,185,129,0.08);
        color: var(--accent-green);
    }

    /* Input Console */
    .dai-console {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.75rem 2rem;
        margin-bottom: 0.5rem;
    }
    .dai-console-label {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--accent-violet);
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .dai-console-label::before {
        content: '●';
        color: var(--accent-violet);
        font-size: 0.5rem;
        animation: blink 1.5s infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    /* Verdict Banner */
    .dai-verdict {
        padding: 1.25rem 2rem;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
    }
    .dai-verdict.low {
        background: rgba(16,185,129,0.07);
        border: 1px solid rgba(16,185,129,0.22);
    }
    .dai-verdict.medium {
        background: rgba(245,158,11,0.07);
        border: 1px solid rgba(245,158,11,0.22);
    }
    .dai-verdict.high {
        background: rgba(244,63,94,0.07);
        border: 1px solid rgba(244,63,94,0.22);
    }
    .dai-verdict-icon { font-size: 1.5rem; }
    .dai-verdict-label {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        opacity: 0.6;
    }
    .dai-verdict-text {
        font-family: var(--font-display);
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 2px;
    }
    .dai-verdict.low .dai-verdict-text { color: var(--accent-green); }
    .dai-verdict.medium .dai-verdict-text { color: var(--accent-amber); }
    .dai-verdict.high .dai-verdict-text { color: var(--accent-red); }

    /* Metric Cards */
    .dai-metrics-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    .dai-metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.5rem 1.75rem;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        cursor: default;
    }
    .dai-metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }
    .dai-metric-card::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        border-radius: 2px 2px 0 0;
    }
    .dai-metric-card.green::after { background: linear-gradient(90deg, transparent, var(--accent-green), transparent); }
    .dai-metric-card.red::after { background: linear-gradient(90deg, transparent, var(--accent-red), transparent); }
    .dai-metric-card.blue::after { background: linear-gradient(90deg, transparent, var(--accent-blue), transparent); }
    .dai-metric-card.green:hover { border-color: rgba(16,185,129,0.25); }
    .dai-metric-card.red:hover { border-color: rgba(244,63,94,0.25); }
    .dai-metric-card.blue:hover { border-color: rgba(59,130,246,0.25); }
    .dai-metric-label {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--text-muted);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }
    .dai-metric-value {
        font-family: var(--font-display);
        font-size: 2.6rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.03em;
    }
    .dai-metric-value.green { color: var(--accent-green); }
    .dai-metric-value.red { color: var(--accent-red); }
    .dai-metric-value.blue { color: var(--accent-blue); }
    .dai-metric-sub {
        font-size: 0.78rem;
        color: var(--text-muted);
        margin-top: 0.4rem;
    }

    /* Section headers */
    .dai-section-header {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--text-muted);
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .dai-section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border-subtle);
    }

    /* Explanation box */
    .dai-insight {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-left: 3px solid var(--accent-violet);
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        padding: 1.4rem 1.6rem;
        color: var(--text-secondary);
        font-size: 0.92rem;
        line-height: 1.7;
        margin-bottom: 1.5rem;
    }
    .dai-insight strong { color: var(--text-primary); }

    /* Text display */
    .dai-text-display {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.4rem 1.6rem;
        font-family: var(--font-mono);
        font-size: 0.86rem;
        color: var(--text-secondary);
        line-height: 1.85;
    }

    /* Highlight */
    .highlight {
        background: rgba(244,63,94,0.18);
        color: #FF8098;
        padding: 2px 7px;
        border-radius: 5px;
        border: 1px solid rgba(244,63,94,0.3);
        font-weight: 500;
    }

    /* Tag chips */
    .dai-tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 5px 12px;
        border-radius: 999px;
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.04em;
        margin: 3px 3px 3px 0;
        border: 1px solid;
    }
    .dai-tag.flag {
        background: rgba(244,63,94,0.08);
        border-color: rgba(244,63,94,0.25);
        color: #FF8098;
    }
    .dai-tag.emotion {
        background: rgba(139,92,246,0.1);
        border-color: rgba(139,92,246,0.3);
        color: #C4B5FD;
    }
    .dai-tag.threat-low {
        background: rgba(16,185,129,0.08);
        border-color: rgba(16,185,129,0.25);
        color: #6EE7B7;
    }
    .dai-tag.threat-medium {
        background: rgba(245,158,11,0.08);
        border-color: rgba(245,158,11,0.25);
        color: #FCD34D;
    }
    .dai-tag.threat-high {
        background: rgba(244,63,94,0.08);
        border-color: rgba(244,63,94,0.25);
        color: #FCA5A5;
    }

    /* Sidebar components */
    .dai-sidebar-logo {
        font-family: var(--font-display);
        font-size: 1.3rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .dai-status-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .dai-status-dot.online { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
    .dai-status-dot.offline { background: var(--accent-red); box-shadow: 0 0 6px var(--accent-red); }

    .dai-sys-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-subtle);
        font-size: 0.82rem;
    }
    .dai-sys-row .key { color: var(--text-muted); font-family: var(--font-mono); font-size: 0.72rem; }
    .dai-sys-row .val { color: var(--text-secondary); font-weight: 500; }

    /* Right panel info card */
    .dai-info-card {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }
    .dai-info-card-title {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        color: var(--text-muted);
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }
    
    /* Feedback container */
    .dai-feedback-box {
        background: var(--bg-elevated);
        border: 1px dashed var(--border-active);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        text-align: center;
        margin-top: 2rem;
    }
    
    /* History Log Cards */
    .dai-history-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .dai-history-card:hover {
        transform: translateY(-2px);
        border-color: var(--border-active);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .dai-history-main {
        flex: 1;
        padding-right: 2rem;
    }
    .dai-history-text {
        font-family: var(--font-body);
        font-size: 0.95rem;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        line-height: 1.6;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .dai-history-meta {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--text-muted);
        display: flex;
        gap: 15px;
    }
    .dai-history-score-box {
        text-align: right;
        min-width: 120px;
    }
    .dai-history-score-val {
        font-family: var(--font-display);
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1;
    }
    .dai-history-score-label {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER UI FUNCTIONS ---

def check_backend_status() -> bool:
    try:
        response = requests.get(HEALTH_URL, timeout=1.5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def render_gauge(score: float, threat: str):
    """Renders a stunning Plotly gauge dynamically scaling colors to the threat."""
    bar_color = {"Low": "#10B981", "Medium": "#F59E0B", "High": "#F43F5E"}.get(threat, "#8B5CF6")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score * 100,
        number={
            'font': {'size': 52, 'family': 'Syne, sans-serif', 'color': bar_color},
            'suffix': '%',
        },
        title={
            'text': "DECEPTION RISK",
            'font': {'size': 11, 'family': 'DM Mono, monospace', 'color': '#4E4E6A'},
        },
        gauge={
            'axis': {
                'range': [0, 100],
                'tickcolor': '#2A2A3C',
                'tickwidth': 1,
                'tickfont': {'size': 10, 'color': '#4E4E6A', 'family': 'DM Mono, monospace'},
                'nticks': 6,
            },
            'bar': {'color': bar_color, 'thickness': 0.18},
            'bgcolor': '#0d0d18',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': 'rgba(16,185,129,0.08)'},
                {'range': [40, 70], 'color': 'rgba(245,158,11,0.08)'},
                {'range': [70, 100], 'color': 'rgba(244,63,94,0.08)'},
            ],
            'threshold': {
                'line': {'color': bar_color, 'width': 2},
                'thickness': 0.85,
                'value': score * 100
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"},
        height=520,
        margin=dict(l=20, r=20, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

def highlight_suspicious_words(text: str, words: List[str]) -> str:
    highlighted = text
    for word in words:
        pattern = re.compile(rf'\b({re.escape(word)})\b', re.IGNORECASE)
        highlighted = pattern.sub(r'<span class="highlight">\1</span>', highlighted)
    return highlighted

def get_mock_response(text: str) -> Dict[str, Any]:
    """Provides a safe, realistic fallback for Demo Mode using our utils logic."""
    score = 0.88
    emotion = "Defensive"
    extracted = extract_keywords(text)
    
    return {
        "truth_score": 0.32,
        "deception_score": score,
        "confidence_score": 0.94,
        "emotion": emotion,
        "explanation": generate_explanation(score, emotion),
        "suspicious_words": extracted if extracted else ["honestly", "literally", "trust me"],
        "threat_level": get_threat_level(score)
    }

# --- MAIN ---
def main():
    inject_custom_css()
    is_backend_online = check_backend_status()

    # --- SESSION STATE (Memory) ---
    # This ensures the app remembers the analysis when feedback buttons trigger a refresh!
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "analyzed_text" not in st.session_state:
        st.session_state.analyzed_text = ""
    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="dai-sidebar-logo">👁️ DeceptionAI</div>', unsafe_allow_html=True)
        st.markdown('<div class="dai-section-header">System Status</div>', unsafe_allow_html=True)
        
        dot_class = "online" if is_backend_online else "offline"
        status_text = "Backend Connected" if is_backend_online else "Backend Offline"
        
        st.markdown(f"""
        <div class="dai-sys-row">
            <span class="key">API</span>
            <span class="val"><span class="dai-status-dot {dot_class}"></span>{status_text}</span>
        </div>
        <div class="dai-sys-row">
            <span class="key">Model</span>
            <span class="val">DistilBERT</span>
        </div>
        <div class="dai-sys-row">
            <span class="key">Version</span>
            <span class="val">1.0.0</span>
        </div>
        <div class="dai-sys-row">
            <span class="key">Mode</span>
            <span class="val">Live Analysis</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="dai-section-header">Configuration</div>', unsafe_allow_html=True)
        use_demo_mode = st.toggle("Demo Mode", value=False, help="Use mock data instead of calling the live backend.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="dai-section-header">About</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.8rem; color: #4E4E6A; line-height:1.7;">
        DeceptionAI applies psycholinguistic analysis and cognitive load theory to surface deception markers in natural language.
        </div>
        """, unsafe_allow_html=True)

    # ── HERO ─────────────────────────────────────────────────────────────────
    ts = datetime.datetime.now().strftime('%Y-%m-%d · %H:%M:%S UTC')
    st.markdown(f"""
    <div class="dai-hero">
        <div class="dai-hero-eyebrow">Cognitive Analysis Engine</div>
        <div class="dai-hero-title">DeceptionAI</div>
        <div class="dai-hero-sub">
            Real-time psycholinguistic deception analysis powered by transformer-based language models and behavioral heuristics.
        </div>
        <div class="dai-hero-badges">
        <span class="dai-pill active">● Live</span>
        <span class="dai-pill">DistilBERT</span>
        <span class="dai-pill">v1.0.0</span>
        <span class="dai-pill">{ts}</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABS CONFIGURATION ───────────────────────────────────────────────────
    tab_live, tab_history = st.tabs(["👁️ Live Analysis", "📚 Analysis History"])

    with tab_live:
        # ── INPUT CONSOLE ─────────────────────────────────────────────────────────
        st.markdown('<div class="dai-console">', unsafe_allow_html=True)
        st.markdown('<div class="dai-console-label">Input Statement</div>', unsafe_allow_html=True)
        user_input = st.text_area(
            "statement",
            height=180,
            label_visibility="collapsed",
            placeholder="Paste a message, email, or statement here to analyze for deception patterns…"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        analyze_button = st.button("⚡  Run Analysis")

        # ── ANALYSIS EXECUTION ────────────────────────────────────────────────────
        if analyze_button:
            # 1. Reset the feedback state for a fresh analysis
            st.session_state.feedback_submitted = False
            
            if not validate_input(user_input):
                st.warning("⚠️ Please enter a valid statement to analyze (minimum 10 characters).")
            else:
                st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
        
                try:
                    with st.spinner("Analyzing linguistic patterns…"):
                        time.sleep(0.4)
        
                    # Smooth UI loader
                    prog = st.progress(0)
                    for i in range(100):
                        time.sleep(0.002)
                        prog.progress(i + 1)
                    prog.empty()
        
                    # 2. Store the result strictly in session state! 
                    st.session_state.analyzed_text = user_input
                    if use_demo_mode:
                        time.sleep(0.3)
                        st.session_state.analysis_result = get_mock_response(user_input)
                    else:
                        st.session_state.analysis_result = call_analysis_api(user_input)
                        
                except Exception as e:
                    st.error("An error occurred during analysis or rendering.")
                    with st.expander("Debug info"):
                        st.code(str(e))

        # ── UI RENDERING (Based on Session State Memory) ──────────────────────────
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            text_to_display = st.session_state.analyzed_text
            
            score = result.get("deception_score", 0.0)
            truth = result.get("truth_score", 0.0)
            confidence = result.get("confidence_score", 0.0)
            emotion = result.get("emotion", "Neutral").capitalize()
            
            threat = get_threat_level(score)
            words = extract_keywords(text_to_display)
            explanation = generate_explanation(score, emotion)

            verdict_class = threat.lower()
            verdict_icons = {"Low": "✓", "Medium": "⚠", "High": "✕"}
            verdict_texts = {
                "Low": "Truthful Communication Detected",
                "Medium": "Ambiguous — Further Verification Advised",
                "High": "Deception Pattern Detected"
            }
            
            st.markdown(f"""
            <div class="dai-verdict {verdict_class}">
                <div class="dai-verdict-icon">{verdict_icons.get(threat, '?')}</div>
                <div>
                    <div class="dai-verdict-label">Verdict</div>
                    <div class="dai-verdict-text">{verdict_texts.get(threat, '')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="dai-metrics-row">
                <div class="dai-metric-card green">
                    <div class="dai-metric-label">Authenticity Score</div>
                    <div class="dai-metric-value green">{truth*100:.0f}<span style="font-size:1.2rem">%</span></div>
                    <div class="dai-metric-sub">Truthful linguistic pattern</div>
                </div>
                <div class="dai-metric-card red">
                    <div class="dai-metric-label">Deception Risk</div>
                    <div class="dai-metric-value red">{score*100:.0f}<span style="font-size:1.2rem">%</span></div>
                    <div class="dai-metric-sub">Fabrication probability</div>
                </div>
                <div class="dai-metric-card blue">
                    <div class="dai-metric-label">Confidence</div>
                    <div class="dai-metric-value blue">{confidence*100:.0f}<span style="font-size:1.2rem">%</span></div>
                    <div class="dai-metric-sub">Model certainty</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            left, right = st.columns([1.8, 1.2], gap="large")

            with left:
                st.markdown('<div class="dai-section-header">AI Cognitive Breakdown</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="dai-insight">💡 {explanation}</div>', unsafe_allow_html=True)

                st.markdown('<div class="dai-section-header">Linguistic Evidence</div>', unsafe_allow_html=True)
                highlighted = highlight_suspicious_words(text_to_display, words)
                st.markdown(f'<div class="dai-text-display">"{highlighted}"</div>', unsafe_allow_html=True)

                st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
                st.markdown('<div class="dai-section-header">Detected Flags</div>', unsafe_allow_html=True)
                if not words:
                    st.markdown('<span style="color:var(--text-muted);font-size:0.85rem">No suspicious markers detected.</span>', unsafe_allow_html=True)
                else:
                    flags_html = "".join(f'<span class="dai-tag flag">⚑ {w}</span>' for w in words)
                    st.markdown(f"<div>{flags_html}</div>", unsafe_allow_html=True)

            with right:
                st.markdown('<div class="dai-section-header">Risk Gauge</div>', unsafe_allow_html=True)
                render_gauge(score, threat)

                st.markdown('<div class="dai-info-card">', unsafe_allow_html=True)
                st.markdown('<div class="dai-info-card-title">Threat Classification</div>', unsafe_allow_html=True)
                threat_tag_class = {"Low": "threat-low", "Medium": "threat-medium", "High": "threat-high"}.get(threat, "threat-low")
                threat_icons = {"Low": "●", "Medium": "▲", "High": "■"}
                st.markdown(f'<span class="dai-tag {threat_tag_class}">{threat_icons.get(threat,"")} {threat} Risk</span>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div class="dai-info-card">', unsafe_allow_html=True)
                st.markdown('<div class="dai-info-card-title">Emotional State</div>', unsafe_allow_html=True)
                st.markdown(f'<span class="dai-tag emotion">🎭 {emotion}</span>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div class="dai-info-card">', unsafe_allow_html=True)
                st.markdown('<div class="dai-info-card-title">Analysis Metadata</div>', unsafe_allow_html=True)
                word_count = len(text_to_display.split())
                flag_count = len(words)
                st.markdown(f"""
                <div class="dai-sys-row">
                    <span class="key">Word count</span>
                    <span class="val">{word_count}</span>
                </div>
                <div class="dai-sys-row">
                    <span class="key">Flags found</span>
                    <span class="val">{flag_count}</span>
                </div>
                <div class="dai-sys-row">
                    <span class="key">Source</span>
                    <span class="val">{'Demo' if use_demo_mode else 'Live API'}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # ── CONTINUOUS LEARNING FEEDBACK LOOP ─────────────────────────────────────
            st.markdown('<div class="dai-feedback-box">', unsafe_allow_html=True)
            st.markdown('<h4 style="margin-top: 0;">🔄 Continuous Learning</h4>', unsafe_allow_html=True)
            st.markdown("<p style='color: var(--text-muted); font-size: 0.9rem;'>Help improve the model by verifying if this statement was actually truthful or deceptive.</p>", unsafe_allow_html=True)
            
            # Show buttons only if feedback has NOT been submitted yet
            if not st.session_state.feedback_submitted:
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                with col2:
                    if st.button("👍 Verified Truthful"):
                        success = submit_feedback(text_to_display, 0)
                        if success:
                            st.session_state.feedback_submitted = True
                            st.rerun() # Re-render to show success message while keeping analysis visible!
                        else:
                            st.error("Failed to submit feedback. Backend may be unreachable.")
                with col3:
                    if st.button("👎 Verified Deceptive"):
                        success = submit_feedback(text_to_display, 1)
                        if success:
                            st.session_state.feedback_submitted = True
                            st.rerun() # Re-render to show success message while keeping analysis visible!
                        else:
                            st.error("Failed to submit feedback. Backend may be unreachable.")
            else:
                # Beautiful success message confirming the data is in the database
                st.success("✨ Ground truth securely logged! The model will use this data to self-improve in the next training cycle.")
                
            st.markdown('</div>', unsafe_allow_html=True)

    # ── HISTORY TAB ──────────────────────────────────────────────────────────
    with tab_history:
        st.markdown('<div class="dai-section-header">Recent Database Records</div>', unsafe_allow_html=True)
        
        if use_demo_mode:
            st.info("ℹ️ History is disabled in Demo Mode. Connect to the live database to view records.")
        elif not is_backend_online:
            st.warning("⚠️ Backend is offline. Cannot fetch history.")
        else:
            try:
                with st.spinner("Fetching historical data..."):
                    # NOTICE: Sending the HEADERS payload with our secure API_KEY!
                    history_response = requests.get(f"{HISTORY_URL}?limit=10", headers=HEADERS, timeout=5)
                    
                if history_response.status_code == 200:
                    records = history_response.json()
                    
                    if not records:
                        st.markdown("<div style='text-align: center; color: var(--text-muted); padding: 2rem;'>No analysis records found in the database.</div>", unsafe_allow_html=True)
                    else:
                        for record in records:
                            text = record.get("original_text", "")
                            score = record.get("deception_score", 0.0)
                            emotion = record.get("emotion", "Unknown").capitalize()
                            created_at = record.get("created_at", "").split("T")[0]
                            
                            threat = get_threat_level(score)
                            score_color = "var(--accent-green)" if threat == "Low" else "var(--accent-amber)" if threat == "Medium" else "var(--accent-red)"
                            
                            st.markdown(f"""
                            <div class="dai-history-card">
                                <div class="dai-history-main">
                                    <div class="dai-history-text">"{text}"</div>
                                    <div class="dai-history-meta">
                                        <span>📅 {created_at}</span>
                                        <span>🎭 {emotion}</span>
                                        <span>🔍 Confidence: {record.get('confidence', 0.0)*100:.0f}%</span>
                                    </div>
                                </div>
                                <div class="dai-history-score-box">
                                    <div class="dai-history-score-val" style="color: {score_color};">{score*100:.0f}%</div>
                                    <div class="dai-history-score-label">Deception Risk</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                elif history_response.status_code == 403:
                    st.error("🚨 Access Denied! API Key invalid or missing.")
                            
            except requests.exceptions.RequestException:
                st.error("Failed to connect to the database to fetch history.")

if __name__ == "__main__":
    main()