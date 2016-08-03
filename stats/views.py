from rest_framework.decorators import api_view
import requests


GEOCODING_API_KEY = "AIzaSyD6uu4X9WOw2-hjcFrhooEuev2YBLCgZ_k"


def get_latitude_and_longitude(address):
    params = {'address': address, 'key': GEOCODING_API_KEY}
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
    data = response.json()
    status = data['status'].upper()
    if status == 'OK':
        location = data['results'][0]["geometry"]['location']
        return location['lat'], location['lng']
    elif data['status'] == 'ZERO_RESULTS':
        return None
    else:
        raise ValueError

