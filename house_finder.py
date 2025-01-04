import googlemaps
import numpy as np

# Initialize the Google Maps client
API_KEY = 'YOUR-KEY-HERE'
gmaps = googlemaps.Client(key=API_KEY)

def top_houses_by_average(houses, h, radius=2000, mode="walking"):
    """
    Find the top h houses based on average distance to nearby transit stops.
    """
    house_distances = []

    for house in houses:
        results = gmaps.places_nearby(location=house['location'], radius=radius, type='transit_station')
        transit_stops = [result['geometry']['location'] for result in results['results']]

        if not transit_stops:
            continue

        total_distance = 0
        for stop in transit_stops:
            directions = gmaps.directions(house['location'], stop, mode=mode)
            if directions:
                total_distance += directions[0]['legs'][0]['distance']['value'] / 1609.34

        average_distance = total_distance / len(transit_stops)
        house_distances.append({"House_ID": house["id"], "distance": average_distance})

    # Sort by distance and return the top h houses
    sorted_houses = sorted(house_distances, key=lambda x: x["distance"])[:h]
    return sorted_houses

def top_houses_by_weighted(houses, h, radius=2000, mode="walking"):
    """
    Find the top h houses based on weighted average distance to nearby transit stops.
    """
    house_distances = []

    for house in houses:
        results = gmaps.places_nearby(location=house['location'], radius=radius, type='transit_station')
        transit_stops = [result['geometry']['location'] for result in results['results']]

        if not transit_stops:
            continue

        total_weighted_distance = 0
        total_weight = 0
        for stop in transit_stops:
            directions = gmaps.directions(house['location'], stop, mode=mode)
            if directions:
                distance_miles = directions[0]['legs'][0]['distance']['value'] / 1609.34
                weight = 1 / (distance_miles + 0.1)  # Avoid division by zero
                total_weighted_distance += distance_miles * weight
                total_weight += weight

        weighted_distance = total_weighted_distance / total_weight if total_weight > 0 else None
        if weighted_distance is not None:
            house_distances.append({"House_ID": house["id"], "distance": weighted_distance})

    # Sort by distance and return the top h houses
    sorted_houses = sorted(house_distances, key=lambda x: x["distance"])[:h]
    return sorted_houses

def top_houses_by_knn(houses, h, radius=2000, k=3, mode="walking"):
    """
    Find the top h houses based on K-Nearest Neighbors (KNN) distance to nearby transit stops.
    """
    house_distances = []

    for house in houses:
        results = gmaps.places_nearby(location=house['location'], radius=radius, type='transit_station')
        transit_stops = [result['geometry']['location'] for result in results['results']]

        if not transit_stops:
            continue

        distances = []
        for stop in transit_stops:
            directions = gmaps.directions(house['location'], stop, mode=mode)
            if directions:
                distances.append(directions[0]['legs'][0]['distance']['value'] / 1609.34)

        if len(distances) >= k:
            knn_distance = np.mean(sorted(distances)[:k])
            house_distances.append({"House_ID": house["id"], "distance": knn_distance})

    # Sort by distance and return the top h houses
    sorted_houses = sorted(house_distances, key=lambda x: x["distance"])[:h]
    return sorted_houses

