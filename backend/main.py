from collections import defaultdict
import csv
from datetime import date, datetime, timedelta
from functools import lru_cache
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Punjab Rainfall Estimates",
    description="Offline historical rainfall estimates for Punjab districts",
    version="1.0.0",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
DATASET_PATH = (
    PROJECT_ROOT / "data" / "raw" / "punjab_district_rainfall_2022_2025.csv"
)
RAINY_DAY_THRESHOLD_MM = 0.1
MONTH_NAMES = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
]
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
DISTRICT_BY_NAME = {
    district.casefold(): {
        "district": district,
        "headquarters": headquarters,
        "latitude": latitude,
        "longitude": longitude,
    }
    for district, headquarters, latitude, longitude in DISTRICTS
}
DISTRICT_ALIASES = {
    "sirhind": "Fatehgarh Sahib",
    "firozpur": "Ferozepur",
    "ropar": "Rupnagar",
    "mohali": "Sahibzada Ajit Singh Nagar",
    "nawanshahr": "Shaheed Bhagat Singh Nagar",
    "muktsar": "Sri Muktsar Sahib",
}
for district, headquarters, _, _ in DISTRICTS:
    DISTRICT_ALIASES.setdefault(headquarters.casefold(), district)
    DISTRICT_ALIASES.setdefault(district.casefold(), district)


def india_today():
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def resolve_district(city):
    normalized_city = " ".join(city.strip().casefold().split())
    district_name = DISTRICT_ALIASES.get(normalized_city)
    district = DISTRICT_BY_NAME.get(district_name.casefold()) if district_name else None
    if district is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Could not match {city!r} to a Punjab district. "
                "Choose one of the 23 listed districts or its headquarters."
            ),
        )
    return district


@lru_cache(maxsize=1)
def load_historical_rainfall():
    if not DATASET_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Punjab district dataset not found: {DATASET_PATH.name}",
        )

    observations = {district: [] for district, *_ in DISTRICTS}
    required = {
        "district",
        "headquarters",
        "latitude",
        "longitude",
        "date",
        "rainfall_mm",
    }
    try:
        with DATASET_PATH.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "The Punjab dataset must contain district, "
                        "headquarters, latitude, longitude, date, and "
                        "rainfall_mm columns."
                    ),
                )

            for row in reader:
                district_name = row.get("district", "").strip()
                district_key = district_name.casefold()
                if district_key not in DISTRICT_BY_NAME:
                    continue
                try:
                    observation_date = date.fromisoformat(row["date"].strip())
                    rainfall = float(row["rainfall_mm"])
                except (AttributeError, TypeError, ValueError):
                    continue
                if math.isfinite(rainfall) and rainfall >= 0:
                    observations[DISTRICT_BY_NAME[district_key]["district"]].append(
                        (observation_date, rainfall)
                    )
    except HTTPException:
        raise
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read the Punjab district rainfall dataset.",
        ) from exc

    missing_districts = [
        district for district, records in observations.items() if not records
    ]
    if missing_districts:
        raise HTTPException(
            status_code=500,
            detail=(
                "The Punjab dataset has no valid rainfall records for: "
                + ", ".join(missing_districts)
            ),
        )
    return observations


def estimate_rainfall(target_date, observations):
    matching_days = [
        rainfall
        for observed_date, rainfall in observations
        if (observed_date.month, observed_date.day)
        == (target_date.month, target_date.day)
    ]
    estimate_method = "matching calendar day"

    if not matching_days:
        matching_days = [
            rainfall
            for observed_date, rainfall in observations
            if observed_date.month == target_date.month
        ]
        estimate_method = "calendar month"

    if not matching_days:
        raise HTTPException(
            status_code=500,
            detail=(
                "The historical dataset has no records for the requested "
                "date or month."
            ),
        )

    rainfall_mm = sum(matching_days) / len(matching_days)
    rainy_days = sum(
        rainfall >= RAINY_DAY_THRESHOLD_MM for rainfall in matching_days
    )
    return {
        "rainfall_mm": round(rainfall_mm, 2),
        "precipitation_probability_percent": round(
            rainy_days / len(matching_days) * 100
        ),
        "sample_count": len(matching_days),
        "estimate_method": estimate_method,
    }


def make_daily_estimate(target_date, observations):
    estimate = estimate_rainfall(target_date, observations)
    return {
        "date": target_date.isoformat(),
        **estimate,
        "temperature_max_c": None,
        "temperature_min_c": None,
        "weather_code": None,
        "summary": (
            f"Historical estimate from {estimate['sample_count']} "
            f"{estimate['estimate_method']} samples"
        ),
    }


def district_observations(city):
    district = resolve_district(city)
    return district, load_historical_rainfall()[district["district"]]


def response_location(district):
    return {
        "district": district["district"],
        "city": district["headquarters"],
        "country": "India",
        "state": "Punjab",
        "latitude": district["latitude"],
        "longitude": district["longitude"],
        "timezone": "Asia/Kolkata",
    }


@app.get("/")
def home():
    return FileResponse(FRONTEND_PATH / "index.html")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "backend": "online",
        "forecast_mode": "offline_district_historical_estimates",
        "district_count": len(DISTRICTS),
    }


@app.get("/districts")
def list_districts():
    return {
        "districts": [
            {
                "district": district,
                "headquarters": headquarters,
            }
            for district, headquarters, _, _ in DISTRICTS
        ]
    }


@app.get("/predict")
def predict_tomorrow(
    city: str = Query(
        "Ludhiana",
        min_length=2,
        max_length=100,
    )
):
    district, observations = district_observations(city)
    forecast_date = india_today() + timedelta(days=1)
    forecast = make_daily_estimate(forecast_date, observations)

    return {
        "status": "success",
        "source": DATASET_PATH.name,
        "location": response_location(district),
        "current_conditions": {
            "time": None,
            "temperature_c": None,
            "relative_humidity_percent": None,
            "feels_like_c": None,
            "precipitation_mm": None,
            "rain_mm": None,
            "showers_mm": None,
            "weather_code": None,
            "wind_speed_kmh": None,
            "summary": "Current weather is not included in the historical dataset.",
        },
        "forecast_date": forecast["date"],
        "forecast": forecast,
        "note": (
            f"This historical estimate represents the ERA5 grid point near "
            f"{district['headquarters']}, {district['district']} district. "
            "It is not a live forecast or a local rain-gauge measurement."
        ),
    }


@app.get("/predict/weekly")
def predict_weekly(
    city: str = Query(
        "Ludhiana",
        min_length=2,
        max_length=100,
    )
):
    district, observations = district_observations(city)
    first_date = india_today() + timedelta(days=1)
    forecasts = [
        make_daily_estimate(first_date + timedelta(days=offset), observations)
        for offset in range(7)
    ]
    return {
        "status": "success",
        "source": DATASET_PATH.name,
        "location": response_location(district),
        "daily_forecasts": forecasts,
        "note": (
            f"These are historical estimates for the ERA5 grid point near "
            f"{district['headquarters']}, {district['district']} district. "
            "They are not live forecasts."
        ),
    }


@app.get("/analytics/monthly")
def monthly_rainfall_analytics(
    city: str = Query(
        "Ludhiana",
        min_length=2,
        max_length=100,
    )
):
    """Summarize historical rainfall by calendar month for one district."""
    district, observations = district_observations(city)
    monthly = defaultdict(
        lambda: {
            "total_mm": 0.0,
            "days": 0,
            "rainy_days": 0,
        }
    )

    for observation_date, rainfall in observations:
        stats = monthly[observation_date.month]
        stats["total_mm"] += rainfall
        stats["days"] += 1
        if rainfall >= RAINY_DAY_THRESHOLD_MM:
            stats["rainy_days"] += 1

    results = []
    for month_number, month_name in enumerate(MONTH_NAMES, start=1):
        stats = monthly[month_number]
        days = stats["days"]
        results.append({
            "month": month_name,
            "month_number": month_number,
            "days_with_data": days,
            "total_rainfall_mm": round(stats["total_mm"], 2),
            "average_daily_rainfall_mm": (
                round(stats["total_mm"] / days, 2) if days else None
            ),
            "rainy_days": stats["rainy_days"],
        })

    available_months = [
        item for item in results if item["days_with_data"] > 0
    ]
    wettest_month = (
        max(
            available_months,
            key=lambda item: item["average_daily_rainfall_mm"],
        )["month"]
        if available_months else None
    )

    return {
        "status": "success",
        "source": DATASET_PATH.name,
        "location": (
            f"{district['district']} district ERA5 grid point near "
            f"{district['headquarters']}"
        ),
        "description": (
            "Historical gridded rainfall grouped by calendar month. "
            "These are not live forecasts or rain-gauge observations."
        ),
        "wettest_month_by_average_daily_rainfall": wettest_month,
        "monthly_statistics": results,
    }


app.mount("/", StaticFiles(directory=FRONTEND_PATH), name="frontend")
