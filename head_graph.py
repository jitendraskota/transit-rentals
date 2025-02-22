#!/usr/bin/env python
# coding: utf-8

import requests
import pandas as pd
import googlemaps
import pickle as pkl
import time
import house_finder2
import house_finder2_graph
import networkx as nx

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
    #print(radius)
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



def main1(address_list, frequency_list, time_list, radius, limit):

    
    address = address_list[0]
    user_pref_df = pd.DataFrame(list(zip(address_list[1:], frequency_list, time_list)), columns=['Address', 'Frequency', 'Time'])
    user_pref_df.index = [f'up{i}' for i in range(len(user_pref_df))]
    user_pref_df['latitude'] = user_pref_df.Address.map(lambda x: get_lat_lng(x,G_API_KEY)[0])
    user_pref_df['longitude'] = user_pref_df.Address.map(lambda x: get_lat_lng(x,G_API_KEY)[1])
   
    #print("Fetching coordinates...")
    latitude, longitude = get_lat_lng(address, G_API_KEY)


    #print("Fetching rental listings...")
    listings = get_rental_listings(latitude, longitude, radius, limit)
    
    
    #print("Processing listings...")
    rental_df = process_listings(listings)
    rental_df.index = [f'rl{i}' for i in range(len(rental_df))]
    #print("df is:", rental_df)

    #print(rental_df.columns)

    # Initialize an empty graph
    G = nx.Graph()

    # Step 4: Add User Preference Nodes (Type 1 nodes)
    for idx, row in user_pref_df.iterrows():
        node_id = f"up{idx}"  # Assign node label up0, up1, etc.
        # Add node to graph with properties (address, latitude, longitude, etc.)
        G.add_node(node_id, 
                   address=row['Address'], 
                   latitude=row['latitude'], 
                   longitude=row['longitude'], 
                   reach_time=row['Time'], 
                   freq=row['Frequency'])

    # Step 4: Add Rental Listing Nodes (Type 2 nodes)
    for idx, row in rental_df.iterrows():
        node_id = f"rl{idx}"  # Assign node label rl0, rl1, etc.
        # Add node to graph with properties (address, latitude, longitude, etc.)
        G.add_node(node_id, 
                   address=row['formattedAddress'], 
                   latitude=row['latitude'], 
                   longitude=row['longitude'], 
                   price=row['price'], 
                   beds=row['bedrooms'], 
                   baths=row['bathrooms'], 
                   sqft=row['squareFootage'])

    # Display the nodes in the graph to verify
    #print(f"number of Nodes in the graph: {len(G.nodes)}")
    
    # Add edges between user preferences and rental listings
    G = house_finder2_graph.add_edges_to_graph(G, user_pref_df, rental_df)

    # Display the number of edges in the graph
    #print(f"Number of edges in the graph: {len(G.edges)}")

    
    # Example: Get rental recommendations with the applied penalty
    recommended_rentals = house_finder2_graph.get_rental_recommendations(user_pref_df, rental_df, G, penalty_multiplier=1.5)

    # Display the top recommendations
    #print(recommended_rentals.head())
    
    return recommended_rentals
