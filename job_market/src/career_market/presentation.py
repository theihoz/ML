"""Shared visual treatment for the local demo."""

import streamlit as st


def apply_theme():
    st.markdown(
        """
    <style>
    .stApp {background: #f6f8fc;}
    .stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,.stApp summary {color: #15253e;}
    [data-testid="stCaptionContainer"] p {color: #62748b;}
    [data-testid="stSidebar"] a {color: #20314b;}
    [data-testid="stSidebar"] {background: #fff; border-right: 1px solid #e5eaf1;}
    .block-container {max-width: 1160px; padding-top: 4rem; padding-bottom: 3rem;}
    h1 {letter-spacing: -.035em; color: #15253e; font-size: 2.5rem;}
    h2,h3 {color: #20314b;}
    [data-testid="stVerticalBlockBorderWrapper"] {background: white; border-radius: 16px;}
    [data-testid="stMetricValue"] {color: #2563eb;}
    button[kind="primary"],button[kind="primaryFormSubmit"] {background: #2563eb; border-color: #2563eb; border-radius: 9px;}
    button[kind="primary"] p,button[kind="primaryFormSubmit"] p {color: white !important;}
    [data-testid="stForm"] {border: 0; padding: 0;}
    [class*="st-key-overview_"] {background: white; border-radius: 14px; box-shadow: 0 3px 18px rgba(31, 49, 80, .035);}
    [class*="st-key-overview_chart_"] h3 {font-size: 1.15rem;}
    .st-key-overview_kpi_tech h3 {font-size: 1.2rem;}
    </style>
    """,
        unsafe_allow_html=True,
    )
