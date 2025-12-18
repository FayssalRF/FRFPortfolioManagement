import streamlit as st
import pandas as pd

def dashboard_tab():
    # Demo-data (skift ud med jeres rigtige data)
    df = pd.DataFrame([
        {"Customer":"Acme A/S","CSM":"You","Health":"Green","MRR":42000,"City":"København"},
        {"Customer":"Nordic ApS","CSM":"You","Health":"Yellow","MRR":18000,"City":"Aarhus"},
        {"Customer":"Retail X","CSM":"You","Health":"Red","MRR":9000,"City":"Odense"},
    ])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Kunder", len(df))
    k2.metric("MRR (sum)", f"{df['MRR'].sum():,}".replace(",", "."))
    k3.metric("At-risk", int((df["Health"]=="Red").sum()))
    k4.metric("Needs attention", int((df["Health"].isin(["Red","Yellow"])).sum()))

    st.markdown('<div class="mover-card"><h3 class="mover-title" style="margin:0;">Portfolio oversigt</h3></div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
