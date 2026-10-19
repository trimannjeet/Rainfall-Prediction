from collections import defaultdict
import csv
from datetime import date, datetime, timedelta
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="RainfallAI 2026",
    description="Offline historical rainfall estimates for Ludhiana",
    version="1.0.0",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
DATASET_PATH = (
    PROJECT_ROOT / "data" / "raw" / "ludhiana_rainfall_reference_2022_2025.csv"
)
SUPPORTED_CITY = "Ludhiana"
RAINY_DAY_THRESHOLD_MM = 0.1
MONTH_NAMES = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
]


def india_today():
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def validate_supported_city(city):
    if city.strip().casefold() != SUPPORTED_CITY.casefold():
        raise HTTPException(
            status_code=404,
            detail=(
                "Offline historical rainfall estimates are currently "
                "available for Ludhiana only."
            ),
        )
    return SUPPORTED_CITY


def load_historical_rainfall():
    if not DATASET_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Historical dataset not found: {DATASET_PATH.name}",
        )

    observations = []
    try:
        with DATASET_PATH.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)
            required = {"date", "observed_rainfall_mm"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "The CSV must contain date and "
                        "observed_rainfall_mm columns."
                    ),
                )

            for row in reader:
                try:
                    observation_date = date.fromisoformat(row["date"].strip())
                    rainfall = float(row["observed_rainfall_mm"])
                except (AttributeError, TypeError, ValueError):
                    continue

                if math.isfinite(rainfall) and rainfall >= 0:
                    observations.append((observation_date, rainfall))
    except HTTPException:
        raise
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read the historical rainfall dataset.",
        ) from exc

    if not observations:
        raise HTTPException(
            status_code=500,
            detail="The historical rainfall dataset contains no valid records.",
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
    probability = rainy_days / len(matching_days) * 100
    return {
        "rainfall_mm": round(rainfall_mm, 2),
        "precipitation_probability_percent": round(probability),
        "sample_count": len(matching_days),
        "estimate_method": estimate_method,
    }


def make_daily_estimate(target_date, observations):
    estimate = estimate_rainfall(target_date, observations)
    return {
        "date": target_date.isoformat(),
        "rainfall_mm": estimate["rainfall_mm"],
        "precipitation_probability_percent":
            estimate["precipitation_probability_percent"],
        "temperature_max_c": None,
        "temperature_min_c": None,
        "weather_code": None,
        "summary": (
            f"Historical estimate from {estimate['sample_count']} "
            f"{estimate['estimate_method']} samples"
        ),
        "sample_count": estimate["sample_count"],
        "estimate_method": estimate["estimate_method"],
    }


@app.get("/")
def home():
    return FileResponse(FRONTEND_PATH / "index.html")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "backend": "online",
        "forecast_mode": "offline_historical_estimates",
    }


@app.get("/predict")
def predict_tomorrow(
    city: str = Query(
        SUPPORTED_CITY,
        min_length=2,
        max_length=100,
    )
):
    resolved_city = validate_supported_city(city)
    observations = load_historical_rainfall()
    forecast_date = india_today() + timedelta(days=1)
    forecast = make_daily_estimate(forecast_date, observations)

    return {
        "status": "success",
        "source": DATASET_PATH.name,
        "location": {
            "city": resolved_city,
            "country": "India",
            "timezone": "Asia/Kolkata",
        },
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
            "summary": "Current weather is not included in the offline dataset.",
        },
        "forecast_date": forecast["date"],
        "forecast": forecast,
        "note": (
            "This is a historical rainfall estimate for Ludhiana based on "
            "the included 2022–2025 observations. It is not a live forecast."
        ),
    }


@app.get("/predict/weekly")
def predict_weekly(
    city: str = Query(
        SUPPORTED_CITY,
        min_length=2,
        max_length=100,
    )
):
    resolved_city = validate_supported_city(city)
    observations = load_historical_rainfall()
    first_date = india_today() + timedelta(days=1)
    forecasts = [
        make_daily_estimate(first_date + timedelta(days=offset), observations)
        for offset in range(7)
    ]
    return {
        "status": "success",
        "source": DATASET_PATH.name,
        "location": {
            "city": resolved_city,
            "country": "India",
            "timezone": "Asia/Kolkata",
        },
        "daily_forecasts": forecasts,
        "note": (
            "These are historical rainfall estimates for Ludhiana based on "
            "matching calendar dates in the included 2022–2025 observations. "
            "They are not live forecasts."
        ),
    }


@app.get("/analytics/monthly")
def monthly_rainfall_analytics():
    """Summarize historical rainfall by calendar month."""
    observations = load_historical_rainfall()
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
        "location": "Ludhiana historical reference dataset",
        "description": (
            "Historical observed rainfall grouped by calendar month. "
            "These statistics are not a live forecast."
        ),
        "wettest_month_by_average_daily_rainfall": wettest_month,
        "monthly_statistics": results,
    }


app.mount("/", StaticFiles(directory=FRONTEND_PATH), name="frontend")
