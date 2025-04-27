import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Define paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_dir = os.path.join(base_dir, 'cleaned_data')
output_dir = os.path.join(base_dir, 'outputs')

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# --- Load Data --- 
try:
    leases_path = os.path.join(input_dir, 'leases_clean.csv')
    price_path = os.path.join(input_dir, 'price_and_availability_clean.csv')
    occupancy_path = os.path.join(input_dir, 'major_market_occupancy_clean.csv')

    leases_df = pd.read_csv(leases_path)
    price_df = pd.read_csv(price_path)
    occupancy_df = pd.read_csv(occupancy_path)

    print("Data loaded successfully.")
    # Print unique markets for verification
    print("\nAvailable Markets in Price Data:")
    print(sorted(price_df['market'].unique()))
    print("\nAvailable Markets in Occupancy Data:")
    print(sorted(occupancy_df['market'].unique()))

except FileNotFoundError as e:
    print(f"Error loading data: {e}")
    print("Please ensure the cleaned data files are in the '../cleaned_data/' directory relative to the script.")
    exit()

# --- Explore Data Scope ---
print("\nAvailable Markets in Leases Data:")
print(sorted(leases_df['market'].unique()))
print("\nAvailable Regions in Leases Data:")
print(sorted(leases_df['region'].unique()))

# Define Target Cities and Markets
target_cities = ['Houston', 'Dallas', 'Austin']
# Define Target Markets (using the names found in price/occupancy files)
target_markets = ['Houston', 'Dallas-Ft. Worth', 'Austin']
post_covid_start_date = '2021-01-01'
construction_industry_name = 'Construction, Engineering and Architecture'

# --- Market Definitions and Mapping ---
# Core Texas + Competitors
target_markets_base = ['Houston', 'Dallas', 'Austin', 'Atlanta', 'Phoenix', 'Los Angeles', 'San Francisco']

# Define specific names for each file and the desired final short name
market_mapping = {
    'price': {
        'Houston': 'HOU', 'Dallas-Ft. Worth': 'DFW', 'Austin': 'AUS',
        'Atlanta': 'ATL', 'Phoenix': 'PHX', 'Los Angeles': 'LA', 'San Francisco': 'SF'
    },
    'leases': {
        'Houston': 'HOU', 'Dallas/Ft Worth': 'DFW', 'Austin': 'AUS',
        'Atlanta': 'ATL', 'Phoenix': 'PHX', 'Los Angeles': 'LA', 'San Francisco': 'SF'
    },
    'occupancy': {
        'Houston': 'HOU', 'Dallas/Ft Worth': 'DFW', 'Austin': 'AUS',
        'Los Angeles': 'LA', 'San Francisco': 'SF'
        # Note: ATL, PHX not in occupancy data based on previous check
    }
}

# Extract market lists for filtering
markets_for_price = list(market_mapping['price'].keys())
markets_for_leases = list(market_mapping['leases'].keys())
markets_for_occupancy = list(market_mapping['occupancy'].keys())

# Short names for plotting
short_market_names_price = list(market_mapping['price'].values())
short_market_names_leases = list(market_mapping['leases'].values())
short_market_names_occupancy = list(market_mapping['occupancy'].values())

post_covid_start_date_dt = pd.to_datetime('2021-01-01')
pre_covid_year = 2019
latest_year = 2024 # Assuming data goes up to roughly here, adjust if needed
latest_quarter_start = pd.to_datetime(f'{latest_year}-10-01') # Adjust if latest data is different

construction_industry_name = 'Construction, Engineering and Architecture'

# --- Data Cleaning and Preparation --- 

# Function to create a date column from year and quarter
def create_date(df):
    # Ensure year and quarter are integers
    df['year'] = df['year'].astype(int)
    # Map Quarter to Month (Start of Quarter)
    quarter_map = {'Q1': 1, 'Q2': 4, 'Q3': 7, 'Q4': 10}
    df['month'] = df['quarter'].map(quarter_map)
    # Create datetime object
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(DAY=1))
    df = df.drop(columns=['month'])
    return df

leases_df = create_date(leases_df)
price_df = create_date(price_df)
occupancy_df['date'] = pd.to_datetime(occupancy_df['year'].astype(str) + '-' + occupancy_df['quarter'].str[1].astype(int).apply(lambda q: f'{q*3-2:02d}-01'))

# Apply market name mapping
price_df['market_short'] = price_df['market'].map(market_mapping['price'])
leases_df['market_short'] = leases_df['market'].map(market_mapping['leases'])
occupancy_df['market_short'] = occupancy_df['market'].map(market_mapping['occupancy'])

print("Applied market name mapping.")

# --- Analysis (Expanded Scope) --- 

# 1. Construction Leasing Activity (All Target Markets)
print("\nAnalyzing Construction Leasing (Expanded Scope)...")
leases_filtered_expanded = leases_df[leases_df['market'].isin(markets_for_leases)].copy()
construction_leases_expanded = leases_filtered_expanded[leases_filtered_expanded['internal_industry'] == construction_industry_name].copy()
construction_agg_expanded = construction_leases_expanded.groupby(['market_short', 'date'])['leasedsf'].sum().reset_index()
construction_agg_expanded = construction_agg_expanded.sort_values(by=['market_short', 'date'])

# 2. Rent Trends (All Target Markets)
print("\nAnalyzing Rent Trends (Expanded Scope)...")
price_filtered_expanded = price_df[price_df['market'].isin(markets_for_price)].copy()
rent_agg_expanded = price_filtered_expanded.groupby(['market_short', 'date'])['overall_rent'].mean().reset_index()
rent_agg_expanded = rent_agg_expanded.sort_values(by=['market_short', 'date'])

# Calculate Indexed Rent Growth (Expanded Scope)
rent_agg_post_covid_expanded = rent_agg_expanded[rent_agg_expanded['date'] >= post_covid_start_date_dt].copy()
base_rents_expanded = rent_agg_post_covid_expanded[rent_agg_post_covid_expanded['date'] == post_covid_start_date_dt]
base_rents_expanded = base_rents_expanded.set_index('market_short')['overall_rent']
rent_agg_post_covid_expanded['base_rent'] = rent_agg_post_covid_expanded['market_short'].map(base_rents_expanded)
# Handle markets that might not have data exactly on 2021-01-01 (forward fill base rent)
rent_agg_post_covid_expanded['base_rent'] = rent_agg_post_covid_expanded.groupby('market_short')['base_rent'].ffill().bfill()
rent_agg_post_covid_expanded['rent_index'] = (rent_agg_post_covid_expanded['overall_rent'] / rent_agg_post_covid_expanded['base_rent']) * 100
rent_agg_post_covid_expanded = rent_agg_post_covid_expanded.dropna(subset=['rent_index']) # Drop if base rent couldn't be found

# 3. Occupancy Trends (Occupancy Market Subset)
print("\nAnalyzing Occupancy Trends (Subset)...")
occupancy_filtered_subset = occupancy_df[occupancy_df['market'].isin(markets_for_occupancy)].copy()
occupancy_agg_subset = occupancy_filtered_subset.groupby(['market_short', 'date'])['occupancy_proportion'].mean().reset_index()
occupancy_agg_subset = occupancy_agg_subset.sort_values(by=['market_short', 'date'])

# 4. Calculations for Bar Charts
# Rent Growth % Bar Chart Data
latest_rent_index = rent_agg_post_covid_expanded[rent_agg_post_covid_expanded['date'] == rent_agg_post_covid_expanded['date'].max()]
rent_growth_pct = latest_rent_index.set_index('market_short')['rent_index'] - 100
rent_growth_pct = rent_growth_pct.sort_values(ascending=False).reset_index()
rent_growth_pct.columns = ['Market', 'Rent Growth % (Since 2021-Q1)']

# Construction Leasing Total Bar Chart Data
construction_total_post_covid = construction_agg_expanded[construction_agg_expanded['date'] >= post_covid_start_date_dt]
construction_total_sum = construction_total_post_covid.groupby('market_short')['leasedsf'].sum() / 1_000_000 # Convert to millions
construction_total_sum = construction_total_sum.sort_values(ascending=False).reset_index()
construction_total_sum.columns = ['Market', 'Total Construction Leased SF (Millions, Since 2021-Q1)']

# Occupancy Change Bar Chart Data
occupancy_agg_subset['year'] = occupancy_agg_subset['date'].dt.year
occ_avg_pre = occupancy_agg_subset[occupancy_agg_subset['year'] == pre_covid_year].groupby('market_short')['occupancy_proportion'].mean()
occ_avg_post = occupancy_agg_subset[occupancy_agg_subset['year'] >= post_covid_start_date_dt.year].groupby('market_short')['occupancy_proportion'].mean()
occ_change = ((occ_avg_post - occ_avg_pre) * 100).round(1) # Pct point change
occ_change = occ_change.sort_values(ascending=False).reset_index()
occ_change.columns = ['Market', 'Occupancy Pct Point Change (Avg 2021+ vs Avg 2019)']

print("Calculations for summary charts complete.")

# --- Visualization (Expanded Scope - 6 New Plots) --- 
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

# Plot 1: Indexed Rent Growth Comparison (Wider Scope)
print("\nGenerating Plot 1: Wider Rent Index...")
plt.figure(figsize=(14, 8))
sns.lineplot(data=rent_agg_post_covid_expanded, x='date', y='rent_index', hue='market_short', marker='.')
plt.title(f'Indexed Rent Growth (Base {post_covid_start_date_dt.strftime("%Y-%m-%d")}=100)')
plt.xlabel('Date')
plt.ylabel('Rent Index (Base 100)')
plt.axhline(100, color='grey', linestyle='--', linewidth=0.8)
plt.legend(title='Market', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout for legend
plt.savefig(os.path.join(output_dir, 'comp_1_rent_index_expanded.png'))
plt.close()

# Plot 2: Construction Leasing Activity (Wider Scope)
print("Generating Plot 2: Wider Construction Leasing...")
plt.figure(figsize=(14, 8))
sns.lineplot(data=construction_agg_expanded, x='date', y='leasedsf', hue='market_short', marker='.')
plt.title(f'Quarterly Leased SF ({construction_industry_name})')
plt.xlabel('Date')
plt.ylabel('Leased Square Footage')
plt.legend(title='Market', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout for legend
plt.savefig(os.path.join(output_dir, 'comp_2_construction_leasing_expanded.png'))
plt.close()

# Plot 3: Post-COVID Rent Growth Ranking (Bar Chart)
print("Generating Plot 3: Rent Growth % Bar Chart...")
plt.figure(figsize=(12, 7))
sns.barplot(data=rent_growth_pct, x='Rent Growth % (Since 2021-Q1)', y='Market', palette='viridis')
plt.title(f'Total Rent Growth ({post_covid_start_date_dt.strftime("%Y-%m-%d")} to {rent_agg_post_covid_expanded["date"].max().strftime("%Y-%m-%d")})')
plt.xlabel('Rent Growth (%)')
plt.ylabel('Market')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'comp_3_rent_growth_pct_bar.png'))
plt.close()

# Plot 4: Post-COVID Construction Leasing Total (Bar Chart)
print("Generating Plot 4: Construction Total SF Bar Chart...")
plt.figure(figsize=(12, 7))
sns.barplot(data=construction_total_sum, x='Total Construction Leased SF (Millions, Since 2021-Q1)', y='Market', palette='magma')
plt.title(f'Total Construction Leased SF ({post_covid_start_date_dt.strftime("%Y-%m-%d")} Onwards)')
plt.xlabel('Total Leased SF (Millions)')
plt.ylabel('Market')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'comp_4_construction_total_sf_bar.png'))
plt.close()

# Plot 5: Occupancy Rate Trends (Competitive Set)
print("Generating Plot 5: Occupancy Trends Subset...")
plt.figure(figsize=(12, 7))
sns.lineplot(data=occupancy_agg_subset, x='date', y='occupancy_proportion', hue='market_short', marker='.')
plt.title('Market Occupancy Rate Over Time (Subset)')
plt.xlabel('Date')
plt.ylabel('Occupancy Proportion')
plt.legend(title='Market')
plt.ylim(0, 1) # Standardize y-axis for proportion
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'comp_5_occupancy_trends_subset.png'))
plt.close()

# Plot 6: Occupancy Rate Change (Pre- vs. Post-COVID) (Bar Chart)
print("Generating Plot 6: Occupancy Change Bar Chart...")
plt.figure(figsize=(10, 6))
sns.barplot(data=occ_change, x='Occupancy Pct Point Change (Avg 2021+ vs Avg 2019)', y='Market', palette='coolwarm')
plt.title(f'Occupancy Change: Avg Post-COVID (2021+) vs. Avg Pre-COVID ({pre_covid_year})')
plt.xlabel('Percentage Point Change in Occupancy Rate')
plt.ylabel('Market')
plt.axvline(0, color='grey', linestyle='-', linewidth=0.8)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'comp_6_occupancy_change_bar.png'))
plt.close()

print("\n--- Original TX Plots (For Reference) ---")
# Keep original plots for direct TX comparison if needed
# Filter data for TX only
rent_agg_post_covid_tx = rent_agg_post_covid_expanded[rent_agg_post_covid_expanded['market_short'].isin(['HOU', 'DFW', 'AUS'])]
construction_agg_tx = construction_agg_expanded[construction_agg_expanded['market_short'].isin(['HOU', 'DFW', 'AUS'])]
occupancy_agg_tx = occupancy_agg_subset[occupancy_agg_subset['market_short'].isin(['HOU', 'DFW', 'AUS'])]

# Plot 1 Original: Indexed Rent Growth (TX Only)
print("Generating Original Plot 1: TX Rent Index...")
plt.figure(figsize=(12, 7))
sns.lineplot(data=rent_agg_post_covid_tx, x='date', y='rent_index', hue='market_short', marker='o')
plt.title(f'Indexed Rent Growth (TX Only, Base {post_covid_start_date_dt.strftime("%Y-%m-%d")}=100)')
plt.xlabel('Date')
plt.ylabel('Rent Index (Base 100)')
plt.axhline(100, color='grey', linestyle='--', linewidth=0.8)
plt.legend(title='Market')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'original_1_rent_index_tx.png'))
plt.close()

# Plot 2 Original: Construction Lease Activity (TX Only - Refined Filter)
print("Generating Original Plot 2: TX Construction Leasing...")
plt.figure(figsize=(12, 7))
sns.lineplot(data=construction_agg_tx, x='date', y='leasedsf', hue='market_short', marker='o')
plt.title(f'Quarterly Leased SF ({construction_industry_name}) (TX Only)')
plt.xlabel('Date')
plt.ylabel('Leased Square Footage')
plt.legend(title='Market')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, f'original_2_construction_leasing_tx.png'))
plt.close()

# Plot 3 Original: Occupancy Trends (TX Only)
print("Generating Original Plot 3: TX Occupancy Trends...")
plt.figure(figsize=(12, 7))
sns.lineplot(data=occupancy_agg_tx, x='date', y='occupancy_proportion', hue='market_short', marker='o')
plt.title('Market Occupancy Rate Over Time (TX Only)')
plt.xlabel('Date')
plt.ylabel('Occupancy Proportion')
plt.legend(title='Market')
plt.ylim(0, 1)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'original_3_occupancy_trends_tx.png'))
plt.close()

print("\nComparative Analysis Complete. 6 new plots and 3 original TX plots saved in '../outputs/' directory.")
