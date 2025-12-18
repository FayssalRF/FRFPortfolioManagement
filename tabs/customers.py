import streamlit as st
import pandas as pd
from io import BytesIO
import pydeck as pdk
from datetime import date
from streamlit_gsheets import GSheetsConnection

# Kolonner til kundedata
COLUMNS = [
    "CustomerName",
    "CVR",
    "CommercialContact",
    "AdminContact",
    "ForecastYearlyRevenue",
    "ActualRevenueToDate",
    "AccountCreatedDate",
    "FirstTripDate",
]

SHEET_WORKSHEET = "Customers"  # matcher worksheet i secrets (kan ændres)

def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Customers")
    return output.getvalue()

def _get_conn():
    # Bruger Streamlit secrets: [connections.gsheets]
    return st.connection("gsheets", type=GSheetsConnection)

def _load_customers_from_sheet() -> pd.DataFrame:
    conn = _get_conn()
    df = conn.read(worksheet=SHEET_WORKSHEET, ttl=0)
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=COLUMNS)
    df = df.dropna(how="all").copy()

    # Sikr kolonner
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""

    # Ryd op / typer
    df["ForecastYearlyRevenue"] = pd.to_numeric(df["ForecastYearlyRevenue"], errors="coerce").fillna(0.0)
    df["ActualRevenueToDate"] = pd.to_numeric(df["ActualRevenueToDate"], errors="coerce").fillna(0.0)
    df["AccountCreatedDate"] = pd.to_datetime(df["AccountCreatedDate"], errors="coerce")
    df["FirstTripDate"] = pd.to_datetime(df["FirstTripDate"], errors="coerce")

    return df[COLUMNS].copy()

def _save_customers_to_sheet(df: pd.DataFrame) -> None:
    conn = _get_conn()
    # update() er måden at skrive tilbage til sheet på i GSheetsConnection-eksemplerne. :contentReference[oaicite:3]{index=3}
    conn.update(worksheet=SHEET_WORKSHEET, data=df)

def customers_tab():
    st.markdown("### Kunder")

    # --- Load fra Google Sheet (persist) ---
    if "customers_df" not in st.session_state:
        try:
            st.session_state.customers_df = _load_customers_from_sheet()
        except Exception:
            # Fallback: app må ikke crashe hvis Sheets ikke er sat op endnu
            st.session_state.customers_df = pd.DataFrame(columns=COLUMNS)

    df = st.session_state.customers_df.copy()

    # --- Tilføj ny kunde ---
    with st.expander("➕ Tilføj ny kunde", expanded=False):
        with st.form("add_customer_form", clear_on_submit=True):
            name = st.text_input("Kundenavn*")
            cvr = st.text_input("CVR nr (optional)")
            comm = st.text_input("Kommerciel kontaktperson*")
            admin = st.text_input("Administrativ kontaktperson*")

            col1, col2 = st.columns(2)
            with col1:
                forecast = st.number_input("Forecast yearly revenue", min_value=0.0, step=1000.0)
            with col2:
                actual = st.number_input("Actual revenue d.d.", min_value=0.0, step=1000.0)

            col3, col4 = st.columns(2)
            with col3:
                created = st.date_input("Dato for oprettelse af konto", value=date.today())
            with col4:
                first_trip = st.date_input("Dato for første tur", value=date.today())

            submitted = st.form_submit_button("Gem kunde", type="primary")

            if submitted:
                if not name.strip() or not comm.strip() or not admin.strip():
                    st.error("Udfyld felter markeret med *")
                    st.stop()

                new_row = {
                    "CustomerName": name.strip(),
                    "CVR": cvr.strip() if cvr else "",
                    "CommercialContact": comm.strip(),
                    "AdminContact": admin.strip(),
                    "ForecastYearlyRevenue": float(forecast),
                    "ActualRevenueToDate": float(actual),
                    "AccountCreatedDate": pd.to_datetime(created),
                    "FirstTripDate": pd.to_datetime(first_trip),
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                # Gem til Google Sheet (persist)
                try:
                    _save_customers_to_sheet(df)
                    st.cache_data.clear()
                    st.success("Kunde tilføjet og gemt permanent")
                except Exception as e:
                    st.error("Kunne ikke gemme til Google Sheet. Se fejlen nedenfor:")
                    st.exception(e)
                    st.stop()

                st.session_state.customers_df = df
                st.rerun()

    # --- Vis tabel ---
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Download Excel ---
    st.download_button(
        "⬇️ Download kunder (Excel)",
        data=_to_excel_bytes(df),
        file_name="customers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.divider()

    # --- Kort (ingen Mapbox token; vises kun hvis lat/lon findes) ---
    if {"lat", "lon"}.issubset(set(df.columns)) and len(df.dropna(subset=["lat", "lon"])) > 0:
        view = df.dropna(subset=["lat", "lon"]).copy()

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=view,
            get_position='[lon, lat]',
            get_radius=2500,
            pickable=True,
            auto_highlight=True,
        )

        deck = pdk.Deck(
            initial_view_state=pdk.ViewState(latitude=55.9, longitude=11.6, zoom=6),
            layers=[layer],
            tooltip={"text": "{CustomerName}\nForecast: {ForecastYearlyRevenue}\nActual: {ActualRevenueToDate}"},
        )
        st.pydeck_chart(deck, use_container_width=True)
    else:
        st.info("Kort vises, når kunder har lat/lon (vi kan tilføje adresse→koordinater som næste step).")
