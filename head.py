#!/usr/bin/env python
# coding: utf-8

import requests
import pandas as pd
import googlemaps
import pickle as pkl
import time
import house_finder2

# API Keys
API_KEY = "Use-your-key"
G_API_KEY = 'Use-your-key'

# Base URLs
BASE_URL = "https://api.rentcast.io/v1/listings/rental/long-term"

# Headers for Rentcast API
headers = {
    "X-Api-Key": API_KEY
}

def get_lat_lng(address, api_key):
    """
    Get latitude and longitude for a given address using Google Maps API.
    """
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(geocode_url)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            lat = data['results'][0]['geometry']['location']['lat']
            lng = data['results'][0]['geometry']['location']['lng']
            return lat, lng
        else:
            raise ValueError("No results found for the given address.")
    else:
        raise ConnectionError(f"Google Maps API error: {response.status_code} - {response.text}")

def get_rental_listings(latitude, longitude, radius, limit):
    """
    Fetch rental listings using Rentcast API.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "limit": limit
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise ConnectionError(f"Rentcast API error: {response.status_code} - {response.text}")

def process_listings(listings):
    """
    Process raw rental listings into a DataFrame and sort by price.
    """
    df = pd.DataFrame(listings)
    if 'status' in df.columns:
        df = df[df['status'] == 'Active']
    df.sort_values(by='price', inplace=True)
    df = df.rename(columns={'index': 'price_id'})
    return df

def generate_houses_dataframe(df):
    """
    Create a DataFrame with house locations for further analysis.
    """
    df_homes = df[['latitude', 'longitude']]
    houses = [
        {"id": idx, "location": (row['latitude'], row['longitude'])}
        for idx, row in df_homes.iterrows()
    ]
    return houses

def save_houses_to_file(houses, filename='houses.pkl'):
    """
    Save house data to a pickle file.
    """
    with open(filename, 'wb') as f:
        pkl.dump(houses, f)

def evaluate_houses(houses,radius, method='knn', top_n=10):
    """
    Evaluate houses using the specified method from house_finder2.
    """
    print(radius)
    start_time = time.time()
    if method == 'average':
        result = house_finder2.top_houses_by_average(houses, top_n, radius)
    elif method == 'weighted':
        result = house_finder2.top_houses_by_weighted(houses, top_n, radius)
    elif method == 'knn':
        result = house_finder2.top_houses_by_knn(houses, top_n, radius)
    else:
        raise ValueError("Invalid evaluation method. Choose 'average', 'weighted', or 'knn'.")
    end_time = time.time()
    #print(f"Total time for {method}: {end_time - start_time:.2f} seconds")
    return result

def main1(address, radius, limit):
    """
    Main function to handle the workflow:
    - Fetch coordinates.
    - Fetch rental listings.
    - Process listings.
    - Save houses.
    - Evaluate houses.
    """
    print("Fetching coordinates...")
    latitude, longitude = get_lat_lng(address, G_API_KEY)


    print("Fetching rental listings...")
    listings = get_rental_listings(latitude, longitude, radius, limit)

    
    print("Processing listings...")
    df = process_listings(listings)


    print("Generating houses data...")
    houses = generate_houses_dataframe(df)
    save_houses_to_file(houses)
    

    print("Evaluating houses using KNN...")
    knn_top = evaluate_houses(houses, radius, method='knn', top_n=int(limit))

    print("Top few houses based on KNN:")
    knn_best_ids = [x['House_ID'] for x in knn_top]
    knn_df = df.loc[knn_best_ids]

    avg_distance = [x['distance'] for x in knn_top]
    avg_distance = pd.DataFrame(avg_distance)
    knn_df = knn_df.reset_index()
    df_final = pd.concat([knn_df,avg_distance],axis=1)
    df_final=df_final.rename(columns={df_final.columns[-1]:'Distance'})
    return df_final
