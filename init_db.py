import sqlite3
from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "COEBiddingResultsPrices.csv"
SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")
DB_PATH = Path(__file__).resolve().with_name("coe.db")


def load_raw_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Clean numeric columns (remove commas and coerce to numbers).
    numeric_cols = ["quota", "bids_success", "bids_received", "premium"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")

    # Ensure bidding_no is numeric in case it arrives as text.
    df["bidding_no"] = pd.to_numeric(df["bidding_no"], errors="coerce")

    # Convert month to a normalized YYYY-MM-01 date for filtering.
    df["month_dt"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df["month_dt"] = df["month_dt"].dt.strftime("%Y-%m-01")

    # Drop rows with missing critical values.
    df = df.dropna(
        subset=["month", "month_dt", "bidding_no", "vehicle_class"] + numeric_cols
    )

    # Use integer types for numeric fields in SQLite.
    df[numeric_cols + ["bidding_no"]] = df[numeric_cols + ["bidding_no"]].astype(int)

    return df


def init_db(db_path: Path, schema_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_path.read_text())


def insert_rows(db_path: Path, df: pd.DataFrame) -> None:
    insert_sql = """
        INSERT OR REPLACE INTO coe_bids (
            month,
            month_dt,
            bidding_no,
            vehicle_class,
            quota,
            bids_success,
            bids_received,
            premium
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    rows = list(
        df[
            [
                "month",
                "month_dt",
                "bidding_no",
                "vehicle_class",
                "quota",
                "bids_success",
                "bids_received",
                "premium",
            ]
        ].itertuples(index=False, name=None)
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(insert_sql, rows)
        conn.commit()


def main() -> None:
    df = load_raw_csv(DATA_PATH)
    init_db(DB_PATH, SCHEMA_PATH)
    insert_rows(DB_PATH, df)
    print(f"Loaded {len(df)} rows into {DB_PATH}")


if __name__ == "__main__":
    main()
