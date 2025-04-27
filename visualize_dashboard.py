import pandas as pd
import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go
import os
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import numpy as np
from dash.dash_table.Format import Format, Scheme

CLEANED_DIR = os.path.join(os.path.dirname(__file__), 'cleaned_data')

# Load cleaned data
def load_data():
    leases = pd.read_csv(os.path.join(CLEANED_DIR, 'leases_clean.csv'), low_memory=False)
    occupancy = pd.read_csv(os.path.join(CLEANED_DIR, 'major_market_occupancy_clean.csv'))
    price_avail = pd.read_csv(os.path.join(CLEANED_DIR, 'price_and_availability_clean.csv'))
    unemployment = pd.read_csv(os.path.join(CLEANED_DIR, 'unemployment_clean.csv'))
    return leases, occupancy, price_avail, unemployment

leases, occupancy, price_avail, unemployment = load_data()

# --- Custom Style (Google Fonts + CSS) ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Commercial Real Estate Trends - DataFest"

# --- Improved City-to-Metro mapping (expanded, typo-tolerant, includes NYC boroughs and SF/LA suburbs) ---
def get_metro(city):
    city = str(city).strip().lower()
    nyc = ["new york", "manhattan", "brooklyn", "queens", "nyc", "bronx", "staten island"]
    sf = ["san francisco", "sf", "south bay/san jose", "oakland", "san jose", "berkeley", "palo alto", "mountain view", "redwood city", "menlo park", "cupertino", "fremont", "milpitas", "santa clara", "sunnyvale", "san mateo", "foster city", "burlingame", "san bruno", "daly city", "san leandro", "hayward", "union city", "alameda"]
    la = ["los angeles", "beverly hills", "santa monica", "west hollywood", "culver city", "pasadena", "long beach", "glendale", "burbank", "inglewood", "el segundo", "redondo beach", "hermosa beach", "manhattan beach", "hawthorne", "torrance", "gardena", "compton", "carson", "san pedro", "venice", "marina del rey", "malibu", "encino", "sherman oaks", "studio city", "van nuys", "north hollywood", "reseda", "woodland hills", "calabasas", "agoura hills", "thousand oaks"]
    chicago = ["chicago", "evanston", "oak park", "skokie", "naperville", "aurora", "wheaton", "oak brook", "schaumburg", "elgin", "joliet", "arlington heights", "des plaines", "cicero", "berwyn"]
    houston = ["houston", "sugar land", "the woodlands", "katy", "pasadena", "pearland", "baytown"]
    dallas = ["dallas", "fort worth", "plano", "irving", "arlington", "garland", "grand prairie", "mckinney", "frisco", "richardson", "lewisville", "carrollton", "allen", "flower mound"]
    atlanta = ["atlanta", "marietta", "alpharetta", "roswell", "sandy springs", "johns creek", "lawrenceville"]
    dc = ["washington d.c.", "arlington", "alexandria", "bethesda", "silver spring", "rockville", "falls church", "tysons", "mclean"]
    miami = ["miami", "fort lauderdale", "hollywood", "hialeah", "aventura", "coral gables", "miami beach", "doral", "homestead"]
    boston = ["boston", "cambridge", "somerville", "brookline", "newton", "quincy", "waltham", "malden"]
    philly = ["philadelphia", "camden", "cherry hill", "king of prussia", "norristown", "conshohocken", "ardmore"]
    if city in nyc:
        return "NYC Metro"
    if city in sf:
        return "SF Bay Area"
    if city in la:
        return "LA Metro"
    if city in chicago:
        return "Chicago Metro"
    if city in houston:
        return "Houston Metro"
    if city in dallas:
        return "Dallas Metro"
    if city in atlanta:
        return "Atlanta Metro"
    if city in dc:
        return "DC Metro"
    if city in miami:
        return "Miami Metro"
    if city in boston:
        return "Boston Metro"
    if city in philly:
        return "Philadelphia Metro"
    return city.title()
leases_sample = leases.copy()
leases_sample["metro"] = leases_sample["city"].apply(get_metro)

# --- Improved industry cleaning/grouping ---
def clean_industry(ind):
    if not isinstance(ind, str):
        return "Other"
    ind = ind.lower()
    if "tech" in ind or "information" in ind or "software" in ind:
        return "Tech & Info"
    if "finance" in ind or "bank" in ind or "insurance" in ind:
        return "Finance & Insurance"
    if "legal" in ind or "law" in ind:
        return "Legal"
    if "consult" in ind or "business" in ind or "accounting" in ind:
        return "Consulting & Business"
    if "media" in ind or "advertis" in ind:
        return "Media & Advertising"
    if "health" in ind or "hospital" in ind or "medical" in ind:
        return "Healthcare"
    if "manufactur" in ind or "industrial" in ind or "engineering" in ind:
        return "Manufacturing & Engineering"
    if "real estate" in ind:
        return "Real Estate"
    if "retail" in ind:
        return "Retail"
    if "education" in ind:
        return "Education"
    if "non-profit" in ind:
        return "Non-Profit"
    if "restaurant" in ind or "food" in ind:
        return "Food & Hospitality"
    return ind.title() if len(ind) < 30 else "Other"
leases_sample["industry_group"] = leases_sample["internal_industry"].apply(clean_industry)
top_industries = leases_sample["industry_group"].value_counts().nlargest(10).index.tolist()
def industry_group2(ind):
    return ind if ind in top_industries else "Other"
leases_sample["industry_group"] = leases_sample["industry_group"].apply(industry_group2)

# --- 1. Cleaned Industry × Metro Area Table (top 10 metros, top 10 industries, better normalization) ---
metro_industry = leases_sample.groupby(["metro", "industry_group"]).size().reset_index(name="count")
total_by_metro = metro_industry.groupby("metro")["count"].transform("sum")
metro_industry["pct"] = metro_industry["count"] / total_by_metro * 100
pivot_metro = metro_industry.pivot(index="metro", columns="industry_group", values="pct").fillna(0)
top_metros = metro_industry.groupby("metro")["count"].sum().nlargest(10).index.tolist()
pivot_metro = pivot_metro.loc[top_metros, top_industries]

# --- 2. NYC Metro: Pin 300 random cached leases, color by industry ---
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
nyc_leases = leases_sample[leases_sample["metro"] == "NYC Metro"].copy()
# Load geocode cache
geocode_cache_file = "nyc_geocode_cache.csv"
if os.path.exists(geocode_cache_file):
    geocode_cache = pd.read_csv(geocode_cache_file)
else:
    geocode_cache = pd.DataFrame(columns=["address", "lat", "lon"])
# Merge only cached addresses
nyc_leases = nyc_leases.merge(geocode_cache, on="address", how="inner")
# Sample 300 random points for speed and visual clarity
if len(nyc_leases) > 300:
    nyc_leases_sample = nyc_leases.sample(n=300, random_state=42)
else:
    nyc_leases_sample = nyc_leases.copy()
fig_nyc_map = px.scatter_mapbox(
    nyc_leases_sample.dropna(subset=["lat", "lon"]),
    lat="lat", lon="lon", color="industry_group", hover_name="address", hover_data=["company_name", "industry_group"],
    mapbox_style="carto-positron", zoom=10.5, title="NYC Metro: 300 Random Leases by Industry (Pin Map)",
    color_discrete_sequence=px.colors.qualitative.Safe
)
fig_nyc_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, font_family="Inter")

# --- 3. Metro Areas by Commercial Rent (Bar Chart, Indexed, improved grouping) ---
metro_coli = {
    "NYC Metro": 1.25, "LA Metro": 1.18, "Chicago Metro": 1.0, "Houston Metro": 0.95, "Dallas Metro": 0.97,
    "Atlanta Metro": 0.93, "DC Metro": 1.15, "SF Bay Area": 1.27, "Boston Metro": 1.22, "Miami Metro": 1.08,
    # Fallback for others
}
rent_metro = leases_sample.groupby("metro").agg(avg_rent=("overall_rent", "mean"), lease_count=("overall_rent", "count")).reset_index()
rent_metro = rent_metro[rent_metro["lease_count"] > 10]
rent_metro["coli"] = rent_metro["metro"].map(metro_coli).fillna(1.0)
rent_metro["indexed_rent"] = rent_metro["avg_rent"] / rent_metro["coli"]
rent_metro = rent_metro.sort_values("indexed_rent", ascending=False).head(10)
fig_rent_metro = px.bar(rent_metro, x="metro", y="indexed_rent", color="lease_count", title="Metro Areas by Commercial Rent (Cost-of-Living Indexed)", color_continuous_scale="Blues")
fig_rent_metro.update_layout(yaxis_title="Indexed Avg Rent", xaxis_title="Metro Area", font_family="Inter")

# --- 4. Top 10 Metro Areas by Available Space (unchanged) ---
space_metro = leases_sample.groupby("metro")["available_space"].sum().reset_index()
space_metro = space_metro.sort_values("available_space", ascending=False).head(10)
fig_space_metro = px.bar(space_metro, x="metro", y="available_space", title="Top 10 Metro Areas by Total Available Space", template="plotly_white")
fig_space_metro.update_layout(yaxis_title="Total Available Space (sq ft)", xaxis_title="Metro Area", font_family="Inter")

# --- Graphs ---
# 1. Occupancy Crash Around COVID (quarterly, all years) - now by market
occ_q = occupancy.groupby(["year", "quarter", "market"]).agg({"occupancy_proportion": "mean"}).reset_index()
occ_q["year_q"] = occ_q["year"].astype(str) + " " + occ_q["quarter"]
occ_q = occ_q.reset_index(drop=True)
# Assign a unique x_idx for each year_q for x-axis
occ_q["x_idx"] = occ_q.groupby(["year_q"]).ngroup()
fig_occ = px.line(occ_q, x="x_idx", y="occupancy_proportion", color="market", title=None, markers=True, template="plotly_white")
# COVID vertical line at 2020 Q1
if "2020 Q1" in occ_q["year_q"].values:
    covid_idx = int(occ_q[occ_q["year_q"] == "2020 Q1"]["x_idx"].iloc[0])
    fig_occ.add_vline(x=float(covid_idx), line_dash="dash", line_color="red", annotation_text="COVID-19 Pandemic", annotation_position="top left")
else:
    fig_occ.add_vline(x=float(10), line_dash="dash", line_color="red", annotation_text="COVID-19 Pandemic", annotation_position="top left")
fig_occ.update_layout(yaxis_title="Avg Occupancy Proportion", xaxis_title="Quarter", font_family="Inter", title_font_size=24)
# Only show x-ticks for unique year_q
fig_occ.update_xaxes(tickvals=sorted(occ_q["x_idx"].unique()), ticktext=sorted(occ_q["year_q"].unique()))

# 2. Unemployment Trends (all states, monthly)
unemp_m = unemployment.groupby(["year", "month", "state"]).agg({"unemployment_rate": "mean"}).reset_index()
unemp_m["date"] = pd.to_datetime(unemp_m["year"].astype(str) + "-" + unemp_m["month"].astype(str).str.zfill(2) + "-01")
unemp_m["date"] = unemp_m["date"].dt.to_pydatetime()

fig_unemp = px.line(unemp_m, x="date", y="unemployment_rate", color="state", line_group="state", hover_name="state",
                    line_shape="spline", render_mode="svg", template="plotly_white", title=None)
fig_unemp.update_traces(line=dict(width=1), opacity=0.25)
# Highlight US avg and key states
us_avg = unemp_m.groupby("date").agg({"unemployment_rate": "mean"}).reset_index()
# Ensure us_avg["date"] is native datetime
us_avg["date"] = pd.to_datetime(us_avg["date"]).dt.to_pydatetime()
fig_unemp.add_scatter(x=us_avg["date"], y=us_avg["unemployment_rate"], mode="lines", name="US Avg",
                     line=dict(color="#222", width=3))
for st, color in zip(["NY", "CA", "TX", "FL"], ["#0074D9", "#FF4136", "#2ECC40", "#FF851B"]):
    st_data = unemp_m[unemp_m["state"]==st]
    fig_unemp.add_scatter(x=st_data["date"], y=st_data["unemployment_rate"], mode="lines", name=st,
                         line=dict(color=color, width=2))
# Add COVID marker at March 2020 with updated label and style
covid_date = pd.Timestamp("2020-03-01").to_pydatetime()
# Get min/max y for the unemployment rate
unemp_ymin = unemp_m["unemployment_rate"].min()
unemp_ymax = unemp_m["unemployment_rate"].max()
fig_unemp.add_shape(
    type="line",
    x0=covid_date, x1=covid_date,
    y0=unemp_ymin, y1=unemp_ymax,
    line=dict(color="red", width=2, dash="dot"),
)
fig_unemp.add_annotation(
    x=covid_date, y=unemp_ymax,
    text="COVID-19 Pandemic",
    showarrow=False,
    font=dict(color="red", size=12),
    xanchor="left", yanchor="top"
)
fig_unemp.update_layout(
    yaxis_title="Unemployment Rate (%)",
    xaxis_title="Date",
    font_family="Inter",
    legend_title_text="State",
    showlegend=True,
    xaxis=dict(
        tickformat="%Y-%b",
        tickmode="auto",
        range=[pd.Timestamp('2018-01-01').to_pydatetime(), pd.Timestamp('2024-12-31').to_pydatetime()]
    )
)

# 3. Manhattan vs Other Regions (Average Leased Space)
# Calculate average leased space per region per year
if 'leasing' in price_avail.columns and 'region' in price_avail.columns:
    region_leased = price_avail.groupby(["region", "year"]).agg({"leasing": "mean"}).reset_index()
    fig_manh = px.bar(region_leased, x="year", y="leasing", color="region", barmode="group", template="plotly_white",
                     title="Average Leased Space per Region")
    fig_manh.update_layout(yaxis_title="Avg Leased Space (sq ft)", xaxis_title="Year", font_family="Inter", legend_title_text="Region")
else:
    fig_manh = px.bar(title="Average Leased Space per Region (Data Missing)")

# 4. Correlation: Overlay Occupancy vs Unemployment (US Avg)
# Align by quarter/year (since occupancy data is quarterly)
occ_quarterly = occupancy.groupby(["year", "quarter"]).agg({"occupancy_proportion": "mean"}).reset_index()
# Create a date for each quarter for merging
quarter_map = {"Q1": "01", "Q2": "04", "Q3": "07", "Q4": "10"}
occ_quarterly["date"] = pd.to_datetime(occ_quarterly["year"].astype(str) + "-" + occ_quarterly["quarter"].map(quarter_map) + "-01")

fig_corr = px.line(occ_quarterly, x="date", y="occupancy_proportion", line_group="year", hover_name="year",
                    line_shape="spline", render_mode="svg", template="plotly_white", title=None)
fig_corr.update_traces(line=dict(width=1), opacity=0.25)
# Highlight US avg and key states
us_avg = occ_quarterly.groupby("date").agg({"occupancy_proportion": "mean"}).reset_index()
# Ensure us_avg["date"] is native datetime
us_avg["date"] = pd.to_datetime(us_avg["date"]).dt.to_pydatetime()
fig_corr.add_scatter(x=us_avg["date"], y=us_avg["occupancy_proportion"], mode="lines", name="US Avg",
                     line=dict(color="#222", width=3))
# Add COVID marker at March 2020 with updated label and style
covid_date = pd.Timestamp("2020-03-01").to_pydatetime()
# Get min/max y for the correlation plot
corr_ymin = occ_quarterly["occupancy_proportion"].min()
corr_ymax = occ_quarterly["occupancy_proportion"].max()
fig_corr.add_shape(
    type="line",
    x0=covid_date, x1=covid_date,
    y0=corr_ymin, y1=corr_ymax,
    line=dict(color="red", width=2, dash="dot"),
)
fig_corr.add_annotation(
    x=covid_date, y=corr_ymax,
    text="COVID-19 Pandemic",
    showarrow=False,
    font=dict(color="red", size=12),
    xanchor="left", yanchor="top"
)
fig_corr.update_layout(
    yaxis_title="Occupancy Proportion (%)",
    xaxis_title="Date",
    font_family="Inter",
    legend_title_text="Year",
    showlegend=True,
    xaxis=dict(
        tickformat="%Y-%b",
        tickmode="auto",
        range=[pd.Timestamp('2018-01-01').to_pydatetime(), pd.Timestamp('2024-12-31').to_pydatetime()]
    )
)

# 5. Leasing Activity by Quarter (Sun Belt vs Legacy)
leases["region"] = leases["state"].map(lambda s: "Sun Belt" if s in ["TX", "FL", "GA", "AZ", "NC", "SC", "TN", "NV", "AL", "OK", "AR", "LA", "MS"] else ("Legacy" if s in ["NY", "IL", "CA", "MA", "NJ", "PA", "OH", "MI"] else "Other"))
lease_q = leases.groupby(["year", "quarter", "region"]).agg({"leasing": "sum"}).reset_index()
lease_q["year_q"] = lease_q["year"].astype(str) + " " + lease_q["quarter"]
# Use integer index for x and set tick labels
lease_q = lease_q.reset_index(drop=True)
lease_q["x_idx"] = lease_q.index.astype(int)
fig_lease = px.line(lease_q, x="x_idx", y="leasing", color="region", markers=True, template="plotly_white")
if "2020 Q1" in lease_q["year_q"].values:
    covid_idx = int(lease_q[lease_q["year_q"] == "2020 Q1"]["x_idx"].iloc[0])
    fig_lease.add_vline(x=float(covid_idx), line_dash="dash", line_color="red", annotation_text="COVID-19", annotation_position="top left")
else:
    fig_lease.add_vline(x=float(10), line_dash="dash", line_color="red", annotation_text="COVID-19", annotation_position="top left")
fig_lease.update_layout(yaxis_title="Leasing Activity (sq ft)", xaxis_title="Quarter", font_family="Inter", legend_title_text="Region")
fig_lease.update_xaxes(tickvals=lease_q["x_idx"].tolist(), ticktext=lease_q["year_q"].tolist())

# 6. Migration Story: Net Leasing Change (Sun Belt vs Legacy)
pre = lease_q[lease_q["year"] < 2020].groupby("region")["leasing"].mean()
post = lease_q[lease_q["year"] >= 2020].groupby("region")["leasing"].mean()
change = (post - pre).reset_index()
change.columns = ["region", "net_change"]
fig_migration = px.bar(change, x="region", y="net_change", color="region", template="plotly_white")
fig_migration.update_layout(yaxis_title="Net Change in Leasing Activity (Post-COVID vs Pre-COVID)", font_family="Inter", showlegend=False)

# 7. Occupancy Heatmap (by market, quarter, year)
heat = occupancy.pivot_table(index="quarter", columns="year", values="occupancy_proportion", aggfunc="mean")
fig_heatmap = px.imshow(heat, labels=dict(x="Year", y="Quarter", color="Avg Occupancy Proportion"),
                    title=None, aspect="auto", color_continuous_scale="Blues", template="plotly_white")
fig_heatmap.update_layout(font_family="Inter")

# 8. Placeholder for External Data Overlay
def make_external_overlay():
    return dcc.Graph(figure=px.line(title="External Overlay Placeholder"),
                     style={"height": 400, "marginTop": 30})

# --- Graphs for Second Tab: Regional Winners & Losers ---
# 1. Occupancy rebound: Sunbelt vs Coastal cities since 2020
sunbelt_cities = ["Austin", "Dallas/Ft Worth", "Houston", "Atlanta", "Charlotte", "Nashville"]
coastal_cities = ["Manhattan", "Los Angeles", "San Francisco", "South Bay/San Jose", "Philadelphia", "Washington D.C."]
occ_since_2020 = occupancy[occupancy["year"] >= 2020]
occ_cities = occ_since_2020[occ_since_2020["market"].isin(sunbelt_cities + coastal_cities)].copy()
occ_cities["city_group"] = occ_cities["market"].apply(lambda x: "Sunbelt" if x in sunbelt_cities else "Coastal")
occ_cities["year_q"] = occ_cities["year"].astype(str) + " " + occ_cities["quarter"]
occ_cities = occ_cities.sort_values(["market", "year", "quarter"])
fig_occ_cities = px.line(occ_cities, x="year_q", y="occupancy_proportion", color="market", line_dash="city_group",
                        title="Occupancy Rebound: Sunbelt vs Coastal Cities (2020+)", markers=True, template="plotly_white")
fig_occ_cities.update_layout(yaxis_title="Occupancy Proportion", xaxis_title="Quarter", font_family="Inter", legend_title_text="Market")

# --- Update Tab 2 Layout ---
# Layout with Tabs for Multipage Story
app.layout = dbc.Container([
    html.H1("Commercial Real Estate Trends Dashboard", style={"textAlign": "center", "marginTop": 20}),
    dcc.Tabs(id="story-tabs", value="tab-1", children=[
        dcc.Tab(label="Shock & Macro Trends", value="tab-1"),
        dcc.Tab(label="Regional Winners & Losers", value="tab-2"),
        dcc.Tab(label="Connections & Correlations", value="tab-3"),
        dcc.Tab(label="Job & Industry Insights", value="tab-4"),
    ], colors={"border": "#ddd", "primary": "#17BECF", "background": "#f9f9f9"}),
    html.Div(id="tab-content", style={"marginTop": 30}),
], fluid=True, style={"backgroundColor": "#f9f9f9", "color": "#222", "minHeight": "100vh"})

@app.callback(Output("tab-content", "children"), [Input("story-tabs", "value")])
def render_content(tab):
    if tab == "tab-1":
        return html.Div([
            html.H2("Shock & Macro Trends", style={"color": "#17BECF"}),
            dcc.Graph(figure=fig_occ),
            dcc.Graph(figure=fig_unemp),
            dcc.Graph(figure=fig_heatmap),
        ])
    elif tab == "tab-2":
        return html.Div([
            html.H2("Regional Winners & Losers", style={"color": "#17BECF"}),
            dcc.Graph(figure=fig_occ_cities),
            dcc.Graph(figure=fig_lease),
            dcc.Graph(figure=fig_migration),
        ])
    elif tab == "tab-3":
        return html.Div([
            html.H2("Connections & Correlations", style={"color": "#17BECF"}),
            dcc.Graph(figure=fig_corr),
            make_external_overlay(),
            dcc.Graph(figure=fig_heatmap),
        ])
    elif tab == "tab-4":
        return html.Div([
            html.H2("Job & Industry Insights", style={"color": "#17BECF"}),
            html.H4("Industry Distribution by Metro Area"),
            dash_table.DataTable(
                data=pivot_metro.reset_index().to_dict('records'),
                columns=[{"name": col, "id": col, "type": "numeric" if col != "metro" else "text", "format": Format(precision=1, scheme=Scheme.fixed)} for col in pivot_metro.reset_index().columns],
                style_data_conditional=[
                    {
                        'if': {'filter_query': f'{{{col}}} >= 30', 'column_id': col},
                        'backgroundColor': '#003366', 'color': 'white'
                    } if col != "metro" else {} for col in pivot_metro.columns
                ] + [
                    {
                        'if': {'filter_query': f'{{{col}}} >= 15 && {{{col}}} < 30', 'column_id': col},
                        'backgroundColor': '#6699cc', 'color': 'black'
                    } if col != "metro" else {} for col in pivot_metro.columns
                ] + [
                    {
                        'if': {'filter_query': f'{{{col}}} > 0 && {{{col}}} < 15', 'column_id': col},
                        'backgroundColor': '#cce0ff', 'color': 'black'
                    } if col != "metro" else {} for col in pivot_metro.columns
                ],
                style_table={'overflowX': 'auto'},
                style_cell={"minWidth": 90, "maxWidth": 200, "whiteSpace": "normal"},
                page_size=10,
            ),
            html.H4("NYC Metro: 300 Random Leases by Industry (Pin Map)"),
            dcc.Graph(figure=fig_nyc_map),
            html.H4("Metro Areas by Commercial Rent (Indexed)"),
            dcc.Graph(figure=fig_rent_metro),
            html.H4("Top 10 Metro Areas by Available Space"),
            dcc.Graph(figure=fig_space_metro),
        ])
    else:
        return html.Div("Select a story tab to begin.")

if __name__ == "__main__":
    app.run(debug=True, port=8051)
