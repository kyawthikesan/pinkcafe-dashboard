from datetime import date
import pandas as pd
import streamlit as st

from theme import render_pink_header
from storage import load_sales_log, save_sales_log, _row_fingerprint, load_price_map
from forecasting import moving_average

def _chart_section_title(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    st.caption(subtitle)
    st.write("")

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

    _chart_section_title("Revenue by day", "Bars show revenue per day. The line shows the 7-day average.")
    st.bar_chart(pd.DataFrame({"Daily revenue": revenue_daily}))
    st.line_chart(pd.DataFrame({"7-day average": rev_ma7}))

    _chart_section_title("Weekly revenue", "Total revenue grouped by week.")
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
    st.download_button("Download filtered sales (CSV)", data=csv_bytes, file_name="sales_filtered.csv", mime="text/csv")

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

    selected_id = st.radio("Select a record", options=options, format_func=lambda rid: labels.get(rid, rid))

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

            suggested_price = float(price_map[new_product]) if new_product in price_map else float(current.get("unit_price", 0.0))
            new_unit_price = st.number_input("Unit price (£)", min_value=0.0, step=0.05, value=float(suggested_price), key="mgr_edit_unit_price")

            new_qty = st.number_input("Quantity sold", min_value=0, step=1, value=int(current.get("qty", 0)), key="mgr_edit_qty")

            new_staff_user = st.text_input("Staff user (username)", value=str(current.get("staff_user", "")).strip().lower(), key="mgr_edit_staff")

            new_created_at = st.text_input("Created at (timestamp string)", value=str(current.get("created_at", "")).strip(), key="mgr_edit_created_at")

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