import streamlit as st
from theme import render_pink_header
from auth import load_users, create_user, update_password, update_role, delete_user

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