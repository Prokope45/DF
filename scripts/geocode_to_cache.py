import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import os

# Path to input addresses and output cache
ADDR_FILE = 'cleaned_data/leases_clean.csv'
CACHE_FILE = 'nyc_geocode_cache.csv'

# Load all unique NYC addresses
leases = pd.read_csv(ADDR_FILE)
nyc_cities = ["new york", "manhattan", "brooklyn", "queens", "nyc", "bronx", "staten island"]
leases_nyc = leases[leases['city'].str.lower().isin(nyc_cities)]
addresses = leases_nyc['address'].dropna().unique()

# Load or initialize cache
if os.path.exists(CACHE_FILE):
    cache = pd.read_csv(CACHE_FILE)
else:
    cache = pd.DataFrame(columns=['address', 'lat', 'lon'])

cached_addresses = set(cache['address'])
todo = [addr for addr in addresses if addr not in cached_addresses]

if not todo:
    print('All addresses already cached!')
    exit(0)

geolocator = Nominatim(user_agent='df_static_cache')
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2, max_retries=1, error_wait_seconds=10, swallow_exceptions=True)

new_rows = []
for i, addr in enumerate(todo):
    q = f"{addr}, New York, NY"
    loc = geocode(q)
    if loc:
        print(f"{i+1}/{len(todo)}: {addr} -> ({loc.latitude}, {loc.longitude})")
        new_rows.append({'address': addr, 'lat': loc.latitude, 'lon': loc.longitude})
    else:
        print(f"{i+1}/{len(todo)}: {addr} -> NOT FOUND")
    # Optionally save every 10 results
    if (i+1) % 10 == 0:
        cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
        cache.to_csv(CACHE_FILE, index=False)
        new_rows = []

if new_rows:
    cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
    cache.to_csv(CACHE_FILE, index=False)

print(f"Done. Cached {len(cache)} addresses.")
