from unittest import skip
from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from stats.views import get_latitude_and_longitude, WeatherData, get_forecast_data


class GeocodingTests(TestCase):
    def test_get_latitude_and_longitude_returns_correct_data(self):
        address = 'Eiffel Tower, Paris'  # Something that won't move anytime soon
        expected_latitude = 48.8584  # from wikipedia: https://en.wikipedia.org/wiki/Eiffel_Tower
        expected_longitude = 2.2945
        lat, long = get_latitude_and_longitude(address)
        self.assertAlmostEqual(lat, expected_latitude, places=4)
        self.assertAlmostEqual(long, expected_longitude, places=4)

    def test_get_latitude_and_longitude_returns_none_if_address_invalid(self):
        address = "lskjflkfjhsdlk"
        self.assertIsNone(get_latitude_and_longitude(address))


class WeatherDataTests(TestCase):
    def test_calculates_correct_statistics(self):
        data = {
            'daily': {
                'data': [{'humidity': h} for h in [47.5, 13.2, 20.6]],
            }
        }
        weather_data = WeatherData(data)
        stats = weather_data._get_stats_for('humidity')
        self.assertAlmostEqual(stats['mean'], 27.1)
        self.assertEqual(stats['min'], 13.2)
        self.assertEqual(stats['max'], 47.5)
        self.assertEqual(stats['median'], 20.6)

    def test_returns_valid_serialised_data(self):
        data = {
            'daily': {
                'data': [{'humidity': h, 'temperatureMax': t} for h, t in [(47.5, 21.0), (13.2, 4.5), (20.6, 33.3)]],
            }
        }
        weather_data = WeatherData(data)
        serialiser = weather_data.get_serialiser()
        self.assertTrue(serialiser.is_valid())


class GetForecastDataTests(TestCase):
    def test_returns_weather_data_object(self):
        data = get_forecast_data(37.8267, -122.423)
        self.assertIsInstance(data, WeatherData)


class TestWeatherStatisticsView(APITestCase):
    def test_returns_statistics_without_error(self):
        url = reverse('weather')
        url += '?city=Paris&period=day'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('median', response.data['humidity'])
