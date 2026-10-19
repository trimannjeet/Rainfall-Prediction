import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

import main


class OfflineHistoricalEstimateTests(unittest.TestCase):
    def setUp(self):
        self.observations = [
            (date(2022, 7, 1), 0.0),
            (date(2023, 7, 1), 3.0),
            (date(2024, 7, 1), 6.0),
            (date(2022, 7, 2), 50.0),
        ]
        self.all_observations = {
            district: list(self.observations)
            for district, *_ in main.DISTRICTS
        }

    def test_tomorrow_estimate_uses_matching_calendar_days(self):
        with (
            patch("main.india_today", return_value=date(2026, 6, 30)),
            patch(
                "main.load_historical_rainfall",
                return_value=self.all_observations,
            ),
        ):
            result = main.predict_tomorrow(city="Ludhiana")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], main.DATASET_PATH.name)
        self.assertEqual(result["forecast_date"], "2026-07-01")
        self.assertEqual(result["forecast"]["rainfall_mm"], 3.0)
        self.assertEqual(
            result["forecast"]["precipitation_probability_percent"],
            67,
        )
        self.assertEqual(result["forecast"]["sample_count"], 3)
        self.assertEqual(result["location"]["district"], "Ludhiana")
        self.assertIsNone(result["current_conditions"]["temperature_c"])
        self.assertIn("not a live forecast", result["note"])

    def test_all_punjab_districts_and_headquarters_resolve(self):
        districts = main.list_districts()["districts"]
        self.assertEqual(len(districts), 23)
        self.assertEqual(
            main.resolve_district("Mohali")["district"],
            "Sahibzada Ajit Singh Nagar",
        )
        self.assertEqual(
            main.resolve_district("Ropar")["district"],
            "Rupnagar",
        )

    def test_tomorrow_estimate_selects_requested_district(self):
        with (
            patch("main.india_today", return_value=date(2026, 6, 30)),
            patch(
                "main.load_historical_rainfall",
                return_value=self.all_observations,
            ),
        ):
            result = main.predict_tomorrow(city="Amritsar")

        self.assertEqual(result["location"]["district"], "Amritsar")
        self.assertEqual(result["location"]["city"], "Amritsar")

    def test_weekly_endpoint_returns_next_seven_offline_estimates(self):
        with (
            patch("main.india_today", return_value=date(2026, 6, 30)),
            patch(
                "main.load_historical_rainfall",
                return_value=self.all_observations,
            ),
        ):
            result = main.predict_weekly(city="Moga")

        forecasts = result["daily_forecasts"]
        self.assertEqual(len(forecasts), 7)
        self.assertEqual(forecasts[0]["date"], "2026-07-01")
        self.assertEqual(forecasts[-1]["date"], "2026-07-07")
        self.assertEqual(
            forecasts[0]["estimate_method"],
            "matching calendar day",
        )
        self.assertTrue(
            all(
                item["estimate_method"] == "calendar month"
                for item in forecasts[2:]
            )
        )

    def test_february_29_uses_month_history_when_no_matching_day(self):
        estimate = main.estimate_rainfall(
            date(2024, 2, 29),
            [
                (date(2022, 2, 1), 2.0),
                (date(2023, 2, 2), 4.0),
                (date(2022, 3, 1), 100.0),
            ],
        )

        self.assertEqual(estimate["rainfall_mm"], 3.0)
        self.assertEqual(estimate["sample_count"], 2)
        self.assertEqual(estimate["estimate_method"], "calendar month")

    def test_rejects_location_outside_punjab_district_list(self):
        with self.assertRaises(HTTPException) as raised:
            main.predict_tomorrow(city="Delhi")

        self.assertEqual(raised.exception.status_code, 404)
        self.assertIn("23 listed districts", raised.exception.detail)

    def test_loads_included_historical_dataset(self):
        observations = main.load_historical_rainfall()

        self.assertEqual(len(observations), 23)
        for district_observations in observations.values():
            self.assertEqual(len(district_observations), 1461)
            self.assertIsInstance(district_observations[0][0], date)
            self.assertGreaterEqual(district_observations[0][1], 0)

    def test_monthly_analytics_uses_local_dataset(self):
        result = main.monthly_rainfall_analytics(city="Fazilka")

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["monthly_statistics"]), 12)
        self.assertIn("Fazilka", result["location"])
        self.assertIn("not live forecasts", result["description"])

    def test_home_serves_dashboard(self):
        response = main.home()

        self.assertEqual(response.path, main.FRONTEND_PATH / "index.html")
        self.assertTrue(Path(response.path).is_file())

    def test_health_reports_offline_mode(self):
        result = main.health_check()

        self.assertEqual(
            result["forecast_mode"],
            "offline_district_historical_estimates",
        )
        self.assertEqual(result["district_count"], 23)


if __name__ == "__main__":
    unittest.main()
