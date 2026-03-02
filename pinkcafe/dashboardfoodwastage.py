# dashboardfoodwastage.py
# Bristol Pink Café – Streamlit Dashboard (BLACKPINK styling + Admin/Manager/Staff roles + Sales entry + Predictions from uploaded CSVs)

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Dict, Tuple
import hashlib

import numpy as np
import pandas as pd
import streamlit as st

# ---- ML imports (safe) ----
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

    SKLEARN_OK = True
except Exception:
    LinearRegression = None
    RandomForestRegressor = None
    GradientBoostingRegressor = None
    SKLEARN_OK = False


# ----------------------------
# Config / Paths
# ----------------------------
PRICE_FILE = Path("product_prices.csv")
SALES_LOG = Path("sales_entries.csv")
USERS_FILE = Path("users.csv")

st.set_page_config(page_title="Bristol Pink Café Dashboard", layout="wide")

st.markdown(
    """
    <style>
      /* Make the very top header bar transparent / gone */
      [data-testid="stHeader"] {
        background: rgba(0,0,0,0) !important;
        height: 0px !important;
      }

      /* Remove the default top padding/margin Streamlit adds */
      .block-container {
        padding-top: 0rem !important;
      }

      /* Ensure the app background is dark all the way to the top */
      [data-testid="stAppViewContainer"],
      [data-testid="stApp"] {
        background: #000 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# BLACKPINK Theme (higher contrast + more professional)
# ----------------------------
def inject_blackpink_theme() -> None:
    st.markdown(
        """
        <style>
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
# Model evaluation (NEW)
# ----------------------------
def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.where(y_true == 0, np.nan, y_true)
    mape = np.nanmean(np.abs((y_true - y_pred) / denom)) * 100.0
    return float(mape) if np.isfinite(mape) else float("nan")


def evaluate_models_time_holdout(
    daily_total: pd.Series,
    holdout_days: int = 14,
    modes: list[str] | None = None,
) -> Tuple[pd.DataFrame, str]:
    """
    Time-based evaluation:
      - train on all but the last `holdout_days`
      - predict the next `holdout_days`
      - compute MAE / RMSE / MAPE on the holdout period

    Returns:
      (metrics_df, best_mode_by_rmse)
    """
    if modes is None:
        modes = ["AI (Heuristic)", "ML (Linear Regression)", "AI (Random Forest)", "ML (Gradient Boosting)"]

    s = daily_total.copy().sort_index()
    s = s.asfreq("D").fillna(0)

    if len(s) < (holdout_days + 10):
        # not enough to evaluate reliably
        cols = ["MAE", "RMSE", "MAPE_%", "Notes"]
        df = pd.DataFrame(index=modes, columns=cols)
        df["Notes"] = f"Not enough data for holdout ({holdout_days}d). Need ~{holdout_days+10}+ days."
        return df.reset_index(names="Model"), ""

    train = s.iloc[:-holdout_days]
    test = s.iloc[-holdout_days:]

    rows = []
    for m in modes:
        pred_s, info = forecast_series_for_mode(train, holdout_days, m)
        # align prediction to test index
        pred_s = pred_s.reindex(test.index).fillna(0)

        y_true = test.values.astype(float)
        y_pred = pred_s.values.astype(float)

        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        mape = _safe_mape(y_true, y_pred)

        note = ""
        if isinstance(info, dict) and not info.get("ok", True):
            note = str(info.get("reason", ""))

        rows.append(
            {
                "Model": m,
                "MAE": mae,
                "RMSE": rmse,
                "MAPE_%": mape,
                "Notes": note,
            }
        )

    metrics = pd.DataFrame(rows).sort_values("RMSE", ascending=True).reset_index(drop=True)
    best_mode = str(metrics.iloc[0]["Model"]) if not metrics.empty else ""
    return metrics, best_mode


# ----------------------------
# Users DB (CSV) + Password hashing
# ----------------------------
def _pw_hash(password: str, salt: str) -> str:
    """
    Hash password using PBKDF2-HMAC-SHA256.
    Stored format: pbkdf2_sha256$iterations$salt$hash
    """
    password_b = (password or "").encode("utf-8")
    salt_b = (salt or "").encode("utf-8")
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password_b, salt_b, iterations)
    return f"pbkdf2_sha256${iterations}${salt}${dk.hex()}"


def _pw_verify(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, hx = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters)
        test = hashlib.pbkdf2_hmac(
            "sha256",
            (password or "").encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        return test == hx
    except Exception:
        return False


def ensure_users_file() -> None:
    """
    Creates users.csv with default accounts if missing.
    CHANGE the default admin password immediately.
    """
    if USERS_FILE.exists():
        return

    default = pd.DataFrame(
        [
            {"username": "admin", "role": "admin", "pw_hash": _pw_hash("admin123", "salt_admin")},
            {"username": "manager", "role": "manager", "pw_hash": _pw_hash("manager123", "salt_manager")},
            {"username": "staff", "role": "staff", "pw_hash": _pw_hash("staff123", "salt_staff")},
        ]
    )
    default.to_csv(USERS_FILE, index=False)


@st.cache_data
def load_users() -> pd.DataFrame:
    ensure_users_file()
    dfu = pd.read_csv(USERS_FILE)

    for c in ["username", "role", "pw_hash"]:
        if c not in dfu.columns:
            dfu[c] = ""

    dfu["username"] = dfu["username"].astype(str).str.strip().str.lower()
    dfu["role"] = dfu["role"].astype(str).str.strip().str.lower()
    dfu["pw_hash"] = dfu["pw_hash"].astype(str).str.strip()

    dfu = dfu[dfu["username"] != ""].drop_duplicates(subset=["username"], keep="last")
    return dfu.reset_index(drop=True)


def save_users(dfu: pd.DataFrame) -> None:
    out = dfu.copy()
    out["username"] = out["username"].astype(str).str.strip().str.lower()
    out["role"] = out["role"].astype(str).str.strip().str.lower()
    out["pw_hash"] = out["pw_hash"].astype(str).str.strip()
    out = out[out["username"] != ""].drop_duplicates(subset=["username"], keep="last")
    out.to_csv(USERS_FILE, index=False)
    st.cache_data.clear()


def get_user_record(username: str) -> dict | None:
    dfu = load_users()
    u = (username or "").strip().lower()
    hit = dfu[dfu["username"] == u]
    if hit.empty:
        return None
    r = hit.iloc[0].to_dict()
    return {"username": r["username"], "role": r["role"], "pw_hash": r["pw_hash"]}


def create_user(username: str, password: str, role: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    role = (role or "").strip().lower()

    if not u:
        return False, "Username is required."
    if role not in {"admin", "manager", "staff"}:
        return False, "Role must be admin, manager, or staff."
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."

    dfu = load_users()
    if (dfu["username"] == u).any():
        return False, "That username already exists."

    salt = f"salt_{u}"
    pw_hash = _pw_hash(password, salt)
    dfu = pd.concat([dfu, pd.DataFrame([{"username": u, "role": role, "pw_hash": pw_hash}])], ignore_index=True)
    save_users(dfu)
    return True, "User created."


def update_password(username: str, new_password: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    if len(new_password or "") < 6:
        return False, "Password must be at least 6 characters."

    dfu = load_users()
    m = dfu["username"] == u
    if not m.any():
        return False, "User not found."

    salt = f"salt_{u}"
    dfu.loc[m, "pw_hash"] = _pw_hash(new_password, salt)
    save_users(dfu)
    return True, "Password updated."


def update_role(username: str, new_role: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    new_role = (new_role or "").strip().lower()
    if new_role not in {"admin", "manager", "staff"}:
        return False, "Role must be admin, manager, or staff."

    dfu = load_users()
    m = dfu["username"] == u
    if not m.any():
        return False, "User not found."

    dfu.loc[m, "role"] = new_role
    save_users(dfu)
    return True, "Role updated."


def delete_user(username: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    if u == "admin":
        return False, "You can't delete the default admin account."

    dfu = load_users()
    before = len(dfu)
    dfu = dfu[dfu["username"] != u].copy()
    if len(dfu) == before:
        return False, "User not found."

    save_users(dfu)
    return True, "User deleted."


# ----------------------------
# Auth (file-backed)
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
            username = st.text_input("Username", placeholder="admin, manager or staff")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Log in")

        if submit:
            u = (username or "").strip().lower()
            user = get_user_record(u)

            if user and _pw_verify(password, user["pw_hash"]):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = user["role"]
                st.success(f"Welcome, {st.session_state.role.title()}.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown('<div class="bp-divider"></div>', unsafe_allow_html=True)
        st.caption("Default accounts (change immediately): admin/admin123, manager/manager123, staff/staff123")
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


def _row_fingerprint(row: pd.Series) -> str:
    parts = [
        str(row.get("date", "")),
        str(row.get("product", "")),
        str(row.get("qty", "")),
        str(row.get("unit_price", "")),
        str(row.get("staff_user", "")),
        str(row.get("created_at", "")),
    ]
    raw = "||".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:12]


def save_sales_log(df: pd.DataFrame) -> None:
    cols = ["date", "product", "qty", "unit_price", "staff_user", "created_at"]
    out = df.copy()

    for c in cols:
        if c not in out.columns:
            out[c] = ""

    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date.astype(str)
    out["product"] = out["product"].astype(str).str.strip()
    out["qty"] = pd.to_numeric(out["qty"], errors="coerce").fillna(0).astype(int)
    out["unit_price"] = pd.to_numeric(out["unit_price"], errors="coerce").fillna(0.0).astype(float)
    out["staff_user"] = out["staff_user"].astype(str).str.strip().str.lower()
    out["created_at"] = out["created_at"].astype(str).str.strip()

    out[cols].to_csv(SALES_LOG, index=False)


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
    df["created_at"] = df["created_at"].astype(str).str.strip()
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

    # weird layout: first row contains product names under "Unnamed" cols
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

    # alternative long format
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


def simple_forecast(series: pd.Series, days: int) -> pd.DataFrame:
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


def linear_regression_forecast(series: pd.Series, days: int) -> Tuple[pd.DataFrame, dict]:
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


def random_forest_forecast(series: pd.Series, days: int) -> Tuple[pd.DataFrame, dict]:
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


def gradient_boosting_forecast(series: pd.Series, days: int) -> Tuple[pd.DataFrame, dict]:
    """
    Gradient Boosting Regressor using the same lag/weekday features as the RF model.
    We do recursive (one-step-ahead) forecasting, same as RF.
    """
    if not SKLEARN_OK or GradientBoostingRegressor is None:
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

    model = GradientBoostingRegressor(random_state=42, n_estimators=400, learning_rate=0.05, max_depth=3)
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
    info = {"ok": True, "type": "gradient_boosting", "r2_train": r2}
    return pred_df, info


def forecast_series_for_mode(daily_total: pd.Series, forecast_days: int, mode_name: str) -> tuple[pd.Series, dict]:
    """
    Returns (pred_series indexed by future dates, model_info)
    mode_name must be one of:
      - "AI (Heuristic)"
      - "ML (Linear Regression)"
      - "AI (Random Forest)"
      - "ML (Gradient Boosting)"
    """
    if mode_name == "AI (Heuristic)":
        pred_raw = simple_forecast(daily_total, days=forecast_days)
        model_info = {"ok": True, "type": "heuristic"}
    elif mode_name == "ML (Linear Regression)":
        pred_raw, model_info = linear_regression_forecast(daily_total, days=forecast_days)
    elif mode_name == "AI (Random Forest)":
        pred_raw, model_info = random_forest_forecast(daily_total, days=forecast_days)
    else:
        pred_raw, model_info = gradient_boosting_forecast(daily_total, days=forecast_days)

    last_date = daily_total.index.max()
    future_index = pd.date_range(last_date + pd.Timedelta(days=1), periods=forecast_days, freq="D")
    pred_series = pd.Series(pred_raw["predicted"].values, index=future_index)
    return pred_series, model_info


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
    render_pink_header("Manager • Sales Records", "Filter, review, export, and manage (edit/delete) the sales log.")

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

    st.write("")
    st.markdown("### Manage entries (edit / delete)")
    st.caption("Select an entry from the filtered results, then edit fields or delete it.")

    if out.empty:
        st.info("No rows match the current filters, so there is nothing to edit or delete.")
        return

    out = out.copy()
    out["_row_id"] = out.apply(_row_fingerprint, axis=1)

    def _label(r: pd.Series) -> str:
        d = pd.to_datetime(r["date"], errors="coerce")
        d_str = d.date().isoformat() if pd.notna(d) else str(r.get("date", ""))
        return (
            f"{d_str} | {r.get('product','')} | qty {int(r.get('qty',0))} | "
            f"£{float(r.get('unit_price',0.0)):.2f} | {r.get('staff_user','')} | {str(r.get('created_at',''))}"
        )

    options = out["_row_id"].tolist()
    labels = {rid: _label(out.loc[idx]) for idx, rid in zip(out.index, options)}

    selected_id = st.radio(
        "Select a record",
        options=options,
        format_func=lambda rid: labels.get(rid, rid),
    )

    selected_filtered_row = out[out["_row_id"] == selected_id].iloc[0]
    selected_index = selected_filtered_row.name
    current = df.loc[selected_index].copy()

    price_map = load_price_map()
    known_products = sorted(set(list(price_map.keys()) + df["product"].dropna().astype(str).tolist()))

    st.markdown('<div class="bp-card">', unsafe_allow_html=True)
    st.markdown('<div class="bp-badge">Manager actions</div>', unsafe_allow_html=True)

    cA, cB = st.columns([3, 1])
    with cA:
        st.markdown("#### Edit selected entry")

        with st.form("manager_edit_form", clear_on_submit=False):
            cur_date = pd.to_datetime(current["date"], errors="coerce")
            default_date = cur_date.date() if pd.notna(cur_date) else date.today()
            new_date = st.date_input("Date", value=default_date, key="mgr_edit_date")

            cur_product = str(current.get("product", "")).strip()
            if cur_product not in known_products and cur_product:
                known_products = [cur_product] + known_products
            prod_index = max(0, known_products.index(cur_product)) if cur_product in known_products else 0
            new_product = st.radio("Product", known_products, index=prod_index, key="mgr_edit_product")

            suggested_price = float(price_map[new_product]) if new_product in price_map else float(
                current.get("unit_price", 0.0)
            )
            new_unit_price = st.number_input(
                "Unit price (£)",
                min_value=0.0,
                step=0.05,
                value=float(suggested_price),
                key="mgr_edit_unit_price",
            )

            new_qty = st.number_input(
                "Quantity sold",
                min_value=0,
                step=1,
                value=int(current.get("qty", 0)),
                key="mgr_edit_qty",
            )

            new_staff_user = st.text_input(
                "Staff user (username)",
                value=str(current.get("staff_user", "")).strip().lower(),
                key="mgr_edit_staff",
            )

            new_created_at = st.text_input(
                "Created at (timestamp string)",
                value=str(current.get("created_at", "")).strip(),
                key="mgr_edit_created_at",
                help="Leave as-is unless you need to correct it.",
            )

            save_btn = st.form_submit_button("Save changes")

        if save_btn:
            df2 = df.copy()
            df2.loc[selected_index, "date"] = pd.to_datetime(str(new_date), errors="coerce")
            df2.loc[selected_index, "product"] = str(new_product).strip()
            df2.loc[selected_index, "qty"] = int(new_qty)
            df2.loc[selected_index, "unit_price"] = float(new_unit_price)
            df2.loc[selected_index, "staff_user"] = str(new_staff_user).strip().lower()
            df2.loc[selected_index, "created_at"] = str(new_created_at).strip()

            save_sales_log(df2)
            st.success("Entry updated.")
            st.rerun()

    with cB:
        st.markdown("#### Delete")
        st.caption("This permanently removes the row from sales_entries.csv.")
        if st.button("Delete selected entry", type="primary"):
            df2 = df.drop(index=selected_index).copy()
            save_sales_log(df2)
            st.success("Entry deleted.")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def page_admin_user_management() -> None:
    render_pink_header("Admin • User Management", "Create accounts, reset passwords, and set roles.")

    dfu = load_users()

    st.subheader("Current users")
    show = dfu[["username", "role"]].sort_values(["role", "username"])
    st.dataframe(show, use_container_width=True)

    st.write("")
    st.markdown("### Create a new user")
    with st.form("admin_create_user", clear_on_submit=True):
        new_u = st.text_input("Username (lowercase recommended)")
        new_role = st.radio("Role", ["staff", "manager", "admin"], horizontal=True)
        new_pw = st.text_input("Temporary password", type="password")
        create_btn = st.form_submit_button("Create user")

    if create_btn:
        ok, msg = create_user(new_u, new_pw, new_role)
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()

    st.write("")
    st.markdown("### Reset password")
    users = dfu["username"].tolist()
    if users:
        target = st.radio("Select user", users, index=0)
        with st.form("admin_reset_pw", clear_on_submit=True):
            pw1 = st.text_input("New password", type="password")
            reset_btn = st.form_submit_button("Update password")
        if reset_btn:
            ok, msg = update_password(target, pw1)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
    else:
        st.info("No users found.")

    st.write("")
    st.markdown("### Change role")
    if users:
        target2 = st.radio("User to change role", users, index=0, key="role_user_pick")
        new_role2 = st.radio("New role", ["staff", "manager", "admin"], horizontal=True, key="new_role_pick")
        if st.button("Update role"):
            ok, msg = update_role(target2, new_role2)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    st.write("")
    st.markdown("### Delete user")
    st.caption("Admin account cannot be deleted.")
    if users:
        target3 = st.radio("User to delete", users, index=0, key="delete_user_pick")
        if st.button("Delete user", type="primary"):
            ok, msg = delete_user(target3)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()


def page_predictions_dashboard() -> None:
    render_pink_header("Predictions", "Upload café CSVs to view trends and generate a forecast.")

    # ---- NEW: Why models section (for dashboard + report) ----
    with st.expander("Why these prediction models? (method justification)"):
        st.markdown(
            """
**Why we use multiple models**
- Food demand varies because of **weekday patterns, seasonality, events, and randomness**. No single model is best in all situations.
- We implement a **baseline heuristic** plus two **machine-learning models** to compare accuracy and robustness.
- This supports the project aim: **reduce food waste** by selecting a forecasting method that matches the data.

**1) AI (Heuristic) — baseline**
- Uses recent moving average + a simple trend.
- Strength: **fast, transparent, and stable** even with small datasets.
- Weakness: cannot learn complex patterns (e.g., strong weekday effects).

**2) ML (Linear Regression) — interpretable trend model**
- Fits a straight-line trend over time.
- Strength: very **interpretable** (slope per day), good when demand changes steadily.
- Weakness: assumes a linear relationship; can underperform when demand is non-linear or seasonal.

**3) AI (Random Forest) — non-linear model**
- Learns from lagged sales (yesterday, last week, etc.) and weekday features.
- Strength: captures **non-linear** effects and interactions (e.g., weekends vs weekdays).
- Weakness: needs more data; can overfit if data is limited.

**4) ML (Gradient Boosting) — strong predictive learner**
- Boosted trees can be very accurate with structured tabular features (lags + weekday).
- Strength: often **high accuracy** with well-chosen features.
- Weakness: still needs enough history; less interpretable than linear regression.

**How we choose a “best” model**
- We use a **time-based holdout** (e.g., last 14 days) and compare **MAE / RMSE / MAPE**.
- The model with the lowest error is recommended for operational use, while others remain available for comparison.
            """
        )

    st.markdown("### Upload files")
    coffee_file = st.file_uploader("Coffee Sales CSV", type=["csv"], key="coffee_upload")
    croissant_file = st.file_uploader("Croissant Sales CSV", type=["csv"], key="croissant_upload")

    horizon_weeks = st.radio("Forecast horizon", [4, 8], index=0, horizontal=True)
    forecast_days = int(horizon_weeks) * 7

    modes = ["AI (Heuristic)", "ML (Linear Regression)", "AI (Random Forest)", "ML (Gradient Boosting)"]
    mode = st.radio("Prediction mode", modes, horizontal=True)

    st.caption(
        "Heuristic uses recent average + trend. Linear Regression fits a straight line. "
        "Random Forest / Gradient Boosting use lag + weekday features."
    )

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

    # ---- NEW: Model comparison metrics (time-based holdout) ----
    st.subheader("Model accuracy comparison (holdout evaluation)")
    holdout_days = st.slider("Holdout days (evaluate on the most recent days)", 7, 28, 14, step=7)
    metrics_df, best_mode = evaluate_models_time_holdout(daily_total, holdout_days=holdout_days, modes=modes)

    if best_mode:
        st.success(f"Recommended model (lowest RMSE on last {holdout_days} days): **{best_mode}**")
    else:
        st.info("Not enough data to run holdout evaluation reliably.")

    # show metrics nicely
    if not metrics_df.empty:
        show_metrics = metrics_df.copy()
        # friendly formatting
        for c in ["MAE", "RMSE", "MAPE_%"]:
            if c in show_metrics.columns:
                show_metrics[c] = pd.to_numeric(show_metrics[c], errors="coerce")

        st.dataframe(show_metrics, use_container_width=True)

    st.subheader(f"Forecast (next {horizon_weeks} weeks)")

    # ---- Comparison overlay chart (all models) ----
    compare_models = st.checkbox("Compare AI vs ML forecasts (chart)", value=True)
    if compare_models:
        compare_modes = ["AI (Heuristic)", "ML (Linear Regression)", "AI (Random Forest)", "ML (Gradient Boosting)"]
        preds = {}
        infos = {}

        for m in compare_modes:
            s_pred, info = forecast_series_for_mode(daily_total, forecast_days, m)
            preds[m] = s_pred
            infos[m] = info

        comp_df = pd.DataFrame(preds)
        chart_section_title("Forecast comparison", "All models forecast the same horizon for an apples-to-apples comparison.")
        st.line_chart(comp_df)

        with st.expander("Comparison model details"):
            st.write(infos)

    # ---- Single selected model (keeps your band + download) ----
    pred_series, model_info = forecast_series_for_mode(daily_total, forecast_days, mode)
    band_df = make_pred_band(pred_series, daily_total)

    st.caption("Predicted daily sales with a variation band based on recent volatility.")
    st.line_chart(band_df[["predicted", "lower", "upper"]])

    with st.expander("Forecast details"):
        st.write(model_info)

    out = band_df.reset_index().rename(columns={"index": "date"})
    csv_bytes = out.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download {horizon_weeks}-week forecast (CSV)",
        data=csv_bytes,
        file_name=f"prediction_next_{horizon_weeks}_weeks.csv",
        mime="text/csv",
    )


# ----------------------------
# App start
# ----------------------------
inject_blackpink_theme()

if not login_gate():
    st.stop()

with st.sidebar:
    st.markdown("### Session")
    st.write(f"User: **{st.session_state.username}**")
    st.write(f"Role: **{st.session_state.role}**")
    logout_button()
    st.markdown("---")

    if st.session_state.role == "admin":
        page = st.radio("Navigation", ["User Management", "Sales Overview", "Sales Records", "Predictions"], index=0)
    elif st.session_state.role == "manager":
        page = st.radio("Navigation", ["Sales Overview", "Sales Records", "Predictions"], index=0)
    else:
        page = st.radio("Navigation", ["Record Sale", "Predictions"], index=0)

if st.session_state.role == "admin" and page == "User Management":
    page_admin_user_management()
elif st.session_state.role == "admin" and page == "Sales Overview":
    page_manager_sales_overview()
elif st.session_state.role == "admin" and page == "Sales Records":
    page_manager_sales_records()
elif st.session_state.role == "manager" and page == "Sales Overview":
    page_manager_sales_overview()
elif st.session_state.role == "manager" and page == "Sales Records":
    page_manager_sales_records()
elif st.session_state.role == "staff" and page == "Record Sale":
    page_staff_record_sale()
else:
    page_predictions_dashboard()

if not PRICE_FILE.exists():
    st.warning("product_prices.csv was not found and a template should have been created. Please check your folder.")

