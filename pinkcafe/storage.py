from __future__ import annotations

from datetime import datetime
from typing import Dict
import hashlib

import numpy as np
import pandas as pd
import streamlit as st

from constants import PRICE_FILE, SALES_LOG

def ensure_price_file_template() -> None:
    if PRICE_FILE.exists():
        return
    template = pd.DataFrame({"product": ["Cappuccino", "Americano", "Croissant"], "unit_price": [3.50, 3.00, 2.20]})
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

def new_sale_row(d, product: str, qty: int, unit_price: float, staff_user: str) -> dict:
    return {
        "date": str(d),
        "product": product,
        "qty": int(qty),
        "unit_price": float(unit_price),
        "staff_user": str(staff_user).strip().lower(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }