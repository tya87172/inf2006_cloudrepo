PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS coe_bids (
    month TEXT NOT NULL,
    month_dt TEXT NOT NULL,
    bidding_no INTEGER NOT NULL,
    vehicle_class TEXT NOT NULL,
    quota INTEGER NOT NULL,
    bids_success INTEGER NOT NULL,
    bids_received INTEGER NOT NULL,
    premium INTEGER NOT NULL,
    PRIMARY KEY (month, bidding_no, vehicle_class)
);

CREATE INDEX IF NOT EXISTS idx_coe_bids_vehicle_class ON coe_bids (vehicle_class);
CREATE INDEX IF NOT EXISTS idx_coe_bids_month_dt ON coe_bids (month_dt);
