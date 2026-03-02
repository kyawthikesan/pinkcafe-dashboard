# app.py
import streamlit as st

from constants import APP_TITLE, PRICE_FILE
from theme import inject_blackpink_theme, inject_header_gap_fix
from auth import login_gate, logout_button
from pages.staff import page_staff_record_sale
from pages.manager import page_manager_sales_overview, page_manager_sales_records
from pages.admin import page_admin_user_management
from pages.predictions import page_predictions_dashboard

st.set_page_config(page_title=APP_TITLE, layout="wide")

# ----------------------------
# Hide Streamlit's native multipage nav dropdown
# ----------------------------
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Theme + top-gap fix
inject_header_gap_fix()
inject_blackpink_theme()

# Auth gate
if not login_gate():
    st.stop()

with st.sidebar:
    st.markdown("### Session")
    st.write(f"User: **{st.session_state.username}**")
    st.write(f"Role: **{st.session_state.role}**")
    logout_button()
    st.markdown("---")

    # Your role-based navigation (the ONLY nav users should see)
    if st.session_state.role == "admin":
        page = st.radio("Navigation", ["User Management", "Sales Overview", "Sales Records", "Predictions"], index=0)
    elif st.session_state.role == "manager":
        page = st.radio("Navigation", ["Sales Overview", "Sales Records", "Predictions"], index=0)
    else:
        page = st.radio("Navigation", ["Record Sale", "Predictions"], index=0)

# Routing
if st.session_state.role == "admin" and page == "User Management":
    page_admin_user_management()
elif st.session_state.role in {"admin", "manager"} and page == "Sales Overview":
    page_manager_sales_overview()
elif st.session_state.role in {"admin", "manager"} and page == "Sales Records":
    page_manager_sales_records()
elif st.session_state.role == "staff" and page == "Record Sale":
    page_staff_record_sale()
else:
    page_predictions_dashboard()

# Sanity warning if template wasn't created
if not PRICE_FILE.exists():
    st.warning("product_prices.csv was not found and a template should have been created. Please check your folder.")