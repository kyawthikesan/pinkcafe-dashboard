# dashboardfoodwastage.py
# Bristol Pink Café – Streamlit Dashboard
# Works with your TWO CSVs:
#   1) "Pink CoffeeSales March - Oct 2025.csv"  (weird first-row product names)
#   2) "Pink CroissantSales March - Oct 2025.csv" (normal Date + Number Sold)
#
# Adds ML forecasting using Linear Regression (scikit-learn) via AI/ML toggle.

import streamlit as st
import pandas as pd
import numpy as np

# ---- ML import (safe) ----
try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_OK = True
except Exception:
    LinearRegression = None
    SKLEARN_OK = False

st.set_page_config(page_title="Bristol Pink Café Dashboard", layout="wide")

# ----------------------------
# Helpers
# ----------------------------
def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def parse_date_series(s: pd.Series) -> pd.Series:
    # Your dates look UK-style (dd/mm/yyyy) so dayfirst=True
    return pd.to_datetime(s, dayfirst=True, errors="coerce")

def load_coffee_weird_layout(uploaded_file) -> pd.DataFrame:
    """
    Handles your Coffee CSV format:
      Columns: Date, Number Sold, Unnamed: 2
      Row 0: Date is NaN, other columns contain product names (e.g., Cappuccino, Americano)
      Remaining rows: Date + numeric sales for each product
    Returns long format: date, product, units_sold
    """
    df = pd.read_csv(uploaded_file)
    df = normalize_cols(df)

    if "Date" not in df.columns:
        raise ValueError("Coffee file must contain a 'Date' column (as in your file).")

    # Detect the "header-like" first row
    first_date = df.loc[0, "Date"] if len(df) > 0 else None
    has_unnamed = any(str(c).lower().startswith("unnamed") for c in df.columns)

    if pd.isna(first_date) and has_unnamed and len(df.columns) >= 3:
        # Product names are stored in row 0 for all non-Date columns
        sales_cols = [c for c in df.columns if c != "Date"]
        product_names = [str(df.loc[0, c]).strip() for c in sales_cols]

        # Rename those columns to the product names
        df = df[["Date"] + sales_cols].copy()
        df.columns = ["Date"] + product_names

        # Drop the first row (it was the product-name row)
        df = df.iloc[1:].copy()
    else:
        # If it ever becomes a normal layout, we can support:
        # Date, Product, Number Sold
        lower_cols = [c.lower().strip() for c in df.columns]
        if "product" in lower_cols and any(x in lower_cols for x in ["number sold", "units_sold", "units sold", "sold"]):
            # map columns
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

        raise ValueError("Coffee file format not recognised. (Expected the weird 2-product layout).")

    # Convert dates + numeric columns
    df["Date"] = parse_date_series(df["Date"])
    df = df.dropna(subset=["Date"])

    for c in df.columns:
        if c != "Date":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Long format
    long = df.melt(id_vars=["Date"], var_name="product", value_name="units_sold")
    long = long.dropna(subset=["units_sold"])
    long["product"] = long["product"].astype(str).str.strip()
    long = long.rename(columns={"Date": "date"})
    return long[["date", "product", "units_sold"]]

def load_simple_product_file(uploaded_file, product_name: str) -> pd.DataFrame:
    """
    For your Croissant CSV: Date, Number Sold
    Returns long format: date, product, units_sold
    """
    df = pd.read_csv(uploaded_file)
    df = normalize_cols(df)

    # Find date column
    date_col = None
    for cand in ["Date", "date", "DATE"]:
        if cand in df.columns:
            date_col = cand
            break
    if date_col is None:
        raise ValueError(f"{product_name} file must contain a Date column.")

    # Find units sold column
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

def simple_forecast(series: pd.Series, days: int = 28) -> pd.DataFrame:
    """
    Simple AI-ish forecast: rolling mean + light trend from last points
    """
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

def linear_regression_forecast(series: pd.Series, days: int = 28):
    """
    ML forecast: Linear Regression on time index -> predict next N days.
    Returns:
      pred_df (DataFrame with 'predicted' col)
      model_info (dict with slope/intercept/r2)
    """
    if not SKLEARN_OK:
        return simple_forecast(series, days), {
            "ok": False,
            "reason": "scikit-learn not installed",
        }

    s = series.dropna()
    if len(s) < 5:
        return simple_forecast(series, days), {
            "ok": False,
            "reason": "not enough data (need ~5+ points)",
        }

    # X = 0..n-1
    X = np.arange(len(s)).reshape(-1, 1)
    y = s.values.astype(float)

    model = LinearRegression()
    model.fit(X, y)

    # Evaluate (on training data - ok for demo/coursework baseline)
    r2 = float(model.score(X, y))

    # Predict future
    X_future = np.arange(len(s), len(s) + days).reshape(-1, 1)
    y_future = model.predict(X_future)

    # clamp negatives
    y_future = np.clip(y_future, 0, None)

    pred_df = pd.DataFrame({"predicted": y_future})
    info = {
        "ok": True,
        "slope_per_day": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "r2_train": r2,
    }
    return pred_df, info


# ----------------------------
# Header UI
# ----------------------------
st.markdown(
    """
    <div style="background-color:#ffd1e8;padding:18px;border-radius:12px">
        <h1 style="margin:0;">Bristol Pink Café – Prediction Dashboard</h1>
        <p style="margin:0;">Coffee + Croissant sales (CSV)</p>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.header("Upload files")
    coffee_file = st.file_uploader("Coffee Sales CSV", type=["csv"])
    croissant_file = st.file_uploader("Croissant Sales CSV", type=["csv"])

    st.divider()
    mode = st.radio("Prediction mode", ["AI", "ML"], horizontal=True)

    st.caption("ML = Linear Regression forecast on daily totals.")

# Require both
if not coffee_file or not croissant_file:
    st.info("Upload BOTH CSV files in the sidebar to continue.")
    st.stop()

# ----------------------------
# Load + combine
# ----------------------------
try:
    coffee_long = load_coffee_weird_layout(coffee_file)          # Cappuccino + Americano
    croissant_long = load_simple_product_file(croissant_file, "Croissant")
except Exception as e:
    st.error(f"Error loading CSVs: {e}")
    st.stop()

df_all = pd.concat([coffee_long, croissant_long], ignore_index=True)

# clean
df_all["product"] = df_all["product"].astype(str).str.strip()
df_all["units_sold"] = pd.to_numeric(df_all["units_sold"], errors="coerce").fillna(0)
df_all = df_all.dropna(subset=["date"])
df_all = df_all.sort_values("date")

# ----------------------------
# Debug expander
# ----------------------------
with st.expander("🔎 Debug (cleaned data preview)"):
    st.write("Coffee (long format):")
    st.dataframe(coffee_long.head(10), use_container_width=True)
    st.write("Croissant (long format):")
    st.dataframe(croissant_long.head(10), use_container_width=True)
    st.write("Combined:")
    st.dataframe(df_all.head(10), use_container_width=True)

# ----------------------------
# Best selling products
# ----------------------------
st.subheader("🏆 Best selling products")
totals = df_all.groupby("product")["units_sold"].sum().sort_values(ascending=False)
top3 = totals.head(3)

cols = st.columns(3)
medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
for i in range(3):
    if i < len(top3):
        product = top3.index[i]
        units = int(top3.iloc[i])
        cols[i].metric(medals[i], product, f"{units:,} sold")
    else:
        cols[i].metric(medals[i], "-", "-")

# ----------------------------
# Main layout (charts + side panel)
# ----------------------------
left, right = st.columns([3, 2])

daily_total = df_all.groupby("date")["units_sold"].sum()

with left:
    st.subheader("📈 Total sales trend")
    st.line_chart(daily_total)

    st.write("")
    st.subheader("📈 Sales trend by product")
    pivot = (
        df_all.pivot_table(index="date", columns="product", values="units_sold", aggfunc="sum")
        .fillna(0)
    )
    st.line_chart(pivot)

with right:
    st.subheader("⚠️ Products that could generate a loss (low average sales)")
    avg = df_all.groupby("product")["units_sold"].mean().sort_values()
    threshold = float(avg.mean())
    risky = avg[avg < threshold]

    if len(risky) == 0:
        st.write("None detected with current rule.")
    else:
        for p in risky.index.tolist():
            st.write(f"• {p}")

    st.write("")
    st.subheader("📉 Based on previous patterns (recent period)")
    recent = daily_total.tail(max(14, len(daily_total) // 4))
    st.line_chart(recent)

    amount_to_sell = int(max(0, daily_total.tail(14).mean() * 7))  # next week estimate
    st.markdown(f"### Amount to sell: **{amount_to_sell:,}**")

# ----------------------------
# Prediction (next 4 weeks)
# ----------------------------
st.subheader("🔮 Prediction for next 4 weeks")
forecast_days = 28

if mode == "AI":
    pred_df = simple_forecast(daily_total, days=forecast_days)
    model_info = {"ok": True, "type": "heuristic"}
else:
    pred_df, model_info = linear_regression_forecast(daily_total, days=forecast_days)

# Future date index
last_date = daily_total.index.max()
future_index = pd.date_range(last_date + pd.Timedelta(days=1), periods=forecast_days, freq="D")
pred_df = pred_df.copy()
pred_df.index = future_index

st.line_chart(pred_df)

# ----------------------------
# Model details + install help
# ----------------------------
with st.expander("🧠 Prediction details"):
    if mode == "AI":
        st.write("**AI mode**: rolling mean + light recent trend (heuristic baseline).")
    else:
        st.write("**ML mode**: Linear Regression trained on daily total sales vs time index.")

        if not model_info.get("ok", False):
            st.warning(f"ML fallback used: {model_info.get('reason', 'unknown reason')}")
            if not SKLEARN_OK:
                st.code("pip install scikit-learn", language="bash")
        else:
            st.write(f"- Slope (units/day): **{model_info['slope_per_day']:.4f}**")
            st.write(f"- Intercept: **{model_info['intercept']:.4f}**")
            st.write(f"- R² (training fit): **{model_info['r2_train']:.3f}**")
            st.caption("R² shown is on training data (simple baseline for coursework).")

# ----------------------------
# Download prediction
# ----------------------------
out = pred_df.reset_index().rename(columns={"index": "date"})
csv_bytes = out.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download 4-week prediction (CSV)",
    data=csv_bytes,
    file_name="prediction_next_4_weeks.csv",
    mime="text/csv",
)
