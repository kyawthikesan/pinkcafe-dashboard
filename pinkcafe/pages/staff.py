from datetime import date
import pandas as pd
import streamlit as st

from theme import render_pink_header
from storage import load_price_map, append_sale, load_sales_log, new_sale_row

def page_staff_record_sale() -> None:
    render_pink_header(
        "Staff • Record Sales",
        "Record completed sales using the current product price list."
    )

    price_map = load_price_map()
    products = list(price_map.keys())

    st.info(
        "Product prices are set from `product_prices.csv`. For any price changes, please contact a manager.",
        icon=None
    )

    with st.form("sale_form", clear_on_submit=True):
        d = st.date_input("Sale date", value=date.today())
        product = st.radio("Select product", products, index=0)
        unit_price = float(price_map[product])

        st.markdown(f"**Unit price:** £{unit_price:.2f}")

        qty = st.number_input("Quantity sold", min_value=1, step=1, value=1)
        submitted = st.form_submit_button("Save sale")

    if submitted:
        row = new_sale_row(d, product, int(qty), float(unit_price), st.session_state.username)
        append_sale(row)
        st.success("Sale recorded successfully.")
        st.rerun()

    st.write("")
    st.subheader("Recent sales entries")
    df = load_sales_log()
    mine = df[df["staff_user"] == str(st.session_state.username).strip().lower()].copy()
    if mine.empty:
        st.caption("No sales entries recorded yet.")
    else:
        mine = mine.sort_values("created_at", ascending=False).head(20)
        show = mine[["date", "product", "qty", "unit_price", "total", "created_at"]].copy()
        show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.date.astype(str)
        show["unit_price"] = show["unit_price"].map(lambda x: f"£{float(x):.2f}")
        show["total"] = show["total"].map(lambda x: f"£{float(x):.2f}")
        st.dataframe(show, use_container_width=True)
