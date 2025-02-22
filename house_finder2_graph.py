import googlemaps
import numpy as np
import requests
from datetime import datetime
import time
import pandas as pd

API_KEY = 'Use-your-key'
gmaps = googlemaps.Client(key=API_KEY)

def fetch_transit_stops(location, radius):
    """
    Fetch nearby transit stops for a given location within a specified radius.
    Returns a list of transit stops.
    """
    results = gmaps.places_nearby(location=location, radius=radius, type='transit_station')
    return [result['geometry']['location'] for result in results.get('results', [])]



def fetch_directions(house_location, transit_stops, mode="walking"):
    """
    Fetch directions for a house location to multiple transit stops.
    Returns a list of distances in miles.
    """
    distances = []
    for stop in transit_stops:
        directions = gmaps.directions(house_location, stop, mode=mode)
        if directions:
            distances.append(directions[0]['legs'][0]['distance']['value'] / 1609.34)  # Convert meters to miles
    return distances


def top_houses_by_average(houses, h, radius, mode="walking"):
    house_distances = []

    for house in houses:
        transit_stops = fetch_transit_stops(house['location'], radius)
        if not transit_stops:
            continue

        distances = fetch_directions(house['location'], transit_stops, mode)
        if distances:
            average_distance = sum(distances) / len(distances)
            house_distances.append({"House_ID": house["id"], "distance": average_distance})

    return sorted(house_distances, key=lambda x: x["distance"])[:h]

def top_houses_by_weighted(houses, h, radius, mode="walking"):
    house_distances = []

    for house in houses:
        transit_stops = fetch_transit_stops(house['location'], radius)
        if not transit_stops:
            continue

        distances = fetch_directions(house['location'], transit_stops, mode)
        if distances:
            total_weighted_distance = 0
            total_weight = 0
            for dist in distances:
                weight = 1 / (dist + 0.1)  # Avoid division by zero
                total_weighted_distance += dist * weight
                total_weight += weight

            weighted_distance = total_weighted_distance / total_weight if total_weight > 0 else None
            if weighted_distance is not None:
                house_distances.append({"House_ID": house["id"], "distance": weighted_distance})

    return sorted(house_distances, key=lambda x: x["distance"])[:h]

def top_houses_by_knn(houses, h, radius, k=3, mode="walking"):
    house_distances = []
    radius = radius * 1609.34 #Adding this because rentcast api takes radius in miles and Google API takes radius in meters
    for house in houses:
        transit_stops = fetch_transit_stops(house['location'], radius)
        if not transit_stops:
            continue

        distances = fetch_directions(house['location'], transit_stops, mode)
        if len(distances) >= k:
            knn_distance = np.mean(sorted(distances)[:k])
            house_distances.append({"House_ID": house["id"], "distance": knn_distance})

    return sorted(house_distances, key=lambda x: x["distance"])[:h]


def get_unix_timestamp(time_str):
    if not time_str or time_str.lower() == "now":
        return int(time.time())  # Use current timestamp
    now = datetime.now()
    today_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
    if today_time < now:
        today_time += timedelta(days=1)  # Move to tomorrow if the time has passed
    return int(today_time.timestamp())



# Function to get transit details using latitudes and longitudes
def get_transit_details_using_coords(origin_lat, origin_lng, destination_lat, destination_lng, reach_time):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    
    # Convert the reach_time to a timestamp if it's provided in "HH:MM" format
    if reach_time:
        # Getting the current date and combining with the time
        current_date = datetime.now().strftime("%Y-%m-%d")
        full_time = f"{current_date} {reach_time}"
        reach_timestamp = int(time.mktime(datetime.strptime(full_time, "%Y-%m-%d %H:%M").timetuple()))
    else:
        reach_timestamp = int(time.time()) # Use 'now' if no specific reach_time is not given

    params = {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{destination_lat},{destination_lng}",
        "mode": "transit",  # Public transit mode
        "departure_time": reach_timestamp,
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK':
            # Extract transit details from the response
            legs = data['routes'][0]['legs'][0]
            transit_details = {
                'duration': legs['duration']['value'],  # Travel time in seconds
                'walk_time': legs['steps'][0]['duration']['value'],  # Walk time to/from transit
                'num_stops': len(legs['steps']),
                'num_changes': sum(1 for step in legs['steps'] if 'transit_details' in step)
            }
            return transit_details
        else:
            # If no transit data, return None
            return None
    except Exception as e:
        print(f"Error fetching transit details: {e}")
        return None

# Step 6: Add Edges Using Latitude and Longitude (Handling Missing Data)
def add_edges_to_graph(G, user_pref_df, rental_df):
    for idx_rental, rental_row in rental_df.iterrows():
        rental_coords = (rental_row['latitude'], rental_row['longitude'])
        
        for idx_user, user_row in user_pref_df.iterrows():
            user_coords = (user_row['latitude'], user_row['longitude'])
            reach_time = user_row['Time']  # Time user wants to reach the destination
            
            # Get transit details from rental to user address using coordinates
            transit_details = get_transit_details_using_coords(
                rental_coords[0], rental_coords[1],
                user_coords[0], user_coords[1],
                reach_time
            )
            
            # If transit details are available, add the edge
            if transit_details:
                edge_weight = transit_details['duration'] + transit_details['walk_time']
                availability_flag = "Yes" if transit_details['num_stops'] > 0 else "No"
                
                G.add_edge(f"rl{idx_rental}", f"up{idx_user}", 
                           transit_time=transit_details['duration'], 
                           walk_time=transit_details['walk_time'], 
                           num_stops=transit_details['num_stops'], 
                           num_changes=transit_details['num_changes'], 
                           availability_flag=availability_flag, 
                           weight=edge_weight)
            else:
                # If transit details are unavailable, add edge with "unavailable" flag
                G.add_edge(f"rl{idx_rental}", f"up{idx_user}", 
                           transit_time=None, 
                           walk_time=None, 
                           num_stops=None, 
                           num_changes=None, 
                           availability_flag="Unavailable", 
                           weight=None)
    
    return G



def calculate_utility_score(rental_node, user_pref_df, G, penalty_multiplier=1.5):
    total_score = 0  # This will accumulate the total score
    
    # Initialize variables to keep track of missing transit data
    total_transit_time = 0
    total_cost_penalty = 0
    
    for idx_user, user_row in user_pref_df.iterrows():
        user_node = f"up{idx_user}"
        
        # Check if the edge exists between the rental and the user address
        if G.has_edge(rental_node, user_node):
            edge_data = G[rental_node][user_node]
            
            # Extract transit details from the edge
            transit_time = edge_data.get('transit_time', None)
            availability_flag = edge_data.get('availability_flag', None)
            
            if transit_time is None:
                transit_time = 999999  # If no transit time available, assume it's 0 or use fallback
            
            # If transit is unavailable, apply a penalty
            if availability_flag == "Unavailable":
                total_cost_penalty += penalty_multiplier  # Apply penalty multiplier
                
            # For rentals with public transit available, multiply the transit time by the frequency
            frequency = user_row.get('freq', 1)  # Default to 1 if frequency is not provided
            total_score += frequency/(1+transit_time/60) #changed this
            #total_score += transit_time * frequency
            #print(total_score)

    # Add the penalty cost for rentals with no transit data
    total_score /= total_cost_penalty
    
    # Normalize or adjust the final score if necessary
    normalized_score = total_score / (total_cost_penalty)
    
    return normalized_score


def get_rental_recommendations(user_pref_df, rental_df, G, penalty_multiplier=1.5):
    rental_scores = []
    
    # Calculate utility score for each rental
    for idx_rental, rental_row in rental_df.iterrows():
        rental_node = f"rl{idx_rental}"
        
        # Calculate the utility score for each rental
        score = calculate_utility_score(rental_node, user_pref_df, G, penalty_multiplier)
        
        rental_scores.append((rental_row['formattedAddress'],rental_row['price'], rental_row['bedrooms'],rental_row['bathrooms'], rental_row['squareFootage'], score))
    
    # Sort the rentals by their utility scores (highest score first)
    rental_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Create a DataFrame for the rental recommendations
    recommendations_df = pd.DataFrame(rental_scores, columns=["Address", "Price", "Bedrooms", "Bathrooms", "SquareFootage", "Utility_Score"])
    
    recommendations_df = recommendations_df.sort_values(by='Utility_Score', ascending=False)
    
    return recommendations_df


