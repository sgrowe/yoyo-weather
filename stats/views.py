from rest_framework import serializers
from rest_framework.decorators import api_view
from urllib.parse import quote as url_quote
from statistics import mean, median
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


FORECAST_API_KEY = "edf73a3d61144d6a104356f2b53bf5b9"


def get_forecast_data(latitude, longitude):
    latitude, longitude = url_quote(str(latitude)), url_quote(str(longitude))
    url = 'https://api.forecast.io/forecast/{}/{},{}'.format(FORECAST_API_KEY, latitude, longitude)
    response = requests.get(url)
    if response.status_code == 200:
        return WeatherData(response.json())


class WeatherData:
    def __init__(self, json):
        self.json = json

    def _get_daily_data_for(self, item):
        for day in self.json['daily']['data']:
            yield day[item]

    def _get_stats_for(self, item):
        data = list(self._get_daily_data_for(item))
        return {
            'median': median(data),
            'mean': mean(data),
            'min': min(data),
            'max': max(data),
        }

    def _get_serialised_data_for(self, item):
        return StatisticsSerialiser(data=self._get_stats_for(item))

    def get_serialiser(self):
        data = {
            'humidity': self._get_stats_for('humidity'),
            'temperature': self._get_stats_for('temperatureMax'),
        }
        return WeatherDataSerialiser(data=data)


class StatisticsSerialiser(serializers.Serializer):
    mean = serializers.FloatField()
    median = serializers.FloatField()
    min = serializers.FloatField()
    max = serializers.FloatField()


class WeatherDataSerialiser(serializers.Serializer):
    humidity = StatisticsSerialiser()
    temperature = StatisticsSerialiser()
