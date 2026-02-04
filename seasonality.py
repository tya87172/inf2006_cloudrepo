import pandas as pd
import matplotlib.pyplot as plt

# --- 1. The Analytics Logic (Parameterized) ---
def get_seasonality_analysis(df, vehicle_class="Category A", start_year=2010, end_year=2025, aggregation="mean"):
    """
    Performs Seasonal Analysis across years.
    Satisfies: Group-by (category), Descriptive (mean/median), and Comparative (across years).
    """
    # Filter by Category and Year Range (Comparative Analysis)
    mask = (
        (df['vehicle_class'] == vehicle_class) &
        (df['month_dt'].dt.year >= start_year) &
        (df['month_dt'].dt.year <= end_year)
    )
    filtered_data = df[mask].copy()

    # Extract Month Name for grouping
    filtered_data['month_name'] = filtered_data['month_dt'].dt.month_name()

    # Perform Aggregation (Descriptive Statistics)
    if aggregation == "median":
        seasonal_df = filtered_data.groupby('month_name').median(numeric_only=True)
    else:
        seasonal_df = filtered_data.groupby('month_name').mean(numeric_only=True)

    # Reindex to ensure months are in chronological order (Jan -> Dec)
    month_order = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    seasonal_df = seasonal_df.reindex(month_order).reset_index()

    return seasonal_df

# --- 2. The Visualization Function ---
def plot_seasonality(seasonal_data, vehicle_class, start_year, end_year):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart for Quota (Supply side)
    ax1.bar(seasonal_data['month_name'], seasonal_data['quota'], color='tab:green', alpha=0.5, label='Avg Quota')
    ax1.set_ylabel('Avg Quota (Supply)', color='tab:green')
    ax1.tick_params(axis='x', rotation=45)

    # Line chart for Premium (Price side)
    ax2 = ax1.twinx()
    ax2.plot(seasonal_data['month_name'], seasonal_data['premium'], color='tab:red', marker='o', linewidth=3, label='Avg Premium')
    ax2.set_ylabel('Avg Premium ($)', color='tab:red')

    plt.title(f'Feature 2: Seasonality Analysis - {vehicle_class} ({start_year}-{end_year})')
    fig.tight_layout()
    plt.show()

# --- 3. Main Execution Block ---
if __name__ == "__main__":
    # Load and clean data
    # Make sure 'data/COEBiddingResultsPrices.csv' exists in your directory!
    raw_df = pd.read_csv('data/COEBiddingResultsPrices.csv')

    # Clean numeric columns
    for col in ['bids_success', 'bids_received', 'quota', 'premium']:
        raw_df[col] = pd.to_numeric(raw_df[col].astype(str).str.replace(',', ''), errors='coerce')

    # Convert to datetime
    raw_df['month_dt'] = pd.to_datetime(raw_df['month'])

    # NOW you can call the function because 'raw_df' is defined
    # Tinker with these parameters to see the interaction!
    results = get_seasonality_analysis(raw_df, vehicle_class="Category B", start_year=2018, end_year=2023)

    # Visualize the results
    plot_seasonality(results, "Category B", 2018, 2023)
