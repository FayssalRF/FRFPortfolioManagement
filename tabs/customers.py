import streamlit as st
import pandas as pd
import pydeck as pdk

def customers_tab():
    # Demo-data (indsæt jeres rigtige kolonner)
    df = pd.DataFrame([
        {"Customer":"Acme A/S","MRR":42000,"Health":"Green","lat":55.6761,"lon":12.5683},
        {"Customer":"Nordic ApS","MRR":18000,"Health":"Yellow","lat":56.1629,"lon":10.2039},
        {"Customer":"Retail X","MRR":9000,"Health":"Red","lat":55.4038,"lon":10.4024},
    ])

    left, right = st.columns([0.46, 0.54], gap="large")

    with left:
        st.markdown('<div class="mover-card"><h3 class="mover-title" style="margin:0;">Kundekort</h3><p class="mover-subtle" style="margin:6px 0 0 0;">Klik og filtrér porteføljen.</p></div>', unsafe_allow_html=True)
        st.write("")

        health = st.multiselect("Health", sorted(df["Health"].unique().tolist()), default=sorted(df["Health"].unique().tolist()))
        view = df[df["Health"].isin(health)].copy()

        for _, r in view.iterrows():
            st.markdown(f"""
            <div class="mover-card" style="margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div class="mover-title" style="font-size:16px;">{r['Customer']}</div>
                  <div class="mover-subtle">Health: <b>{r['Health']}</b></div>
                </div>
                <div style="text-align:right;">
                  <div class="mover-subtle">MRR</div>
                  <div class="mover-title" style="font-size:16px;">{int(r['MRR']):,}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="mover-card"><h3 class="mover-title" style="margin:0;">Kort</h3><p class="mover-subtle" style="margin:6px 0 0 0;">Geografisk overblik over kunder.</p></div>', unsafe_allow_html=True)
        st.write("")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=view,
            get_position='[lon, lat]',
            get_radius=2500,
            pickable=True,
            auto_highlight=True,
        )

        deck = pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v10",
            initial_view_state=pdk.ViewState(latitude=55.9, longitude=11.6, zoom=6),
            layers=[layer],
            tooltip={"text": "{Customer}\nMRR: {MRR}\nHealth: {Health}"},
        )
        st.pydeck_chart(deck, use_container_width=True)
