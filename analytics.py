import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data/COEBiddingResultsPrices.csv')

# clean numeric columns i.e remove commas
cols_to_clean = ['bids_success', 'bids_received']

for col in cols_to_clean:
    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

# conv month to datetime objects
df['month_dt'] = pd.to_datetime(df['month'])

# filter by category
cat_a = df[df['vehicle_class'] == 'Category A'].sort_values('month_dt')

print("\ncleaned df:")
print(cat_a[['month', 'vehicle_class', 'premium', 'bids_received']].head())

window_size = 6

# rolling mean
cat_a['moving_avg'] = cat_a['premium'].rolling(window=window_size).mean()

# bid to quota
cat_a['demand_ratio'] = cat_a['bids_received'] / cat_a['quota']

print("\nanalysis results:")
print(cat_a[['month', 'premium', 'moving_avg', 'demand_ratio']].tail(10))

def get_coe_timeseries(df, vehicle_class="Category A", window=6):
    filtered_df = df[df['vehicle_class'] == vehicle_class].sort_values('month_dt').copy()

    # analytics calculations
    filtered_df['moving_avg'] = filtered_df['premium'].rolling(window=window).mean()
    filtered_df['demand_ratio'] = filtered_df['bids_received'] / filtered_df['quota']

    # calculate % change
    filtered_df['price_change_pct'] = filtered_df['premium'].pct_change() * 100

    return filtered_df

results = get_coe_timeseries(df, vehicle_class="Category A", window=12)
print(results.tail())

def plot_coe_trends(results_df, vehicle_class):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot Premium and Moving Average on the left Y-axis
    ax1.set_xlabel('Time (Bidding Rounds)')
    ax1.set_ylabel('Premium ($)', color='tab:blue')
    ax1.plot(results_df['month_dt'], results_df['premium'], label='Actual Premium', color='tab:blue', alpha=0.3)
    ax1.plot(results_df['month_dt'], results_df['moving_avg'], label='12-Month Moving Avg', color='tab:red', linewidth=2)
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.legend(loc='upper left')

    # Create a second Y-axis for the Demand Ratio
    ax2 = ax1.twinx()
    ax2.set_ylabel('Demand Ratio (Bids/Quota)', color='tab:green')
    ax2.plot(results_df['month_dt'], results_df['demand_ratio'], label='Demand Intensity', color='tab:green', linestyle='--', alpha=0.5)
    ax2.tick_params(axis='y', labelcolor='tab:green')

    plt.title(f'COE Time Series Analysis: {vehicle_class}')
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

# Run the visualization
plot_coe_trends(results, "Category A")
