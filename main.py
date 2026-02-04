import sqlite3
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

DB_PATH = Path(__file__).resolve().parent / "db" / "coe.db"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def load_seasonality_from_db(db_path, vehicle_class, start_year, end_year, aggregation):
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")

    query = """
          SELECT month_dt, \
                 quota, \
                 premium
          FROM coe_bids
          WHERE vehicle_class = ?
            AND CAST(strftime('%Y', month_dt) AS INTEGER) BETWEEN ? AND ? \
          """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            query, conn, params=(vehicle_class, start_year, end_year)
        )

    if df.empty:
        return df

    df["month_dt"] = pd.to_datetime(df["month_dt"])
    df["month_name"] = df["month_dt"].dt.month_name()

    if aggregation == "median":
        seasonal_df = df.groupby("month_name").median(numeric_only=True)
    else:
        seasonal_df = df.groupby("month_name").mean(numeric_only=True)

    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    seasonal_df = seasonal_df.reindex(month_order).reset_index()

    return seasonal_df


@app.get("/seasonality")
def get_seasonality(vehicle_class, start_year, end_year, aggregation):
    if end_year < start_year:
        raise HTTPException(status_code=400, detail="end_year must be >= start_year")

    try:
        seasonal_df = load_seasonality_from_db(
            DB_PATH, vehicle_class, start_year, end_year, aggregation
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if seasonal_df.empty:
        return {"data": [], "count": 0}

    payload = seasonal_df[["month_name", "quota", "premium"]].to_dict(orient="records")
    return {"data": payload, "count": len(payload)}


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text()

import numpy as np


@app.get("/premium")
def get_premium_analysis(
    vehicle_class: str = Query("ALL"),                 # default ALL categories
    window: int = Query(6, ge=1),
    x_axis_mode: Literal["Year", "Month"] = "Year",
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
):
    # Build dynamic WHERE clause so 'ALL' and optional years are supported
    params = []
    where_clauses = []

    if vehicle_class and vehicle_class.upper() != "ALL":
        where_clauses.append("vehicle_class = ?")
        params.append(vehicle_class)

    if start_year is not None:
        where_clauses.append("CAST(strftime('%Y', month_dt) AS INTEGER) >= ?")
        params.append(start_year)

    if end_year is not None:
        where_clauses.append("CAST(strftime('%Y', month_dt) AS INTEGER) <= ?")
        params.append(end_year)

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    query = f"""
        SELECT month_dt, quota, premium, vehicle_class
        FROM coe_bids
        {where}
        ORDER BY month_dt
    """
    params = tuple(params)

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return {"data": [], "count": 0}

    # Convert types safely
    df["month_dt"] = pd.to_datetime(df["month_dt"], errors="coerce")
    df["premium"] = pd.to_numeric(df["premium"].astype(str).str.replace(",", ""), errors="coerce")

    # Remove bad rows
    df = df.dropna(subset=["month_dt", "premium"])

    df["year"] = df["month_dt"].dt.year
    df["month_name"] = df["month_dt"].dt.month_name()

    # ==========================
    # Grouping based on x_axis_mode
    # ==========================
    if x_axis_mode == "Year":
        grouped = df.groupby("year", as_index=False)["premium"].mean()
        grouped["x_axis"] = grouped["year"]
        grouped["x_label"] = grouped["year"].astype(str)

    else:  # Month mode (Jan-Dec grouped together across all years)
        grouped = df.groupby("month_name", as_index=False)["premium"].mean()

        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        grouped = grouped.set_index("month_name").reindex(month_order).reset_index()

        grouped["x_axis"] = grouped["month_name"]
        grouped["x_label"] = grouped["month_name"].str[:3]   # Jan, Feb, Mar...

    # Moving average
    grouped["moving_avg"] = grouped["premium"].rolling(window=window).mean()

    # ✅ Replace NaN/inf so JSON works
    grouped = grouped.replace([np.nan, np.inf, -np.inf], None)

    payload = grouped[["x_axis", "x_label", "premium", "moving_avg"]].to_dict(orient="records")
    return {
        "vehicle_class": vehicle_class,
        "window": window,
        "x_axis_mode": x_axis_mode,
        "data": payload,
        "count": len(payload),
    }


