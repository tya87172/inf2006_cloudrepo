from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR / "db" / "coe.db"
FRONTEND_DIST_DIR = BACKEND_DIR.parent / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

app = FastAPI(title="COE Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="assets")


def load_seasonality_from_db(db_path, vehicle_class, start_year, end_year, aggregation):
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")

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


@app.get("/api/seasonality")
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


@app.get("/api/analysis")
def get_analysis_data(
    vehicle_class: str = Query("ALL"),
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
):
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
        return {"distribution": [], "scatter": [], "count": 0}

    df["premium"] = pd.to_numeric(df["premium"].astype(str).str.replace(",", ""), errors="coerce")
    df["quota"] = pd.to_numeric(df["quota"].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["premium", "quota"])

    distribution_data = df["premium"].tolist()
    scatter_data = df[["quota", "premium", "vehicle_class"]].to_dict(orient="records")

    return {
        "vehicle_class": vehicle_class,
        "distribution": distribution_data,
        "scatter": scatter_data,
        "count": len(df),
    }


@app.get("/api/premium")
def get_premium_analysis(
    vehicle_class: str = Query("ALL"),
    window: int = Query(6, ge=1),
    x_axis_mode: Literal["Year", "Month"] = "Year",
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
):
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

    df["month_dt"] = pd.to_datetime(df["month_dt"], errors="coerce")
    df["premium"] = pd.to_numeric(df["premium"].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["month_dt", "premium"])

    df["year"] = df["month_dt"].dt.year
    df["month_name"] = df["month_dt"].dt.month_name()

    if x_axis_mode == "Year":
        grouped = df.groupby("year", as_index=False)["premium"].mean()
        grouped["x_axis"] = grouped["year"]
        grouped["x_label"] = grouped["year"].astype(str)
    else:
        grouped = df.groupby("month_name", as_index=False)["premium"].mean()
        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        grouped = grouped.set_index("month_name").reindex(month_order).reset_index()
        grouped["x_axis"] = grouped["month_name"]
        grouped["x_label"] = grouped["month_name"].str[:3]

    grouped["moving_avg"] = grouped["premium"].rolling(window=window).mean()
    grouped = grouped.replace([np.nan, np.inf, -np.inf], None)

    payload = grouped[["x_axis", "x_label", "premium", "moving_avg"]].to_dict(orient="records")
    return {
        "vehicle_class": vehicle_class,
        "window": window,
        "x_axis_mode": x_axis_mode,
        "data": payload,
        "count": len(payload),
    }


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    index_path = FRONTEND_DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "React build not found. Run the frontend dev server or build assets.",
    }
