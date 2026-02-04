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
