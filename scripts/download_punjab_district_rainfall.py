import csv
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
import json
import math
import os
from pathlib import Path
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "punjab_district_rainfall_2022_2025.csv"
)
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = date(2022, 1, 1)
END_DATE = date(2025, 12, 31)
MODEL = "era5"
TIMEZONE = "Asia/Kolkata"
DISTRICTS = (
    ("Amritsar", "Amritsar", 31.62234, 74.87534),
    ("Barnala", "Barnala", 30.37451, 75.54870),
    ("Bathinda", "Bathinda", 30.20747, 74.93893),
    ("Faridkot", "Faridkot", 30.67399, 74.75579),
    ("Fatehgarh Sahib", "Sirhind", 30.64321, 76.38421),
    ("Fazilka", "Fazilka", 30.40207, 74.02836),
    ("Ferozepur", "Firozpur", 30.92574, 74.61311),
    ("Gurdaspur", "Gurdaspur", 32.03933, 75.40318),
    ("Hoshiarpur", "Hoshiarpur", 31.53723, 75.91269),
    ("Jalandhar", "Jalandhar", 31.32556, 75.57917),
    ("Kapurthala", "Kapurthala", 31.38011, 75.38105),
    ("Ludhiana", "Ludhiana", 30.91204, 75.85379),
    ("Malerkotla", "Malerkotla", 30.533129, 75.880760),
    ("Mansa", "Mansa", 29.98844, 75.40167),
    ("Moga", "Moga", 30.81383, 75.16878),
    ("Pathankot", "Pathankot", 32.27484, 75.65287),
    ("Patiala", "Patiala", 30.33625, 76.39220),
    ("Rupnagar", "Ropar", 30.96896, 76.52695),
    ("Sahibzada Ajit Singh Nagar", "Mohali", 30.67995, 76.72211),
    ("Sangrur", "Sangrur", 30.24506, 75.84488),
    ("Shaheed Bhagat Singh Nagar", "Nawanshahr", 31.12450, 76.11613),
    ("Sri Muktsar Sahib", "Muktsar", 30.47426, 74.51660),
    ("Tarn Taran", "Tarn Taran", 31.45191, 74.92777),
)
EXPECTED_DATES = [
    (START_DATE + timedelta(days=offset)).isoformat()
    for offset in range((END_DATE - START_DATE).days + 1)
]


def retry_delay(response_headers, attempt):
    retry_after = response_headers.get("Retry-After")
    if retry_after:
        try:
            return max(1, math.ceil(
                parsedate_to_datetime(retry_after).timestamp() - time.time()
            ))
        except (TypeError, ValueError, OverflowError, OSError):
            try:
                return max(1, int(retry_after))
            except ValueError:
                pass
    return 2 ** attempt


def fetch_district(district, headquarters, latitude, longitude):
    params = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "daily": "rain_sum",
        "timezone": TIMEZONE,
        "models": MODEL,
    })
    request = Request(
        f"{ARCHIVE_URL}?{params}",
        headers={"User-Agent": "PunjabRainfallResearch/1.0"},
    )

    for attempt in range(4):
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read())
            break
        except HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise
            delay = retry_delay(exc.headers, attempt)
            print(f"Rate limited downloading {district}; retrying in {delay}s.")
            time.sleep(delay)
        except (TimeoutError, URLError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"Could not download rainfall data for {district}.")

    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError(f"Archive response has no daily data for {district}.")

    dates = daily.get("time")
    rainfall_values = daily.get("rain_sum")
    if dates != EXPECTED_DATES or not isinstance(rainfall_values, list):
        raise ValueError(
            f"Archive returned an unexpected date range for {district}."
        )
    if len(rainfall_values) != len(EXPECTED_DATES):
        raise ValueError(
            f"Archive returned incomplete rainfall data for {district}."
        )

    rows = []
    for observation_date, rainfall in zip(dates, rainfall_values):
        if (
            not isinstance(rainfall, (int, float))
            or not math.isfinite(rainfall)
            or rainfall < 0
        ):
            raise ValueError(
                f"Archive returned invalid rainfall for {district} "
                f"on {observation_date}: {rainfall!r}"
            )
        rows.append({
            "district": district,
            "headquarters": headquarters,
            "latitude": latitude,
            "longitude": longitude,
            "date": observation_date,
            "rainfall_mm": rainfall,
        })
    return rows


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=OUTPUT_PATH.parent,
            prefix=f".{OUTPUT_PATH.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            writer = csv.DictWriter(
                output,
                fieldnames=(
                    "district",
                    "headquarters",
                    "latitude",
                    "longitude",
                    "date",
                    "rainfall_mm",
                ),
            )
            writer.writeheader()
            for district, headquarters, latitude, longitude in DISTRICTS:
                rows = fetch_district(
                    district,
                    headquarters,
                    latitude,
                    longitude,
                )
                writer.writerows(rows)
                print(f"Downloaded {len(rows)} daily records for {district}.")
                time.sleep(0.5)

        os.replace(temporary_path, OUTPUT_PATH)
        print(f"Saved {len(DISTRICTS) * len(EXPECTED_DATES)} rows to {OUTPUT_PATH}")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    main()
