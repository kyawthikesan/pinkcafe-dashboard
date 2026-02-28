# dashboardfoodwastage.py
# Bristol Pink Café – Streamlit Dashboard (BLACKPINK styling + Manager/Staff roles + Sales entry + Predictions from uploaded CSVs)
#
# What you need in the project folder:
#   - dashboardfoodwastage.py  (this file)
#   - product_prices.csv       (teacher-provided prices; auto-template created if missing)
#
# Predictions page expects TWO CSV uploads:
#   1) Coffee CSV: "Pink CoffeeSales March - Oct 2025.csv"  (weird first-row product names)
#   2) Croissant CSV: "Pink CroissantSales March - Oct 2025.csv" (normal Date + Number Sold)

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# ---- ML imports (safe) ----
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor

    SKLEARN_OK = True
except Exception:
    LinearRegression = None
    RandomForestRegressor = None
    SKLEARN_OK = False


# ----------------------------
# Config / Paths
# ----------------------------
FORECAST_DAYS = 28
PRICE_FILE = Path("product_prices.csv")
SALES_LOG = Path("sales_entries.csv")

# Demo users (replace later with secrets/hashes if needed)
# username is case-insensitive
DEMO_USERS = {
    "manager": {"password": "manager123", "role": "manager"},
    "staff": {"password": "staff123", "role": "staff"},
}


# ----------------------------
# BLACKPINK Theme (higher contrast + more professional)
# ----------------------------
def inject_blackpink_theme() -> None:
    st.markdown(
        """
        <style>
        /* ---------- Blackpink Pro Palette ---------- */
        :root{
            --bp-bg: #06060A;
            --bp-bg-2: #0A0A10;

            --bp-surface: rgba(255,255,255,0.06);
            --bp-surface-2: rgba(255,255,255,0.09);

            --bp-border: rgba(255,105,180,0.22);
            --bp-border-strong: rgba(255,105,180,0.40);

            --bp-text: #F6F1F7;
            --bp-text-dim: rgba(246,241,247,0.78);
            --bp-text-mute: rgba(246,241,247,0.62);

            --bp-pink: #ff69b4;
            --bp-pink-2: #ff2d95;

            --bp-shadow: 0 14px 44px rgba(0,0,0,0.62);
            --bp-radius: 18px;
            --bp-radius-sm: 12px;
        }

        .stApp {
            background:
                radial-gradient(1000px 700px at 20% 0%, rgba(255,105,180,0.10) 0%, rgba(255,105,180,0.0) 62%),
                radial-gradient(1000px 700px at 80% 0%, rgba(255,45,149,0.08) 0%, rgba(255,45,149,0.0) 62%),
                linear-gradient(180deg, var(--bp-bg) 0%, #000 72%, #000 100%);
            color: var(--bp-text);
        }

        html, body, [class*="css"]  {
            color: var(--bp-text);
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
        }

        .block-container { padding-top: 1.1rem; padding-bottom: 2.6rem; }

        h1, h2, h3, h4 {
            color: var(--bp-pink) !important;
            letter-spacing: 0.2px;
        }
        p, li, label, .stMarkdown, .stCaption {
            color: var(--bp-text-dim) !important;
        }

        section[data-testid="stSidebar"]{
            background: linear-gradient(180deg, var(--bp-bg-2) 0%, #050508 100%);
            border-right: 1px solid var(--bp-border);
        }
        section[data-testid="stSidebar"] *{
            color: var(--bp-text) !important;
        }
        section[data-testid="stSidebar"] .stRadio label {
            color: var(--bp-text-dim) !important;
        }

        .bp-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.04) 100%);
            border: 1px solid var(--bp-border);
            border-radius: var(--bp-radius);
            padding: 22px;
            box-shadow: var(--bp-shadow);
            backdrop-filter: blur(10px);
        }

        .bp-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid rgba(255,105,180,0.38);
            background:
                linear-gradient(180deg, rgba(255,105,180,0.14) 0%, rgba(0,0,0,0.10) 100%);
            color: rgba(246,241,247,0.92);
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .bp-divider {
            height: 1px;
            background: rgba(255,105,180,0.18);
            margin: 14px 0;
        }

        .stButton > button,
        button[kind="primary"],
        button[kind="secondary"],
        div[data-testid="stForm"] button {
            background: linear-gradient(90deg, var(--bp-pink) 0%, var(--bp-pink-2) 100%) !important;
            color: #0A0A0F !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 14px !important;
            padding: 0.62rem 1.05rem !important;
            font-weight: 900 !important;
            letter-spacing: 0.2px !important;
            box-shadow: 0 10px 26px rgba(255,45,149,0.14) !important;
            transition: transform 120ms ease, filter 120ms ease !important;
        }

        .stButton > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        div[data-testid="stForm"] button:hover {
            filter: brightness(1.05) !important;
            transform: translateY(-1px) !important;
        }

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {
            background: rgba(10,10,15,0.72) !important;
            color: var(--bp-text) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: var(--bp-radius-sm) !important;
        }

        div[role="radiogroup"] label, .stCheckbox label{
            color: var(--bp-text-dim) !important;
        }

        div[data-testid="stAlert"]{
            border-radius: var(--bp-radius);
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(10,10,15,0.65);
            color: var(--bp-text) !important;
        }

        .stDataFrame, div[data-testid="stDataFrame"] {
            border-radius: var(--bp-radius);
            border: 1px solid rgba(255,255,255,0.10);
            overflow: hidden;
        }
        div[data-testid="stDataFrame"] * {
            color: var(--bp-text) !important;
        }
        div[data-testid="stDataFrame"] thead tr th {
            background: rgba(255,105,180,0.10) !important;
            border-bottom: 1px solid var(--bp-border) !important;
        }
        div[data-testid="stDataFrame"] tbody tr:hover td{
            background: rgba(255,105,180,0.06) !important;
        }

        a, a:visited { color: rgba(255,182,217,0.95) !important; }
        a:hover { color: var(--bp-pink) !important; }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_pink_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="bp-card">
            <div class="bp-badge">BLACKPINK • Bristol Pink Café</div>
            <h1 style="margin:0; line-height:1.1;">{title}</h1>
            <p style="margin:8px 0 0 0; color: rgba(246,241,247,0.72);">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


# ----------------------------
# Chart helpers
# ----------------------------
def moving_average(s: pd.Series, window: int = 7) -> pd.Series:
    s = s.sort_index()
    return s.rolling(window=window, min_periods=max(1, window // 2)).mean()


def friendly_kpi_help(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="bp-card" style="padding:16px; background: linear-gradient(180deg, rgba(255,105,180,0.10) 0%, rgba(255,255,255,0.05) 100%);">
            <div class="bp-badge">{title}</div>
            <div style="color: rgba(246,241,247,0.78); line-height:1.5;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def chart_section_title(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    st.caption(subtitle)
    st.write("")


def make_pred_band(pred: pd.Series, recent_actual: pd.Series) -> pd.DataFrame:
    """
    Friendly 'range' band using recent variability (NOT a statistical confidence interval).
    """
    recent = recent_actual.dropna().tail(21)
    spread = float(recent.std()) if len(recent) >= 5 else 0.0
    lower = (pred - spread).clip(lower=0)
    upper = (pred + spread).clip(lower=0)
    return pd.DataFrame({"predicted": pred, "lower": lower, "upper": upper})


# ----------------------------
# Auth (simple, demo)
# ----------------------------
def login_gate() -> bool:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None

    if st.session_state.logged_in:
        return True

    left, mid, right = st.columns([1.2, 1, 1.2])
    with mid:
        st.markdown('<div class="bp-card">', unsafe_allow_html=True)
        st.markdown('<div class="bp-badge">BLACKPINK • Café Portal</div>', unsafe_allow_html=True)
        st.markdown("## Login")

        with st.form("bp_login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="manager or staff")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Log in")

        if submit:
            u = (username or "").strip().lower()
            user = DEMO_USERS.get(u)
            if user and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = user["role"]
                st.success(f"Welcome, {st.session_state.role.title()}.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown('<div class="bp-divider"></div>', unsafe_allow_html=True)
        st.caption("Demo accounts (change later): manager/manager123 and staff/staff123")
        st.markdown("</div>", unsafe_allow_html=True)

    return False


def logout_button() -> None:
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()


# ----------------------------
# Price list + Sales log (CSV persistence)
# ----------------------------
def ensure_price_file_template() -> None:
    if PRICE_FILE.exists():
        return

    template = pd.DataFrame(
        {"product": ["Cappuccino", "Americano", "Croissant"], "unit_price": [3.50, 3.00, 2.20]}
    )
    template.to_csv(PRICE_FILE, index=False)


@st.cache_data
def load_price_map() -> Dict[str, float]:
    ensure_price_file_template()
    dfp = pd.read_csv(PRICE_FILE)
    dfp["product"] = dfp["product"].astype(str).str.strip()
    dfp["unit_price"] = pd.to_numeric(dfp["unit_price"], errors="coerce")
    dfp = dfp.dropna(subset=["product", "unit_price"])

    price_map = dict(zip(dfp["product"], dfp["unit_price"]))
    if not price_map:
        st.error("product_prices.csv has no valid rows. Please fill it with teacher prices.")
        st.stop()
    return price_map


def append_sale(row: dict) -> None:
    cols = ["date", "product", "qty", "unit_price", "staff_user", "created_at"]
    safe = {c: row.get(c) for c in cols}
    df = pd.DataFrame([safe], columns=cols)
    if SALES_LOG.exists():
        df.to_csv(SALES_LOG, mode="a", header=False, index=False)
    else:
        df.to_csv(SALES_LOG, index=False)


def load_sales_log() -> pd.DataFrame:
    cols = ["date", "product", "qty", "unit_price", "staff_user", "created_at"]
    if not SALES_LOG.exists():
        return pd.DataFrame(columns=cols + ["total"])

    df = pd.read_csv(SALES_LOG)
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
    df["staff_user"] = df["staff_user"].astype(str).str.strip().str.lower()
    df["product"] = df["product"].astype(str).str.strip()
    df["total"] = df["qty"] * df["unit_price"]
    return df


# ----------------------------
# CSV loaders + forecasting (UPLOADS)
# ----------------------------
def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_date_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, dayfirst=True, errors="coerce")


def load_coffee_weird_layout(uploaded_file) -> pd.DataFrame:
    df = pd.read_csv(uploaded_file)
    df = normalize_cols(df)

    if "Date" not in df.columns:
        raise ValueError("Coffee file must contain a 'Date' column (as in your file).")

    first_date = df.loc[0, "Date"] if len(df) > 0 else None
    has_unnamed = any(str(c).lower().startswith("unnamed") for c in df.columns)

    if pd.isna(first_date) and has_unnamed and len(df.columns) >= 3:
        sales_cols = [c for c in df.columns if c != "Date"]
        product_names = [str(df.loc[0, c]).strip() for c in sales_cols]

        df = df[["Date"] + sales_cols].copy()
        df.columns = ["Date"] + product_names
        df = df.iloc[1:].copy()

        df["Date"] = parse_date_series(df["Date"])
        df = df.dropna(subset=["Date"])

        for c in df.columns:
            if c != "Date":
                df[c] = pd.to_numeric(df[c], errors="coerce")

        long = df.melt(id_vars=["Date"], var_name="product", value_name="units_sold")
        long = long.dropna(subset=["units_sold"])
        long["product"] = long["product"].astype(str).str.strip()
        long = long.rename(columns={"Date": "date"})
        return long[["date", "product", "units_sold"]]

    lower_cols = [c.lower().strip() for c in df.columns]
    if "product" in lower_cols and any(x in lower_cols for x in ["number sold", "units_sold", "units sold", "sold"]):
        colmap = {}
        for c in df.columns:
            cl = c.lower().strip()
            if cl == "date":
                colmap[c] = "Date"
            elif cl == "product":
                colmap[c] = "Product"
            elif cl in ["number sold", "units_sold", "units sold", "sold"]:
                colmap[c] = "Number Sold"
        df = df.rename(columns=colmap)

        df["Date"] = parse_date_series(df["Date"])
        df["Number Sold"] = pd.to_numeric(df["Number Sold"], errors="coerce")
        df = df.dropna(subset=["Date"])

        out = df[["Date", "Product", "Number Sold"]].copy()
        out.columns = ["date", "product", "units_sold"]
        out["product"] = out["product"].astype(str).str.strip()
        return out

    raise ValueError("Coffee file format not recognised.")


def load_simple_product_file(uploaded_file, product_name: str) -> pd.DataFrame:
    df = pd.read_csv(uploaded_file)
    df = normalize_cols(df)

    date_col = None
    for cand in ["Date", "date", "DATE"]:
        if cand in df.columns:
            date_col = cand
            break
    if date_col is None:
        raise ValueError(f"{product_name} file must contain a Date column.")

    sold_col = None
    for cand in ["Number Sold", "number sold", "Units Sold", "units_sold", "Units", "Sold", "sold"]:
        if cand in df.columns:
            sold_col = cand
            break
    if sold_col is None:
        raise ValueError(f"{product_name} file must contain a Number Sold / Units Sold column.")

    df[date_col] = parse_date_series(df[date_col])
    df[sold_col] = pd.to_numeric(df[sold_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    out = df[[date_col, sold_col]].copy()
    out.columns = ["date", "units_sold"]
    out["product"] = product_name
    return out[["date", "product", "units_sold"]]


def simple_forecast(series: pd.Series, days: int = FORECAST_DAYS) -> pd.DataFrame:
    s = series.dropna()
    if len(s) < 2:
        future = np.repeat(float(s.iloc[-1]) if len(s) else 0.0, days)
        return pd.DataFrame({"predicted": future})

    window = min(14, max(3, len(s) // 5))
    base = s.rolling(window=window).mean().dropna()
    last = float(base.iloc[-1]) if len(base) else float(s.iloc[-1])

    n = min(21, len(s))
    y = s.iloc[-n:].values.astype(float)
    x = np.arange(len(y))
    slope = np.polyfit(x, y, 1)[0] if len(y) >= 2 else 0.0

    future = [max(0.0, last + slope * i) for i in range(1, days + 1)]
    return pd.DataFrame({"predicted": future})


def linear_regression_forecast(series: pd.Series, days: int = FORECAST_DAYS) -> Tuple[pd.DataFrame, dict]:
    if not SKLEARN_OK or LinearRegression is None:
        return simple_forecast(series, days), {"ok": False, "reason": "scikit-learn not installed"}

    s = series.dropna()
    if len(s) < 5:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough data (need ~5+ points)"}

    X = np.arange(len(s)).reshape(-1, 1)
    y = s.values.astype(float)

    model = LinearRegression()
    model.fit(X, y)
    r2 = float(model.score(X, y))

    X_future = np.arange(len(s), len(s) + days).reshape(-1, 1)
    y_future = np.clip(model.predict(X_future), 0, None)

    pred_df = pd.DataFrame({"predicted": y_future})
    info = {
        "ok": True,
        "type": "linear_regression",
        "slope_per_day": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "r2_train": r2,
    }
    return pred_df, info


def make_rf_features(series: pd.Series) -> pd.DataFrame:
    s = series.copy()
    s.index = pd.to_datetime(s.index)
    s = s.asfreq("D").fillna(0)

    df = pd.DataFrame({"y": s})
    for lag in [1, 2, 3, 7, 14]:
        df[f"lag_{lag}"] = df["y"].shift(lag)

    df["roll_mean_7"] = df["y"].shift(1).rolling(7).mean()
    df["roll_mean_14"] = df["y"].shift(1).rolling(14).mean()

    df["dow"] = df.index.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["day_of_month"] = df.index.day
    df["month"] = df.index.month
    return df.dropna()


def random_forest_forecast(series: pd.Series, days: int = FORECAST_DAYS) -> Tuple[pd.DataFrame, dict]:
    if not SKLEARN_OK or RandomForestRegressor is None:
        return simple_forecast(series, days), {"ok": False, "reason": "scikit-learn not installed"}

    s = series.dropna()
    if len(s) < 30:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough data (need ~30+ days)"}

    s = s.copy()
    s.index = pd.to_datetime(s.index)
    s = s.asfreq("D").fillna(0)

    df = make_rf_features(s)
    if len(df) < 20:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough feature rows after lags"}

    X = df.drop(columns=["y"])
    y = df["y"].astype(float)

    model = RandomForestRegressor(n_estimators=400, random_state=42, min_samples_leaf=2, n_jobs=-1)
    model.fit(X, y)
    r2 = float(model.score(X, y))

    current = s.copy()
    last_date = current.index.max()
    preds = []

    def get_val(d: pd.Timestamp) -> float:
        return float(current.loc[d]) if d in current.index else 0.0

    for i in range(1, days + 1):
        next_date = last_date + pd.Timedelta(days=i)
        prev_7 = current.loc[(next_date - pd.Timedelta(days=7)) : (next_date - pd.Timedelta(days=1))]
        prev_14 = current.loc[(next_date - pd.Timedelta(days=14)) : (next_date - pd.Timedelta(days=1))]

        row = {
            "lag_1": get_val(next_date - pd.Timedelta(days=1)),
            "lag_2": get_val(next_date - pd.Timedelta(days=2)),
            "lag_3": get_val(next_date - pd.Timedelta(days=3)),
            "lag_7": get_val(next_date - pd.Timedelta(days=7)),
            "lag_14": get_val(next_date - pd.Timedelta(days=14)),
            "roll_mean_7": float(prev_7.mean()) if len(prev_7) else 0.0,
            "roll_mean_14": float(prev_14.mean()) if len(prev_14) else 0.0,
            "dow": int(next_date.dayofweek),
            "is_weekend": int(next_date.dayofweek >= 5),
            "day_of_month": int(next_date.day),
            "month": int(next_date.month),
        }

        y_next = float(model.predict(pd.DataFrame([row]))[0])
        y_next = max(0.0, y_next)
        preds.append(y_next)
        current.loc[next_date] = y_next

    pred_df = pd.DataFrame({"predicted": np.array(preds, dtype=float)})
    info = {"ok": True, "type": "random_forest", "r2_train": r2}
    return pred_df, info


# ----------------------------
# Pages
# ----------------------------
def page_staff_record_sale() -> None:
    render_pink_header("Staff • Record Sales", "Enter sales. Unit price is fixed from the price list.")

    price_map = load_price_map()
    products = list(price_map.keys())

    st.info("Prices come from product_prices.csv. If you need to update prices, ask a manager.", icon=None)

    with st.form("sale_form", clear_on_submit=True):
        d = st.date_input("Date", value=date.today())

        # RADIO instead of selectbox
        product = st.radio("Product", products, index=0)

        unit_price = float(price_map[product])
        st.text_input("Unit price", value=f"£{unit_price:.2f}", disabled=True)

        qty = st.number_input("Quantity sold", min_value=1, step=1, value=1)
        submitted = st.form_submit_button("Save")

    if submitted:
        row = {
            "date": str(d),
            "product": product,
            "qty": int(qty),
            "unit_price": float(unit_price),
            "staff_user": str(st.session_state.username).strip().lower(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        append_sale(row)
        st.success("Saved.")
        st.rerun()

    st.write("")
    st.subheader("Recent entries")
    df = load_sales_log()
    mine = df[df["staff_user"] == str(st.session_state.username).strip().lower()].copy()
    if mine.empty:
        st.caption("No entries yet.")
    else:
        mine = mine.sort_values("created_at", ascending=False).head(20)
        show = mine[["date", "product", "qty", "unit_price", "total", "created_at"]].copy()
        show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.date.astype(str)
        show["unit_price"] = show["unit_price"].map(lambda x: f"£{float(x):.2f}")
        show["total"] = show["total"].map(lambda x: f"£{float(x):.2f}")
        st.dataframe(show, use_container_width=True)


def page_manager_sales_overview() -> None:
    render_pink_header("Manager • Sales Overview", "Totals, trends, and top products from staff-entered records.")

    df = load_sales_log()
    if df.empty or df["date"].isna().all():
        st.info("No sales recorded yet.")
        return

    df = df.dropna(subset=["date"]).copy()
    df["day"] = df["date"].dt.date

    c1, c2, c3 = st.columns(3)
    c1.metric("Total units", int(df["qty"].sum()))
    c2.metric("Total revenue", f"£{df['total'].sum():.2f}")
    c3.metric("Transactions", int(len(df)))

    st.write("")

    revenue_daily = df.groupby("day")["total"].sum().sort_index()
    rev_ma7 = moving_average(revenue_daily, 7)

    chart_section_title("Revenue by day", "Bars show revenue per day. The line shows the 7-day average.")
    st.bar_chart(pd.DataFrame({"Daily revenue": revenue_daily}))
    st.line_chart(pd.DataFrame({"7-day average": rev_ma7}))

    chart_section_title("Weekly revenue", "Total revenue grouped by week.")
    weekly_rev = df.groupby(df["date"].dt.to_period("W"))["total"].sum()
    weekly_rev.index = weekly_rev.index.astype(str)
    st.bar_chart(weekly_rev)

    st.write("")
    st.subheader("Units by day")
    units_daily = df.groupby("day")["qty"].sum().sort_index()
    units_ma7 = moving_average(units_daily, 7)
    st.bar_chart(pd.DataFrame({"Daily units": units_daily}))
    st.line_chart(pd.DataFrame({"7-day average": units_ma7}))

    st.subheader("Top products by revenue")
    by_prod = df.groupby("product")["total"].sum().sort_values(ascending=False)
    st.bar_chart(by_prod)


def page_manager_sales_records() -> None:
    render_pink_header("Manager • Sales Records", "Filter, review, and export the sales log.")

    df = load_sales_log()
    if df.empty:
        st.info("No sales recorded yet.")
        return

    df = df.dropna(subset=["date"]).copy()
    df["day"] = df["date"].dt.date

    products = sorted(df["product"].dropna().unique().tolist())
    staff_users = sorted(df["staff_user"].dropna().unique().tolist())

    with st.sidebar:
        st.markdown("### Filters (radios)")

        # RADIO instead of dropdowns
        f_product = st.radio("Product", ["(All)"] + products, index=0)
        f_staff = st.radio("Staff user", ["(All)"] + staff_users, index=0)

        dmin = df["day"].min()
        dmax = df["day"].max()
        d_from, d_to = st.date_input("Date range", value=(dmin, dmax))

    out = df.copy()
    if f_product != "(All)":
        out = out[out["product"] == f_product]
    if f_staff != "(All)":
        out = out[out["staff_user"] == f_staff]

    out = out[(out["day"] >= d_from) & (out["day"] <= d_to)]

    st.subheader("Records")
    show = out[["date", "product", "qty", "unit_price", "total", "staff_user", "created_at"]].copy()
    show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.date.astype(str)
    show["unit_price"] = show["unit_price"].map(lambda x: f"£{float(x):.2f}")
    show["total"] = show["total"].map(lambda x: f"£{float(x):.2f}")
    st.dataframe(show, use_container_width=True)

    st.write("")
    csv_bytes = out.drop(columns=["day"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered sales (CSV)",
        data=csv_bytes,
        file_name="sales_filtered.csv",
        mime="text/csv",
    )


def page_predictions_dashboard() -> None:
    render_pink_header("Predictions", "Upload café CSVs to view trends and generate a 4-week forecast.")

    st.markdown("### Upload files")
    coffee_file = st.file_uploader("Coffee Sales CSV", type=["csv"], key="coffee_upload")
    croissant_file = st.file_uploader("Croissant Sales CSV", type=["csv"], key="croissant_upload")

    mode = st.radio(
        "Prediction mode",
        ["AI (Heuristic)", "ML (Linear Regression)", "AI (Random Forest)"],
        horizontal=True,
    )
    st.caption("Linear Regression fits a straight line trend. Random Forest learns patterns from lag/weekday features.")

    if not coffee_file or not croissant_file:
        st.info("Upload both CSV files to continue.")
        return

    try:
        coffee_long = load_coffee_weird_layout(coffee_file)
        croissant_long = load_simple_product_file(croissant_file, "Croissant")
    except Exception as e:
        st.error(f"Error loading CSVs: {e}")
        return

    df_all = pd.concat([coffee_long, croissant_long], ignore_index=True)
    df_all["product"] = df_all["product"].astype(str).str.strip()
    df_all["units_sold"] = pd.to_numeric(df_all["units_sold"], errors="coerce").fillna(0)
    df_all = df_all.dropna(subset=["date"]).sort_values("date")

    with st.expander("Data preview"):
        st.write("Coffee (long format):")
        st.dataframe(coffee_long.head(10), use_container_width=True)
        st.write("Croissant (long format):")
        st.dataframe(croissant_long.head(10), use_container_width=True)
        st.write("Combined:")
        st.dataframe(df_all.head(10), use_container_width=True)

    st.subheader("Best selling products")
    totals = df_all.groupby("product")["units_sold"].sum().sort_values(ascending=False)
    top3 = totals.head(3)

    cols = st.columns(3)
    labels = ["Top 1", "Top 2", "Top 3"]
    for i in range(3):
        if i < len(top3):
            product = str(top3.index[i])
            units = int(top3.iloc[i])
            cols[i].metric(labels[i], product, f"{units:,} sold")
        else:
            cols[i].metric(labels[i], "-", "-")

    left, right = st.columns([3, 2])

    daily_total = df_all.groupby("date")["units_sold"].sum().sort_index()
    daily_total = daily_total.asfreq("D").fillna(0)
    daily_ma7 = moving_average(daily_total, 7)

    with left:
        chart_section_title("Daily total sales", "Bars show daily sales. The line shows the 7-day average.")
        daily_chart_df = pd.DataFrame({"Daily sales": daily_total, "7-day average": daily_ma7})
        st.bar_chart(daily_chart_df[["Daily sales"]])
        st.line_chart(daily_chart_df[["7-day average"]])

        friendly_kpi_help(
            "Reading the trend",
            "If the bars rise over time and the 7-day average rises, sales are increasing. "
            "If the 7-day average falls, sales are decreasing.",
        )

        chart_section_title("Sales by product", "Top 5 products by total units sold.")
        pivot = (
            df_all.pivot_table(index="date", columns="product", values="units_sold", aggfunc="sum")
            .fillna(0)
            .sort_index()
        )
        pivot = pivot.asfreq("D").fillna(0)

        top_products = pivot.sum().sort_values(ascending=False).head(5).index.tolist()
        if top_products:
            st.line_chart(pivot[top_products])
        else:
            st.info("No product data to chart.")

    with right:
        chart_section_title("Weekday pattern", "Average units sold by weekday.")
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_sales = (
            df_all.copy()
            .assign(weekday=df_all["date"].dt.day_name())
            .groupby("weekday")["units_sold"]
            .mean()
            .reindex(weekday_order)
            .fillna(0)
        )
        st.bar_chart(weekday_sales)

        st.write("")
        chart_section_title("Weekly target suggestion", "Based on the average of the last 14 days.")
        amount_to_sell = int(max(0, daily_total.tail(14).mean() * 7)) if len(daily_total) else 0
        st.markdown(f"### Suggested weekly target: **{amount_to_sell:,} units**")

    st.subheader("Forecast (next 4 weeks)")

    if mode == "AI (Heuristic)":
        pred_raw = simple_forecast(daily_total, days=FORECAST_DAYS)
        model_info = {"ok": True, "type": "heuristic"}
    elif mode == "ML (Linear Regression)":
        pred_raw, model_info = linear_regression_forecast(daily_total, days=FORECAST_DAYS)
    else:
        pred_raw, model_info = random_forest_forecast(daily_total, days=FORECAST_DAYS)

    last_date = daily_total.index.max()
    future_index = pd.date_range(last_date + pd.Timedelta(days=1), periods=FORECAST_DAYS, freq="D")

    pred_series = pd.Series(pred_raw["predicted"].values, index=future_index)
    band_df = make_pred_band(pred_series, daily_total)

    st.caption("Predicted daily sales with a variation band based on recent volatility.")
    st.line_chart(band_df[["predicted", "lower", "upper"]])

    with st.expander("Forecast details"):
        st.write(model_info)

    out = band_df.reset_index().rename(columns={"index": "date"})
    csv_bytes = out.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download 4-week forecast (CSV)",
        data=csv_bytes,
        file_name="prediction_next_4_weeks.csv",
        mime="text/csv",
    )


# ----------------------------
# App start
# ----------------------------
st.set_page_config(page_title="Bristol Pink Café Dashboard", layout="wide")
inject_blackpink_theme()

if not login_gate():
    st.stop()

with st.sidebar:
    st.markdown("### Session")
    st.write(f"User: **{st.session_state.username}**")
    st.write(f"Role: **{st.session_state.role}**")
    logout_button()
    st.markdown("---")

    if st.session_state.role == "manager":
        page = st.radio("Navigation", ["Sales Overview", "Sales Records", "Predictions"], index=0)
    else:
        page = st.radio("Navigation", ["Record Sale", "Predictions"], index=0)

if st.session_state.role == "manager" and page == "Sales Overview":
    page_manager_sales_overview()
elif st.session_state.role == "manager" and page == "Sales Records":
    page_manager_sales_records()
elif st.session_state.role == "staff" and page == "Record Sale":
    page_staff_record_sale()
else:
    page_predictions_dashboard()

if not PRICE_FILE.exists():
    st.warning("product_prices.csv was not found and a template should have been created. Please check your folder.")