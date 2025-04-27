import pandas as pd
import numpy as np
import os
from typing import List

DATA_DIR = os.path.join(os.path.dirname(__file__), 'DF', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'cleaned_data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper to clean column names
def clean_columns(df):
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace(r'["\']', '', regex=True)
    )
    return df

def clean_major_market_occupancy():
    path = os.path.join(DATA_DIR, 'Major Market Occupancy Data.csv')
    df = pd.read_csv(path)
    df = clean_columns(df)
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    df.to_csv(os.path.join(OUTPUT_DIR, 'major_market_occupancy_clean.csv'), index=False)
    return df

def clean_price_and_availability():
    path = os.path.join(DATA_DIR, 'Price and Availability Data.csv')
    df = pd.read_csv(path)
    df = clean_columns(df)
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    df.to_csv(os.path.join(OUTPUT_DIR, 'price_and_availability_clean.csv'), index=False)
    return df

def clean_unemployment():
    path = os.path.join(DATA_DIR, 'Unemployment.csv')
    df = pd.read_csv(path)
    df = clean_columns(df)
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    df.to_csv(os.path.join(OUTPUT_DIR, 'unemployment_clean.csv'), index=False)
    return df

def clean_leases(chunk_size=100000):
    path = os.path.join(DATA_DIR, 'Leases.csv')
    cleaned_chunks = []
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        chunk = clean_columns(chunk)
        chunk = chunk.drop_duplicates()
        chunk = chunk.dropna(how='all')
        cleaned_chunks.append(chunk)
    df = pd.concat(cleaned_chunks, ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, 'leases_clean.csv'), index=False)
    return df

def main():
    print('Cleaning Major Market Occupancy Data...')
    clean_major_market_occupancy()
    print('Cleaning Price and Availability Data...')
    clean_price_and_availability()
    print('Cleaning Unemployment Data...')
    clean_unemployment()
    print('Cleaning Leases Data (chunked)...')
    clean_leases()
    print('All datasets cleaned and saved to cleaned_data/')

if __name__ == '__main__':
    main()
