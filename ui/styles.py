import streamlit as st

def inject_brand_css():
    st.markdown("""
    <style>
      :root{
        --midnight:#01293D;
        --daylight:#003F63;
        --daylight40:#A3B2C1;
        --teal:#91D8C8;
        --lightblue:#D7F3F9;
        --grey:#F7F8F9;
        --radius:18px;
      }

      /* Mere luft */
      .block-container { padding-top: 2rem; padding-bottom: 2.5rem; max-width: 1200px; }

      /* Apple-ish cards */
      .mover-card {
        background: #fff;
        border: 1px solid rgba(1,41,61,0.08);
        border-radius: var(--radius);
        padding: 16px 18px;
        box-shadow: 0 6px 22px rgba(1,41,61,0.06);
      }

      .mover-title { color: var(--midnight); font-weight: 700; letter-spacing: -0.02em; }
      .mover-subtle { color: rgba(1,41,61,0.65); }

      /* Knapper (runde, moderne) */
      .stButton>button {
        border-radius: 999px !important;
        padding: 0.6rem 1.0rem !important;
        border: 1px solid rgba(1,41,61,0.18) !important;
      }

      /* Primary button-look (solid) */
      .stButton>button[kind="primary"]{
        background: var(--midnight) !important;
        color: white !important;
        border: 1px solid transparent !important;
      }
      .stButton>button[kind="primary"]:hover{
        background: var(--daylight) !important;
      }

      /* Inputs afrundet */
      .stTextInput input, .stSelectbox div, .stMultiSelect div, .stDateInput input {
        border-radius: 12px !important;
      }

      /* “Metric cards” */
      div[data-testid="stMetric"]{
        background: #fff;
        border: 1px solid rgba(1,41,61,0.08);
        border-radius: var(--radius);
        padding: 14px 16px;
        box-shadow: 0 6px 22px rgba(1,41,61,0.05);
      }
    </style>
    """, unsafe_allow_html=True)
