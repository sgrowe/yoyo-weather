from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException, ParseError
from rest_framework.response import Response
from django.views.generic.base import TemplateView
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
        raise ValueError("Could not fetch latitude and longitude of address.", address)


FORECAST_API_KEY = "edf73a3d61144d6a104356f2b53bf5b9"


def get_forecast_data(latitude, longitude):
    latitude, longitude = url_quote(str(latitude)), url_quote(str(longitude))
    url = 'https://api.forecast.io/forecast/{}/{},{}'.format(FORECAST_API_KEY, latitude, longitude)
    response = requests.get(url)
    if response.status_code == 200:
        return WeatherData(response.json())
    else:
        raise ValueError('Could not fetch weather forecast.', latitude, longitude, response)


class WeatherData:
    time_periods = {
        'week': 'daily',
        'day': 'hourly',
        'hour': 'minutely',
    }

    def __init__(self, json):
        self.json = json

    def _get_stats_for(self, period, item):
        try:
            data_for_period = self.json[period]['data']
        except KeyError:
            raise APIException(detail="The requested time period is not currently availalble.")
        if period == 'hourly':
            # Api returns two days worth of hourly data so only take the first half
            half_len = len(data_for_period) // 2
            data_for_period = data_for_period[:half_len]
        data = [x[item] for x in data_for_period]
        times = [x['time'] for x in data_for_period]
        return {
            'median': median(data),
            'mean': mean(data),
            'min': min(data),
            'max': max(data),
            'raw_values': data,
            'times': times,
        }

    def _get_serialised_data_for(self, period, item):
        return StatisticsSerialiser(data=self._get_stats_for(period, item))

    def get_serialiser(self, period):
        try:
            time_period = self.time_periods[period.lower()]
        except KeyError:
            raise ParseError(detail='"{}" is not a supported time period, only week, day and hour are allowed.')
        temperature = 'temperatureMax' if time_period == 'daily' else 'temperature'
        data = {
            'humidity': self._get_stats_for(time_period, 'humidity'),
            'temperature': self._get_stats_for(time_period, temperature),
        }
        return WeatherDataSerialiser(data=data)


class StatisticsSerialiser(serializers.Serializer):
    mean = serializers.FloatField()
    median = serializers.FloatField()
    min = serializers.FloatField()
    max = serializers.FloatField()
    raw_values = serializers.ListField(serializers.FloatField())
    times = serializers.ListField(serializers.IntegerField())


class WeatherDataSerialiser(serializers.Serializer):
    humidity = StatisticsSerialiser()
    temperature = StatisticsSerialiser()


@api_view()
def weather_statistics(request):
    city = request.query_params['city']
    period = request.query_params['period']
    location = get_latitude_and_longitude(city)
    if location is None:
        raise UnknownAddress()
    weather_data = get_forecast_data(*location)
    return Response(weather_data.get_serialiser(period).initial_data)


class UnknownAddress(APIException):
    status_code = 503
    default_detail = 'That address does not exist.'


class HomePageView(TemplateView):
    template_name = "home.html"
