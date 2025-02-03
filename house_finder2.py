import googlemaps
import numpy as np

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

    for house in houses:
        transit_stops = fetch_transit_stops(house['location'], radius)
        if not transit_stops:
            continue

        distances = fetch_directions(house['location'], transit_stops, mode)
        if len(distances) >= k:
            knn_distance = np.mean(sorted(distances)[:k])
            house_distances.append({"House_ID": house["id"], "distance": knn_distance})

    return sorted(house_distances, key=lambda x: x["distance"])[:h]
