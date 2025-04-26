import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Load the real data
def load_data():
    # Load data files
    leases_df = pd.read_csv('Leases.csv')
    occupancy_df = pd.read_csv('Major Market Occupancy Data.csv')
    price_df = pd.read_csv('Price and Availability Data.csv')
    unemployment_df = pd.read_csv('Unemployment.csv')
    
    # Print data info for debugging
    print("Loaded data shapes:")
    print(f"Leases: {leases_df.shape}")
    print(f"Occupancy: {occupancy_df.shape}")
    print(f"Price: {price_df.shape}")
    print(f"Unemployment: {unemployment_df.shape}")
    
    # Create date columns - using a more robust method
    def create_date(row):
        year = str(row['year'])
        quarter = str(row['quarter']).replace('Q', '')
        month = str((int(quarter) - 1) * 3 + 1).zfill(2)
        return pd.to_datetime(f"{year}-{month}-01")
    
    leases_df['date'] = leases_df.apply(create_date, axis=1)
    occupancy_df['date'] = occupancy_df.apply(create_date, axis=1)
    price_df['date'] = price_df.apply(create_date, axis=1)
    unemployment_df['date'] = unemployment_df.apply(create_date, axis=1)
    
    # Calculate moving averages for occupancy
    # First sort by date for each market
    occupancy_df = occupancy_df.sort_values(['market', 'date'])
    # Calculate 2-year (8 quarters) moving average
    occupancy_df['occupancy_ma_2y'] = occupancy_df.groupby('market')['occupancy_proportion'].transform(
        lambda x: x.rolling(window=8, min_periods=1).mean()
    )
    # Calculate 3-year (12 quarters) moving average
    occupancy_df['occupancy_ma_3y'] = occupancy_df.groupby('market')['occupancy_proportion'].transform(
        lambda x: x.rolling(window=12, min_periods=1).mean()
    )
    
    # Print unique markets for debugging
    print("\nUnique markets in each dataset:")
    print("Leases markets:", sorted(leases_df['market'].unique()))
    print("Occupancy markets:", sorted(occupancy_df['market'].unique()))
    print("Price markets:", sorted(price_df['market'].unique()))
    print("Unemployment states:", sorted(unemployment_df['state'].unique()))
    
    # Aggregate unemployment data by market (state)
    unemployment_df = unemployment_df.groupby(['date', 'state'])['unemployment_rate'].mean().reset_index()
    unemployment_df = unemployment_df.rename(columns={'state': 'market'})
    
    return leases_df, occupancy_df, price_df, unemployment_df

# Load all data
leases_df, occupancy_df, price_df, unemployment_df = load_data()

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Layout
app.layout = dbc.Container([
    html.H1("Commercial Real Estate Market Analysis 2025", className="text-center my-4"),
    html.H5("Interactive Dashboard for Office Location Decision", className="text-center mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.H6("Select Date Range:"),
            dcc.DatePickerRange(
                id='date-range',
                start_date=price_df['date'].min(),
                end_date=price_df['date'].max(),
                display_format='YYYY-MM-DD'
            ),
        ], width=12, className="mb-4"),
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='price-trends'),
        ], width=6),
        dbc.Col([
            dcc.Graph(id='occupancy-rates'),
            dcc.RadioItems(
                id='occupancy-view',
                options=[
                    {'label': 'Raw Data', 'value': 'raw'},
                    {'label': '2-Year Moving Average', 'value': '2y'},
                    {'label': '3-Year Moving Average', 'value': '3y'}
                ],
                value='raw',
                inline=True,
                className="mt-2"
            ),
        ], width=6),
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='lease-activity'),
        ], width=6),
        dbc.Col([
            dcc.Graph(id='unemployment-trends'),
        ], width=6),
    ]),
    
    html.Div([
        html.H4("Market Insights", className="text-center my-4"),
        html.Div(id='market-insights', className="list-group")
    ], className="mt-4")
])

# Callbacks
@app.callback(
    [Output('price-trends', 'figure'),
     Output('occupancy-rates', 'figure'),
     Output('lease-activity', 'figure'),
     Output('unemployment-trends', 'figure'),
     Output('market-insights', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('occupancy-view', 'value')]
)
def update_graphs(start_date, end_date, occupancy_view):
    print(f"\nUpdating graphs for date range: {start_date} to {end_date}")
    
    # Filter data based on date range
    mask = (price_df['date'] >= start_date) & (price_df['date'] <= end_date)
    price_filtered = price_df[mask]
    
    mask = (occupancy_df['date'] >= start_date) & (occupancy_df['date'] <= end_date)
    occupancy_filtered = occupancy_df[mask]
    
    mask = (leases_df['date'] >= start_date) & (leases_df['date'] <= end_date)
    leases_filtered = leases_df[mask]
    
    mask = (unemployment_df['date'] >= start_date) & (unemployment_df['date'] <= end_date)
    unemployment_filtered = unemployment_df[mask]
    
    # Create figures
    # Price trends
    price_agg = price_filtered.groupby(['date', 'market'])['overall_rent'].mean().reset_index()
    
    price_fig = px.line(price_agg, 
                       x='date', 
                       y='overall_rent',
                       color='market',
                       title='Average Rent Price Trends by Market')
    price_fig.update_layout(yaxis_title='Price per Square Foot ($)')
    
    # Occupancy rates with moving average options
    if occupancy_view == 'raw':
        y_col = 'occupancy_proportion'
        title_suffix = 'Raw Data'
    elif occupancy_view == '2y':
        y_col = 'occupancy_ma_2y'
        title_suffix = '2-Year Moving Average'
    else:
        y_col = 'occupancy_ma_3y'
        title_suffix = '3-Year Moving Average'
        
    occupancy_fig = px.line(occupancy_filtered,
                           x='date',
                           y=y_col,
                           color='market',
                           title=f'Occupancy Rates by Market ({title_suffix})')
    occupancy_fig.update_layout(yaxis_title='Occupancy Rate')
    
    # Lease activity
    lease_agg = leases_filtered.groupby('market')['leasedSF'].sum().reset_index()
    
    lease_fig = px.bar(lease_agg,
                      x='market',
                      y='leasedSF',
                      title='Total Leased Space by Market')
    lease_fig.update_layout(yaxis_title='Total Leased Space (sq ft)')
    
    # Unemployment trends
    unemployment_fig = px.line(unemployment_filtered,
                             x='date',
                             y='unemployment_rate',
                             color='market',
                             title='Unemployment Trends by Market')
    unemployment_fig.update_layout(yaxis_title='Unemployment Rate (%)')
    
    # Generate insights
    latest_date = price_filtered['date'].max()
    
    # Calculate key metrics
    avg_prices = price_filtered[price_filtered['date'] == latest_date].groupby('market')['overall_rent'].mean()
    
    # Use the selected occupancy view for insights
    if occupancy_view == 'raw':
        avg_occupancy = occupancy_filtered[occupancy_filtered['date'] == latest_date].groupby('market')['occupancy_proportion'].mean()
    elif occupancy_view == '2y':
        avg_occupancy = occupancy_filtered[occupancy_filtered['date'] == latest_date].groupby('market')['occupancy_ma_2y'].mean()
    else:
        avg_occupancy = occupancy_filtered[occupancy_filtered['date'] == latest_date].groupby('market')['occupancy_ma_3y'].mean()
    
    total_leases = leases_filtered.groupby('market')['leasedSF'].sum()
    
    # Find best markets
    best_price_market = avg_prices.idxmin() if not avg_prices.empty else "No data"
    best_occupancy_market = avg_occupancy.idxmax() if not avg_occupancy.empty else "No data"
    most_active_market = total_leases.idxmax() if not total_leases.empty else "No data"
    
    insights = [
        html.Li(f"Most Affordable Market: {best_price_market} (${avg_prices[best_price_market]:.2f}/sq ft)" if best_price_market != "No data" else "No price data available", 
               className="list-group-item"),
        html.Li(f"Highest Occupancy: {best_occupancy_market} ({avg_occupancy[best_occupancy_market]:.1%})" if best_occupancy_market != "No data" else "No occupancy data available", 
               className="list-group-item"),
        html.Li(f"Most Active Market: {most_active_market} ({total_leases[most_active_market]:,.0f} sq ft)" if most_active_market != "No data" else "No lease data available", 
               className="list-group-item"),
    ]
    
    return price_fig, occupancy_fig, lease_fig, unemployment_fig, insights

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
