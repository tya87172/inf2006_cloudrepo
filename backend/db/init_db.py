import mysql.connector
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "COEBiddingResultsPrices.csv"

RDS_CONFIG = {
    'host': 'database-1.c6iqpmthl1ik.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Test246!',
    'database': 'coe_analytics',
    'port': 3306
}

def get_db_connection():
    """Create and return a MySQL connection"""
    return mysql.connector.connect(**RDS_CONFIG)

def load_raw_csv(path: Path) -> pd.DataFrame:
    """Load and clean the CSV data"""
    df = pd.read_csv(path)
    
    # Clean numeric columns (remove commas and coerce to numbers)
    numeric_cols = ["quota", "bids_success", "bids_received", "premium"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
    
    # Ensure bidding_no is numeric
    df["bidding_no"] = pd.to_numeric(df["bidding_no"], errors="coerce")
    
    # Convert month to date format
    df["month_dt"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df["month_dt"] = df["month_dt"].dt.strftime("%Y-%m-01")
    
    # Drop rows with missing critical values
    df = df.dropna(
        subset=["month", "month_dt", "bidding_no", "vehicle_class"] + numeric_cols
    )
    
    return df

def init_database():
    """Initialize the database and load data"""
    print("Connecting to RDS MySQL...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table with MySQL syntax
    print("Creating table if not exists...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coe_bids (
            month VARCHAR(10) NOT NULL,
            month_dt DATE NOT NULL,
            bidding_no INT NOT NULL,
            vehicle_class VARCHAR(20) NOT NULL,
            quota INT NOT NULL,
            bids_success INT NOT NULL,
            bids_received INT NOT NULL,
            premium INT NOT NULL,
            PRIMARY KEY (month, bidding_no, vehicle_class),
            INDEX idx_vehicle_class (vehicle_class),
            INDEX idx_month_dt (month_dt)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM coe_bids")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"Table already has {count} rows. Skipping data load.")
        cursor.close()
        conn.close()
        return
    
    # Load CSV data
    print(f"Loading data from {DATA_PATH}...")
    df = load_raw_csv(DATA_PATH)
    
    # Insert data
    print(f"Inserting {len(df)} rows into RDS...")
    insert_query = """
        INSERT INTO coe_bids
        (month, month_dt, bidding_no, vehicle_class, quota, bids_success, bids_received, premium)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for _, row in df.iterrows():
        cursor.execute(insert_query, (
            row['month'],
            row['month_dt'],
            int(row['bidding_no']),
            row['vehicle_class'],
            int(row['quota']),
            int(row['bids_success']),
            int(row['bids_received']),
            int(row['premium'])
        ))
    
    conn.commit()
    print(f"Successfully loaded {len(df)} rows into RDS!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_database()