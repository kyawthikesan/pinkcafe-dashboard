import pandas as pd
import streamlit as st

from theme import render_pink_header
from forecasting import (
    load_coffee_weird_layout,
    load_simple_product_file,
    moving_average,
    forecast_series_for_mode,
    make_pred_band,
    evaluate_models_time_holdout,
)

def _friendly_kpi_help(title: str, text: str) -> None:
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

def _chart_section_title(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    st.caption(subtitle)
    st.write("")

def page_predictions_dashboard() -> None:
    render_pink_header("Predictions", "Upload café CSVs to view trends and generate a forecast.")

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
        _chart_section_title("Daily total sales", "Bars show daily sales. The line shows the 7-day average.")
        daily_chart_df = pd.DataFrame({"Daily sales": daily_total, "7-day average": daily_ma7})
        st.bar_chart(daily_chart_df[["Daily sales"]])
        st.line_chart(daily_chart_df[["7-day average"]])

        _friendly_kpi_help(
            "Reading the trend",
            "If the bars rise over time and the 7-day average rises, sales are increasing. "
            "If the 7-day average falls, sales are decreasing.",
        )

        _chart_section_title("Sales by product", "Top 5 products by total units sold.")
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
        _chart_section_title("Weekday pattern", "Average units sold by weekday.")
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
        _chart_section_title("Weekly target suggestion", "Based on the average of the last 14 days.")
        amount_to_sell = int(max(0, daily_total.tail(14).mean() * 7)) if len(daily_total) else 0
        st.markdown(f"### Suggested weekly target: **{amount_to_sell:,} units**")

    st.subheader("Model accuracy comparison (holdout evaluation)")
    holdout_days = st.slider("Holdout days (evaluate on the most recent days)", 7, 28, 14, step=7)
    metrics_df, best_mode = evaluate_models_time_holdout(daily_total, holdout_days=holdout_days, modes=modes)

    if best_mode:
        st.success(f"Recommended model (lowest RMSE on last {holdout_days} days): **{best_mode}**")
    else:
        st.info("Not enough data to run holdout evaluation reliably.")

    if not metrics_df.empty:
        show_metrics = metrics_df.copy()
        for c in ["MAE", "RMSE", "MAPE_%"]:
            if c in show_metrics.columns:
                show_metrics[c] = pd.to_numeric(show_metrics[c], errors="coerce")
        st.dataframe(show_metrics, use_container_width=True)

    st.subheader(f"Forecast (next {horizon_weeks} weeks)")

    compare_models = st.checkbox("Compare AI vs ML forecasts (chart)", value=True)
    if compare_models:
        preds = {}
        infos = {}
        for m in modes:
            s_pred, info = forecast_series_for_mode(daily_total, forecast_days, m)
            preds[m] = s_pred
            infos[m] = info
        comp_df = pd.DataFrame(preds)
        _chart_section_title("Forecast comparison", "All models forecast the same horizon for an apples-to-apples comparison.")
        st.line_chart(comp_df)
        with st.expander("Comparison model details"):
            st.write(infos)

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