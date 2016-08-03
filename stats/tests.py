from django.test import TestCase
from stats.views import get_latitude_and_longitude


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
