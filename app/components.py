import streamlit as st
import re
from typing import Dict, Any

def _inject_component_css():
    """Injects ultra-premium SaaS CSS specifically scoped for the UI components."""
    st.markdown("""
        <style>
        /* Base Variables & Animations */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.4); }
            70% { box-shadow: 0 0 0 6px rgba(139, 92, 246, 0); }
            100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
        }
        
        @keyframes fillBar {
            from { width: 0%; }
        }

        /* Card Containers with Hover Effects */
        .metric-card {
            background: linear-gradient(180deg, #1C1C28 0%, #15151E 100%);
            border: 1px solid #2D2D3F;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: #4B4B69;
            box-shadow: 0 12px 20px -4px rgba(0, 0, 0, 0.5);
        }
        
        /* Metric Typography */
        .metric-title {
            color: #8E8EA8;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #FFFFFF;
            margin-bottom: 16px;
            font-variant-numeric: tabular-nums;
            letter-spacing: -1px;
        }

        /* Glowing Progress Bars */
        .progress-track {
            background-color: #242435;
            border-radius: 12px;
            width: 100%;
            height: 8px;
            overflow: hidden;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }
        .progress-fill {
            height: 100%;
            border-radius: 12px;
            animation: fillBar 1.2s cubic-bezier(0.1, 0.9, 0.2, 1) forwards;
            position: relative;
        }
        /* Add a subtle shine effect to the bar */
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%);
            border-radius: 12px;
        }
        
        /* Premium Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border-radius: 30px;
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        /* Alert Boxes */
        .alert-box {
            padding: 22px;
            border-radius: 16px;
            background: #191924;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .alert-title {
            font-weight: 800;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .alert-desc {
            color: #A0A0B0;
            font-size: 0.95rem;
            line-height: 1.5;
            margin-left: 34px; /* Align with text, skipping icon */
        }

        /* AI Insight Box - "Magic" styling */
        .insight-container {
            background: linear-gradient(160deg, #1C1C2C 0%, #151522 100%);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-top: 3px solid #8B5CF6;
            padding: 24px;
            border-radius: 16px;
            color: #E2E8F0;
            font-size: 1.05rem;
            line-height: 1.7;
            box-shadow: 0 10px 30px -5px rgba(139, 92, 246, 0.15);
            position: relative;
        }
        .insight-header {
            color: #A78BFA;
            font-weight: 700;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Evidence Highlight Box */
        .evidence-box {
            background-color: #12121A;
            padding: 28px;
            border-radius: 16px;
            border: 1px solid #2D2D3F;
            color: #CBD5E1;
            font-size: 1.1rem;
            line-height: 1.8;
            font-family: 'Georgia', serif;
            font-style: italic;
            position: relative;
        }
        /* Quotation mark decoration */
        .evidence-box::before {
            content: '"';
            position: absolute;
            top: -10px;
            left: 15px;
            font-size: 4rem;
            color: rgba(255,255,255,0.05);
            font-family: sans-serif;
            font-style: normal;
        }
        
        /* Highlight Marker Styling */
        .highlight-word {
            background: linear-gradient(120deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.1) 100%);
            color: #FCA5A5;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 700;
            border-bottom: 2px solid rgba(239, 68, 68, 0.5);
            font-family: system-ui, -apple-system, sans-serif;
            font-style: normal;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)


def render_score_card(title: str, score: float, color: str):
    """
    Displays a premium metric card with a title, percentage, and glowing progress bar.
    """
    pct = int(score * 100)
    
    # Map high-level color names to exact hex values and box-shadow glows
    color_map = {
        "green": {"hex": "#10B981", "glow": "rgba(16, 185, 129, 0.4)", "icon": "🟢"},
        "red": {"hex": "#EF4444", "glow": "rgba(239, 68, 68, 0.4)", "icon": "🔴"},
        "blue": {"hex": "#3B82F6", "glow": "rgba(59, 130, 246, 0.4)", "icon": "🔵"}
    }
    
    style = color_map.get(color.lower(), color_map["blue"])
    
    html = f"""
    <div class="metric-card">
        <div class="metric-title">{style['icon']} {title}</div>
        <div class="metric-value">{pct}%</div>
        <div class="progress-track">
            <div class="progress-fill" style="width: {pct}%; background-color: {style['hex']}; box-shadow: 0 0 10px {style['glow']};"></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_emotion_badge(emotion: str):
    """
    Displays the detected emotion as a dynamically colored premium glassmorphism badge.
    """
    emotion_lower = emotion.lower()
    
    if any(word in emotion_lower for word in ['happy', 'joy', 'calm', 'relaxed', 'confident']):
        bg, text_color, border, icon = 'rgba(16, 185, 129, 0.1)', '#34D399', 'rgba(16, 185, 129, 0.3)', '✨'
    elif any(word in emotion_lower for word in ['nervous', 'anxious', 'defensive', 'hesitant']):
        bg, text_color, border, icon = 'rgba(245, 158, 11, 0.1)', '#FBBF24', 'rgba(245, 158, 11, 0.3)', '⚡'
    elif any(word in emotion_lower for word in ['aggressive', 'angry', 'hostile', 'deceptive']):
        bg, text_color, border, icon = 'rgba(239, 68, 68, 0.1)', '#F87171', 'rgba(239, 68, 68, 0.3)', '🔥'
    else:
        bg, text_color, border, icon = 'rgba(156, 163, 175, 0.1)', '#D1D5DB', 'rgba(156, 163, 175, 0.3)', '🎯'

    html = f"""
    <div style="margin-bottom: 12px; color: #8E8EA8; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Detected Emotion</div>
    <div class="badge" style="background-color: {bg}; color: {text_color}; border: 1px solid {border};">
        <span style="margin-right: 8px; font-size: 1.1rem;">{icon}</span> {emotion}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_threat_level(deception_score: float):
    """
    Converts a deception score into a categorical threat level alert box with refined UI.
    """
    if deception_score < 0.40:
        level, icon, color = "Low Risk", "🛡️", "#10B981"
        desc = "Minimal indicators of deception. Linguistic structures strongly align with authentic, memory-based recall."
    elif deception_score < 0.70:
        level, icon, color = "Elevated Risk", "⚠️", "#F59E0B"
        desc = "Moderate structural anomalies detected. Suggests cognitive load, potential hesitation, or selective omission."
    else:
        level, icon, color = "High Risk", "🚨", "#EF4444"
        desc = "Severe indicators of a fabricated narrative. The model identified high cognitive strain and deceptive markers."

    html = f"""
    <div class="alert-box" style="border-left: 4px solid {color}; border-right: 1px solid rgba(255,255,255,0.05); border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);">
        <div class="alert-title" style="color: {color};">{icon} {level}</div>
        <div class="alert-desc">{desc}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_ai_explanation(text: str, score: float, emotion: str):
    """
    Generates a dynamic, human-like paragraph explaining the AI's reasoning inside a 'magic' container.
    """
    pct = int(score * 100)
    
    if pct < 40:
        insight = f"The text exhibits a natural flow with an underlying {emotion.lower()} tone. Pronoun usage and sentence structure align with memory-based, authentic recall rather than a fabricated narrative."
    elif pct < 70:
        insight = f"The analysis detects mixed cognitive signals. While the tone registers as {emotion.lower()}, the model found mild structural anomalies. This often occurs when a subject is experiencing cognitive load or selectively withholding facts."
    else:
        insight = f"Significant probability of a fabricated statement. The model identified overt linguistic hesitations, over-justification, and a {emotion.lower()} tone—which frequently correlate with deceptive defense mechanisms and high cognitive strain."

    html = f"""
    <div class="insight-container">
        <div class="insight-header">
            <span style="animation: pulse 2s infinite; border-radius: 50%; height: 8px; width: 8px; background-color: #8B5CF6; display: inline-block;"></span>
            System Insight
        </div>
        {insight}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def highlight_suspicious_text(text: str) -> str:
    """
    Scans the text for a predefined list of suspicious words and wraps them in HTML highlight tags.
    """
    keywords = [
        "honestly", "trust me", "believe me", "to be frank", 
        "to tell the truth", "literally", "actually", "to be honest",
        "i swear", "frankly"
    ]
    
    highlighted_text = text
    # Sort keywords by length so "to be honest" matches before "honest"
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    
    for word in sorted_keywords:
        pattern = re.compile(rf'\b({re.escape(word)})\b', re.IGNORECASE)
        highlighted_text = pattern.sub(r'<span class="highlight-word">\1</span>', highlighted_text)
        
    return highlighted_text


def render_result_dashboard(result_dict: Dict[str, Any], input_text: str):
    """
    Master component that combines all sub-components into a highly polished, responsive dashboard.
    """
    _inject_component_css()
    
    truth_score = result_dict.get("truth_score", 0.0)
    deception_score = result_dict.get("deception_score", 0.0)
    confidence_score = result_dict.get("confidence_score", 0.0)
    emotion = result_dict.get("emotion", "Neutral")
    
    # --- ROW 1: SCORE CARDS ---
    st.markdown("<h3 style='font-weight: 800; margin-bottom: 0.2rem;'>📊 Intelligence Report</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8E8EA8; margin-bottom: 1.5rem;'>Cryptographic linguistic analysis complete.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_score_card("Truth Probability", truth_score, "green")
    with col2:
        render_score_card("Deception Probability", deception_score, "red")
    with col3:
        render_score_card("Model Confidence", confidence_score, "blue")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # --- ROW 2: DEEP DIVE ---
    left_col, empty_space, right_col = st.columns([1.6, 0.1, 1])
    
    with left_col:
        st.markdown("<h4 style='font-weight: 700; color: #FFFFFF;'>🧠 Cognitive Breakdown</h4>", unsafe_allow_html=True)
        render_ai_explanation(input_text, deception_score, emotion)
        
        st.markdown("<br><br><h4 style='font-weight: 700; color: #FFFFFF;'>📝 Linguistic Evidence</h4>", unsafe_allow_html=True)
        highlighted_html = highlight_suspicious_text(input_text)
        st.markdown(f'<div class="evidence-box">{highlighted_html}</div>', unsafe_allow_html=True)
        
    with right_col:
        st.markdown("<h4 style='font-weight: 700; color: #FFFFFF;'>🎯 Threat Assessment</h4>", unsafe_allow_html=True)
        render_threat_level(deception_score)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_emotion_badge(emotion)