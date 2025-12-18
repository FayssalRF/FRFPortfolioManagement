import streamlit as st
from ui.styles import inject_brand_css
from tabs.dashboard import dashboard_tab
from tabs.customers import customers_tab

st.set_page_config(page_title="CS Portfolio", layout="wide")
inject_brand_css()

st.markdown('<h1 class="mover-title">Customer Success Portfolio</h1>', unsafe_allow_html=True)
st.markdown('<p class="mover-subtle">Overblik, sundhed, pipeline og geografi – i Mover brand.</p>', unsafe_allow_html=True)

c1, c2 = st.columns([1,1])
with c1:
    if st.button("Dashboard", type="primary", use_container_width=True):
        st.session_state["tab"] = "dash"
with c2:
    if st.button("Kunder", use_container_width=True):
        st.session_state["tab"] = "customers"

tab = st.session_state.get("tab", "dash")
st.divider()

if tab == "dash":
    dashboard_tab()
else:
    customers_tab()
