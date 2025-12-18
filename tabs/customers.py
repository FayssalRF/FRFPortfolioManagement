import streamlit as st
import pandas as pd
from datetime import date, datetime
from uuid import uuid4
from streamlit_gsheets import GSheetsConnection

# Sheet tab (case-sensitive)
SHEET_WORKSHEET = "Customers"

# Vi gemmer et stabilt ID pr. kunde, så redigering altid rammer korrekt række
COLUMNS = [
    "CustomerId",
    "CustomerName",
    "CVR",
    "CommercialContact",
    "AdminContact",
    "ForecastYearlyRevenue",
    "ActualRevenueToDate",
    "AccountCreatedDate",
    "FirstTripDate",
    "UpdatedAt",
]

def _get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=COLUMNS)

    df = df.dropna(how="all").copy()

    # Sikr alle kolonner
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""

    # Typer
    df["ForecastYearlyRevenue"] = pd.to_numeric(df["ForecastYearlyRevenue"], errors="coerce").fillna(0.0)
    df["ActualRevenueToDate"] = pd.to_numeric(df["ActualRevenueToDate"], errors="coerce").fillna(0.0)

    df["AccountCreatedDate"] = pd.to_datetime(df["AccountCreatedDate"], errors="coerce")
    df["FirstTripDate"] = pd.to_datetime(df["FirstTripDate"], errors="coerce")

    # Udfyld manglende ID’er
    missing_id = df["CustomerId"].astype(str).str.strip().eq("") | df["CustomerId"].isna()
    if missing_id.any():
        df.loc[missing_id, "CustomerId"] = [str(uuid4()) for _ in range(missing_id.sum())]

    # UpdatedAt som tekst
    if "UpdatedAt" in df.columns:
        df["UpdatedAt"] = df["UpdatedAt"].astype(str)

    return df[COLUMNS].copy()

def _load_customers() -> pd.DataFrame:
    conn = _get_conn()
    df = conn.read(worksheet=SHEET_WORKSHEET, ttl=0)
    return _normalize_df(df)

def _save_customers(df: pd.DataFrame) -> None:
    # Gem datoer som ISO-strenge (stabilt i Google Sheets)
    out = df.copy()
    out["AccountCreatedDate"] = pd.to_datetime(out["AccountCreatedDate"], errors="coerce").dt.date.astype(str)
    out["FirstTripDate"] = pd.to_datetime(out["FirstTripDate"], errors="coerce").dt.date.astype(str)

    conn = _get_conn()
    # VIGTIGT: write() overskriver arket med hele datasættet (enkelt + stabilt)
    conn.write(out, worksheet=SHEET_WORKSHEET, index=False)

def _card_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="mover-card" style="margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
            <div>
              <div class="mover-title" style="font-size:16px; margin-bottom:4px;">{title}</div>
              <div class="mover-subtle" style="font-size:13px;">{subtitle}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def customers_tab():
    st.markdown("### Kunder")

    # Load én gang pr. session (men altid fra sheet når vi rerunner efter save)
    if "customers_df" not in st.session_state:
        st.session_state.customers_df = _load_customers()

    df = st.session_state.customers_df.copy()

    # ---------- Add new customer ----------
    with st.expander("➕ Tilføj ny kunde", expanded=False):
        with st.form("add_customer_form", clear_on_submit=True):
            name = st.text_input("Kundenavn*")
            cvr = st.text_input("CVR nr (optional)")
            comm = st.text_input("Kommerciel kontaktperson*")
            admin = st.text_input("Administrativ kontaktperson*")

            col1, col2 = st.columns(2)
            with col1:
                forecast = st.number_input("Forecaste yearly revenue", min_value=0.0, step=1000.0)
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
                    "CustomerId": str(uuid4()),
                    "CustomerName": name.strip(),
                    "CVR": cvr.strip() if cvr else "",
                    "CommercialContact": comm.strip(),
                    "AdminContact": admin.strip(),
                    "ForecastYearlyRevenue": float(forecast),
                    "ActualRevenueToDate": float(actual),
                    "AccountCreatedDate": pd.to_datetime(created),
                    "FirstTripDate": pd.to_datetime(first_trip),
                    "UpdatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                _save_customers(df)
                st.session_state.customers_df = _load_customers()
                st.success("Kunde tilføjet og gemt")
                st.rerun()

    # ---------- Filters ----------
    left, right = st.columns([0.6, 0.4])
    with left:
        q = st.text_input("Søg (kundenavn / kontakt / CVR)")
    with right:
        sort_by = st.selectbox("Sorter", ["CustomerName", "ForecastYearlyRevenue", "ActualRevenueToDate"], index=0)

    view = df.copy()
    if q.strip():
        s = q.strip().lower()
        mask = (
            view["CustomerName"].astype(str).str.lower().str.contains(s, na=False)
            | view["CVR"].astype(str).str.lower().str.contains(s, na=False)
            | view["CommercialContact"].astype(str).str.lower().str.contains(s, na=False)
            | view["AdminContact"].astype(str).str.lower().str.contains(s, na=False)
        )
        view = view[mask]

    view = view.sort_values(by=sort_by, ascending=True if sort_by == "CustomerName" else False)

    # ---------- Cards (Apple-ish) ----------
    if len(view) == 0:
        st.info("Ingen kunder endnu (eller intet match på søgning).")
        return

    # Edit state
    if "edit_customer_id" not in st.session_state:
        st.session_state.edit_customer_id = None

    # Grid: 2 cards per row
    rows = list(view.to_dict(orient="records"))
    for i in range(0, len(rows), 2):
        cols = st.columns(2, gap="large")
        for j in range(2):
            if i + j >= len(rows):
                continue
            r = rows[i + j]
            with cols[j]:
                title = r["CustomerName"]
                subtitle = f"Forecast: {int(r['ForecastYearlyRevenue']):,} | Actual: {int(r['ActualRevenueToDate']):,}".replace(",", ".")
                _card_header(title, subtitle)

                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("Redigér", key=f"edit_{r['CustomerId']}", use_container_width=True):
                        st.session_state.edit_customer_id = r["CustomerId"]
                with c2:
                    if st.button("Slet", key=f"del_{r['CustomerId']}", use_container_width=True):
                        df2 = df[df["CustomerId"] != r["CustomerId"]].copy()
                        _save_customers(df2)
                        st.session_state.customers_df = _load_customers()
                        st.success("Kunde slettet")
                        st.rerun()

                # Edit panel (kun for valgt kunde)
                if st.session_state.edit_customer_id == r["CustomerId"]:
                    with st.expander("✏️ Redigér kunde", expanded=True):
                        with st.form(f"edit_form_{r['CustomerId']}"):
                            name = st.text_input("Kundenavn*", value=str(r["CustomerName"]))
                            cvr = st.text_input("CVR nr (optional)", value=str(r["CVR"] if r["CVR"] is not None else ""))
                            comm = st.text_input("Kommerciel kontaktperson*", value=str(r["CommercialContact"]))
                            admin = st.text_input("Administrativ kontaktperson*", value=str(r["AdminContact"]))

                            col1, col2 = st.columns(2)
                            with col1:
                                forecast = st.number_input(
                                    "Forecaste yearly revenue",
                                    min_value=0.0,
                                    step=1000.0,
                                    value=float(r["ForecastYearlyRevenue"] or 0.0),
                                )
                            with col2:
                                actual = st.number_input(
                                    "Actual revenue d.d.",
                                    min_value=0.0,
                                    step=1000.0,
                                    value=float(r["ActualRevenueToDate"] or 0.0),
                                )

                            # Datoer
                            created_val = pd.to_datetime(r["AccountCreatedDate"], errors="coerce")
                            first_val = pd.to_datetime(r["FirstTripDate"], errors="coerce")
                            created_date = st.date_input(
                                "Dato for oprettelse af konto",
                                value=(created_val.date() if pd.notna(created_val) else date.today()),
                                key=f"created_{r['CustomerId']}",
                            )
                            first_trip_date = st.date_input(
                                "Dato for første tur",
                                value=(first_val.date() if pd.notna(first_val) else date.today()),
                                key=f"first_{r['CustomerId']}",
                            )

                            save = st.form_submit_button("Gem ændringer", type="primary")
                            cancel = st.form_submit_button("Annullér")

                            if cancel:
                                st.session_state.edit_customer_id = None
                                st.rerun()

                            if save:
                                if not name.strip() or not comm.strip() or not admin.strip():
                                    st.error("Udfyld felter markeret med *")
                                    st.stop()

                                df2 = df.copy()
                                idx = df2.index[df2["CustomerId"] == r["CustomerId"]]
                                if len(idx) != 1:
                                    st.error("Kunne ikke finde kunden (ID mismatch).")
                                    st.stop()

                                k = idx[0]
                                df2.at[k, "CustomerName"] = name.strip()
                                df2.at[k, "CVR"] = cvr.strip() if cvr else ""
                                df2.at[k, "CommercialContact"] = comm.strip()
                                df2.at[k, "AdminContact"] = admin.strip()
                                df2.at[k, "ForecastYearlyRevenue"] = float(forecast)
                                df2.at[k, "ActualRevenueToDate"] = float(actual)
                                df2.at[k, "AccountCreatedDate"] = pd.to_datetime(created_date)
                                df2.at[k, "FirstTripDate"] = pd.to_datetime(first_trip_date)
                                df2.at[k, "UpdatedAt"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

                                _save_customers(df2)
                                st.session_state.customers_df = _load_customers()
                                st.session_state.edit_customer_id = None
                                st.success("Ændringer gemt")
                                st.rerun()
