import pandas as pd
import matplotlib.pyplot as plt


# --- 1. The Analytics Logic (Parameterized) ---
def get_premium_analysis(
    df,
    vehicle_class="Category A",
    window=6,
    x_axis_mode="Year",   # "Year" or "Month"
    aggregation="mean"    # "mean" or "median"
):
    """
    Moving Average Analysis with flexible X-axis:
    - Year mode: average premium by year
    - Month mode: group all Jan together, Feb together... (seasonality-style)
    """

    # Filter by category
    filtered_df = df[df["vehicle_class"] == vehicle_class].copy()

    if filtered_df.empty:
        return filtered_df

    # Ensure datetime exists
    if "month_dt" not in filtered_df.columns:
        filtered_df["month_dt"] = pd.to_datetime(filtered_df["month"])

    # Extract year and month name
    filtered_df["year"] = filtered_df["month_dt"].dt.year
    filtered_df["month_name"] = filtered_df["month_dt"].dt.month_name()

    # ==============================
    # Grouping logic based on x-axis
    # ==============================
    if x_axis_mode == "Year":
        if aggregation == "median":
            grouped = filtered_df.groupby("year")["premium"].median().reset_index()
        else:
            grouped = filtered_df.groupby("year")["premium"].mean().reset_index()

        grouped = grouped.sort_values("year")
        grouped.rename(columns={"year": "x_axis"}, inplace=True)
        grouped["x_label"] = grouped["x_axis"].astype(str)

    else:  # Month mode (group months together across all years)
        if aggregation == "median":
            grouped = filtered_df.groupby("month_name")["premium"].median().reset_index()
        else:
            grouped = filtered_df.groupby("month_name")["premium"].mean().reset_index()

        # Reindex month order Jan -> Dec
        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        grouped = grouped.set_index("month_name").reindex(month_order).reset_index()

        grouped.rename(columns={"month_name": "x_axis"}, inplace=True)
        grouped["x_label"] = grouped["x_axis"].str[:3]  # Jan, Feb, Mar...

    # Moving average
    grouped["moving_avg"] = grouped["premium"].rolling(window=window).mean()

    return grouped


# --- 2. The Visualization Function ---
def plot_premium(moving_avg_df, vehicle_class, window, x_axis_mode):
    fig, ax = plt.subplots(figsize=(12, 6))

    # Raw premiums: faint dashed line with small markers
    ax.plot(
        moving_avg_df["x_label"],
        moving_avg_df["premium"],
        label="Premium Price",
        color="C0",
        linestyle="--",
        linewidth=1,
        marker='.',
        markersize=6,
        alpha=0.4,
    )

    # Moving average: bold solid line with markers for emphasis
    ax.plot(
        moving_avg_df["x_label"],
        moving_avg_df["moving_avg"],
        label=f"{window}-Period Moving Avg",
        color="C1",
        linewidth=2.5,
        marker='o',
        markersize=6,
    )

    ax.set_title(f"Feature: Moving Average Analysis - {vehicle_class} ({x_axis_mode})")
    ax.set_xlabel(x_axis_mode)
    ax.set_ylabel("Premium ($)")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(frameon=True)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# --- 3. Main Execution Block ---
if __name__ == "__main__":
    raw_df = pd.read_csv("data/COEBiddingResultsPrices.csv")

    # Clean numeric columns
    for col in ["bids_success", "bids_received", "quota", "premium"]:
        raw_df[col] = pd.to_numeric(raw_df[col].astype(str).str.replace(",", ""), errors="coerce")

    # Convert to datetime
    raw_df["month_dt"] = pd.to_datetime(raw_df["month"])

    # Try Year mode
    results_year = get_premium_analysis(
        raw_df, vehicle_class="Category A", window=3, x_axis_mode="Year"
    )
    plot_premium(results_year, "Category A", 3, "Year")

    # Try Month mode (Jan-Dec grouped)
    results_month = get_premium_analysis(
        raw_df, vehicle_class="Category A", window=3, x_axis_mode="Month"
    )
    plot_premium(results_month, "Category A", 3, "Month")
