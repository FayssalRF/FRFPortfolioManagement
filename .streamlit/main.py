import streamlit as st
from ui.styles import inject_brand_css
from tabs.dashboard import dashboard_tab
from tabs.customers import customers_tab
import streamlit as st

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Login")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Log ind", type="primary"):
            if (
                user == st.secrets["auth"]["username"]
                and pwd == st.secrets["auth"]["password"]
            ):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Forkert login")

        st.stop()

login()


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
