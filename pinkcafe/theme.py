import streamlit as st

def inject_header_gap_fix() -> None:
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] {
            background: rgba(0,0,0,0) !important;
            height: 0px !important;
          }
          .block-container { padding-top: 0rem !important; }
          [data-testid="stAppViewContainer"],
          [data-testid="stApp"] {
            background: #000 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
        div[data-testid="stDataFrame"] * { color: var(--bp-text) !important; }
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