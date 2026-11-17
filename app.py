import streamlit as st
from pathlib import Path
from database import init_db

st.set_page_config(page_title="FINORA AI", page_icon="💗", layout="wide", initial_sidebar_state="expanded")
init_db()

css = Path(__file__).parent / "assets" / "style.css"
if css.exists():
    st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

PAGES = {
    "Overview": [
        ("Executive Financial Dashboard", "modules.dashboard"),
        ("Custom Analysis", "modules.custom_analysis"),
    ],
    "Financial Analysis": [
        ("Financial Statement Analysis", "modules.financial_analysis"),
        ("Financial Ratio Analysis", "modules.ratio_analysis"),
        ("Budget vs Actual Analysis", "modules.budget_analysis"),
        ("Cash Flow Analysis", "modules.cashflow_analysis"),
        ("Financial Forecasting", "modules.forecasting"),
    ],
    "Audit & Risk": [
        ("Automated Financial Audit", "modules.automated_audit"),
        ("Audit Risk Assessment", "modules.risk_assessment"),
        ("Document & Evidence Checking", "modules.evidence_checking"),
        ("AI Audit Report Generator", "modules.report_generator"),
    ],
    "AI & Reports": [
        ("FINORA AI Assistant", "modules.ai_assistant"),
        ("Report Center & Export", "modules.report_center"),
    ],
}

st.sidebar.markdown(
    '<div style="padding:12px 4px 18px 4px;">'
    '<div style="font-size:30px;font-weight:800;color:#FF5C8B;letter-spacing:1px;">FINORA AI</div>'
    '<div style="font-size:11px;color:#80616D;">FINANCIAL ANALYSIS & AUDIT INTELLIGENCE</div></div>',
    unsafe_allow_html=True
)
all_pages = [(group, title, module) for group, items in PAGES.items() for title, module in items]
labels = [f"{g}  /  {t}" for g,t,m in all_pages]
selected_label = st.sidebar.radio("NAVIGATION", labels, index=0)
selected = next(item for item in all_pages if f"{item[0]}  /  {item[1]}" == selected_label)

st.sidebar.divider()
st.sidebar.caption("FINORA Signature Pink")
st.sidebar.markdown('<span style="color:#FF5C8B;font-weight:700;">●</span> #FF5C8B &nbsp; <span style="color:#D9C1B9;">●</span> Cream', unsafe_allow_html=True)
st.sidebar.caption("AI responses require a Gemini API key.")

st.markdown(
    '<div class="finora-hero"><h1>FINORA AI</h1>'
    '<div>Financial Analysis & Audit Intelligence</div>'
    '<div style="font-size:13px;margin-top:6px;opacity:.95;">Smart Financial Report Analysis, Automated Audit & AI-Powered Insights</div></div>',
    unsafe_allow_html=True
)

import importlib
module = importlib.import_module(selected[2])
module.render()
