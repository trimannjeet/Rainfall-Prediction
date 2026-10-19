import unittest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from fastapi import HTTPException

import main


class PunjabCityLookupTests(unittest.TestCase):
    @patch("main.requests.get")
    def test_resolves_city_in_punjab_india(self, get):
        response = Mock()
        response.json.return_value = {
            "results": [
                {
                    "name": "Ludhiana",
                    "country": "India",
                    "country_code": "IN",
                    "admin1": "Punjab",
                    "latitude": 30.9,
                    "longitude": 75.85,
                }
            ]
        }
        get.return_value = response

        location = main.find_punjab_city("Ludhiana")

        self.assertEqual(location["name"], "Ludhiana")
        self.assertEqual(
            get.call_args.kwargs["params"]["countryCode"],
            "IN",
        )

    @patch("main.requests.get")
    def test_rejects_city_outside_punjab(self, get):
        response = Mock()
        response.json.return_value = {
            "results": [
                {
                    "name": "Delhi",
                    "country_code": "IN",
                    "admin1": "Delhi",
                }
            ]
        }
        get.return_value = response

        with self.assertRaises(HTTPException) as raised:
            main.find_punjab_city("Delhi")

        self.assertEqual(raised.exception.status_code, 404)

    @patch("main.requests.get")
    def test_rejects_malformed_geocoder_location(self, get):
        response = Mock()
        response.json.return_value = {
            "results": [
                {
                    "name": "Unknown",
                    "country_code": None,
                    "admin1": None,
                }
            ]
        }
        get.return_value = response

        with self.assertRaises(HTTPException) as raised:
            main.find_punjab_city("Unknown")

        self.assertEqual(raised.exception.status_code, 404)


class LiveForecastValidationTests(unittest.TestCase):
    def setUp(self):
        main.CITY_CACHE.clear()
        main.FORECAST_CACHE.clear()
        main.PROVIDER_RATE_LIMITED_UNTIL = 0

    @patch("main.requests.get")
    def test_rate_limit_cooldown_prevents_repeated_provider_requests(self, get):
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "60"}
        get.return_value = response

        with self.assertRaises(HTTPException) as first:
            main.fetch_with_retry(main.WEATHER_URL)

        with self.assertRaises(HTTPException) as second:
            main.fetch_with_retry(main.GEOCODING_URL)

        self.assertEqual(first.exception.status_code, 429)
        self.assertEqual(first.exception.headers["Retry-After"], "60")
        self.assertEqual(second.exception.status_code, 429)
        self.assertEqual(get.call_count, 1)

    def test_home_serves_the_dashboard(self):
        response = main.home()

        self.assertEqual(response.path, main.FRONTEND_PATH / "index.html")

    @patch("main.requests.get")
    @patch("main.find_punjab_city")
    def test_tomorrow_forecast_returns_provider_data(
        self,
        find_city,
        get,
    ):
        today = date.today()
        tomorrow = (today + timedelta(days=1)).isoformat()
        find_city.return_value = {
            "name": "Ludhiana",
            "country": "India",
            "latitude": 30.9,
            "longitude": 75.85,
        }
        response = Mock()
        response.json.return_value = {
            "timezone": "Asia/Kolkata",
            "current": {
                "time": f"{today.isoformat()}T12:00",
                "temperature_2m": 25,
                "relative_humidity_2m": 50,
                "apparent_temperature": 26,
                "precipitation": 0,
                "rain": 0,
                "showers": 0,
                "weather_code": 1,
                "wind_speed_10m": 5,
            },
            "daily": {
                "time": [today.isoformat(), tomorrow],
                "precipitation_sum": [0, 2.5],
                "precipitation_probability_max": [0, 60],
                "temperature_2m_max": [25, 24],
                "temperature_2m_min": [15, 14],
                "weather_code": [1, 61],
            },
        }
        get.return_value = response

        result = main.predict_tomorrow(city="Ludhiana")

        self.assertEqual(result["forecast_date"], tomorrow)
        self.assertEqual(result["forecast"]["rainfall_mm"], 2.5)
        self.assertEqual(result["location"]["city"], "Ludhiana")

    @patch("main.requests.get")
    @patch("main.find_punjab_city")
    def test_tomorrow_forecast_rejects_incomplete_provider_data(
        self,
        find_city,
        get,
    ):
        find_city.return_value = {
            "name": "Ludhiana",
            "country": "India",
            "latitude": 30.9,
            "longitude": 75.85,
        }
        response = Mock()
        response.json.return_value = {
            "current": {
                "time": "2026-10-11T12:00",
                "temperature_2m": 25,
                "relative_humidity_2m": 50,
                "apparent_temperature": 26,
                "precipitation": 0,
                "rain": 0,
                "showers": 0,
                "weather_code": 1,
                "wind_speed_10m": 5,
            },
            "daily": {
                "time": ["2026-10-11", "2026-10-12"],
                "precipitation_sum": [0, 1],
                "precipitation_probability_max": [0],
                "temperature_2m_max": [25, 26],
                "temperature_2m_min": [15, 16],
                "weather_code": [1, 61],
            },
        }
        get.return_value = response

        with self.assertRaises(HTTPException) as raised:
            main.predict_tomorrow(city="Ludhiana")

        self.assertEqual(raised.exception.status_code, 502)

    @patch("main.requests.get")
    @patch("main.find_punjab_city")
    def test_weekly_forecast_rejects_unexpected_provider_payload(
        self,
        find_city,
        get,
    ):
        find_city.return_value = {
            "name": "Ludhiana",
            "latitude": 30.9,
            "longitude": 75.85,
        }
        response = Mock()
        response.json.return_value = []
        get.return_value = response

        with self.assertRaises(HTTPException) as raised:
            main.predict_weekly(city="Ludhiana")

        self.assertEqual(raised.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
