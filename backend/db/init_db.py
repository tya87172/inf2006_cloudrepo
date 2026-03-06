import mysql.connector
from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "COEBiddingResultsPrices.csv"
SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")

RDS_CONFIG = {
    'host': 'database-1.cbk24k08ex7p.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Test246!',
    'database': 'coe_analytics',
    'port': 3306
}


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

    # Use integer types for numeric fields.
    df[numeric_cols + ["bidding_no"]] = df[numeric_cols + ["bidding_no"]].astype(int)

    return df


def init_db(schema_path: Path) -> None:
    with mysql.connector.connect(**RDS_CONFIG) as conn:
        cursor = conn.cursor()
        # Execute schema (skip PRAGMA as it's SQLite-specific)
        schema_sql = schema_path.read_text()
        # Remove SQLite-specific PRAGMA
        schema_sql = schema_sql.replace("PRAGMA foreign_keys = ON;", "")
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        conn.commit()


def insert_rows(df: pd.DataFrame) -> None:
    insert_sql = """
        INSERT INTO coe_bids (
            month,
            month_dt,
            bidding_no,
            vehicle_class,
            quota,
            bids_success,
            bids_received,
            premium
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            quota = VALUES(quota),
            bids_success = VALUES(bids_success),
            bids_received = VALUES(bids_received),
            premium = VALUES(premium)
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

    with mysql.connector.connect(**RDS_CONFIG) as conn:
        cursor = conn.cursor()
        cursor.executemany(insert_sql, rows)
        conn.commit()


def main() -> None:
    df = load_raw_csv(DATA_PATH)
    init_db(SCHEMA_PATH)
    insert_rows(df)
    print(f"Loaded {len(df)} rows into RDS MySQL")


if __name__ == "__main__":
    main()