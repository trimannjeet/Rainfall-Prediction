
from datetime import date, timedelta
import csv
import math
import time
from pathlib import Path
from collections import defaultdict


import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="RainfallAI 2026",
    description="Tomorrow's rainfall forecast using live weather data",
    version="1.0.0",
)

# Open-Meteo API endpoints
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
PUNJAB_STATE = "punjab"
INDIA_COUNTRY_CODE = "IN"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
CITY_CACHE = {}
FORECAST_CACHE = {}
CITY_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
STALE_CITY_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
FORECAST_CACHE_TTL_SECONDS = 60 * 60
STALE_CACHE_TTL_SECONDS = 86400
PROVIDER_RATE_LIMITED_UNTIL = 0


def fetch_with_retry(url, params=None, timeout=20):
    """Retry transient failures, but do not amplify provider rate limits."""
    global PROVIDER_RATE_LIMITED_UNTIL

    params = params or {}
    last_error = None

    for attempt in range(4):
        cooldown_remaining = PROVIDER_RATE_LIMITED_UNTIL - time.time()
        if cooldown_remaining > 0:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Open-Meteo has temporarily limited requests for this "
                    "service. Please wait before trying again."
                ),
                headers={"Retry-After": str(math.ceil(cooldown_remaining))},
            )

        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "900")
                try:
                    retry_after_seconds = max(1, int(retry_after))
                except ValueError:
                    retry_after_seconds = 900
                PROVIDER_RATE_LIMITED_UNTIL = (
                    time.time() + retry_after_seconds
                )
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Open-Meteo has temporarily limited requests for this "
                        "service. Please wait before trying again."
                    ),
                    headers={"Retry-After": str(retry_after_seconds)},
                )

            response.raise_for_status()
            return response
        except HTTPException:
            raise
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise HTTPException(
                status_code=502,
                detail=f"Request to the weather service failed: {exc}",
            ) from exc

    if last_error is not None:
        raise HTTPException(
            status_code=502,
            detail="The weather provider request failed after retries.",
        ) from last_error

    raise HTTPException(
        status_code=502,
        detail="The weather provider request failed after retries.",
    )


def get_weather_forecast(location):
    """Fetch one shared seven-day payload for the daily and weekly views."""
    latitude = location["latitude"]
    longitude = location["longitude"]
    cache_key = (location["name"].casefold(), latitude, longitude)
    now = time.time()
    cached_forecast = FORECAST_CACHE.get(cache_key)

    if cached_forecast is not None:
        age = now - cached_forecast["saved_at"]
        if age < FORECAST_CACHE_TTL_SECONDS:
            return cached_forecast["data"]

    try:
        weather_response = fetch_with_retry(
            WEATHER_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "rain,"
                    "showers,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "daily": (
                    "precipitation_sum,"
                    "precipitation_probability_max,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "weather_code"
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=20,
        )
        weather_data = weather_response.json()
    except HTTPException:
        if (
            cached_forecast is not None
            and now - cached_forecast["saved_at"] < STALE_CACHE_TTL_SECONDS
        ):
            return cached_forecast["data"]
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="The weather service returned unexpected data.",
        ) from exc

    FORECAST_CACHE[cache_key] = {"data": weather_data, "saved_at": now}
    return weather_data


def describe_weather_code(code):
    """Convert a WMO weather code into a readable description."""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return descriptions.get(
        code,
        "Weather conditions unavailable"
    )


def find_punjab_city(city):
    """Resolve a city only when the geocoder identifies it as Punjab, India."""
    normalized_city = city.strip()
    cache_key = normalized_city.casefold()
    cached_result = CITY_CACHE.get(cache_key)
    if cached_result is not None:
        if time.time() - cached_result["saved_at"] < CITY_CACHE_TTL_SECONDS:
            return cached_result["data"]

    try:
        geo_response = fetch_with_retry(
            GEOCODING_URL,
            params={
                "name": normalized_city,
                "count": 10,
                "language": "en",
                "format": "json",
                "countryCode": INDIA_COUNTRY_CODE,
            },
            timeout=15,
        )
        geo_data = geo_response.json()
    except HTTPException:
        if (
            cached_result is not None
            and time.time() - cached_result["saved_at"]
            < STALE_CITY_CACHE_TTL_SECONDS
        ):
            return cached_result["data"]
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="The city lookup service returned unexpected data.",
        ) from exc

    if not isinstance(geo_data, dict):
        raise HTTPException(
            status_code=502,
            detail="The city lookup service returned unexpected data.",
        )

    locations = geo_data.get("results", [])
    if not isinstance(locations, list):
        raise HTTPException(
            status_code=502,
            detail="The city lookup service returned unexpected data.",
        )

    punjab_locations = [
        location
        for location in locations
        if isinstance(location, dict)
        and isinstance(location.get("country_code"), str)
        and location["country_code"].upper() == INDIA_COUNTRY_CODE
        and isinstance(location.get("admin1"), str)
        and location["admin1"].strip().casefold() == PUNJAB_STATE
    ]

    if not punjab_locations:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Could not find {city} in Punjab, India. "
                "Enter a city located in Punjab."
            ),
        )

    result = punjab_locations[0]
    CITY_CACHE[cache_key] = {"data": result, "saved_at": time.time()}
    return result


@app.get("/")
def home():
    return FileResponse(FRONTEND_PATH / "index.html")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "backend": "online",
    }


@app.get("/predict")
def predict_tomorrow(
    city: str = Query(
        "Ludhiana",
        min_length=2,
        max_length=100,
    )
):
    # STEP 1: Resolve the city within Punjab, India
    try:
        location = find_punjab_city(city)
        latitude = location["latitude"]
        longitude = location["longitude"]
        resolved_city = location["name"]
        country = location.get("country", "Unknown")

        # STEP 2: Reuse the same provider payload for daily and weekly views.
        weather_data = get_weather_forecast(location)

    except HTTPException:
        raise

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Weather service request failed: {exc}",
        ) from exc

    except (ValueError, KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=502,
            detail="The weather service returned unexpected data.",
        ) from exc

    if not isinstance(weather_data, dict):
        raise HTTPException(
            status_code=502,
            detail="The weather service returned unexpected data.",
        )

    current = weather_data.get("current")
    current_fields = (
        "time",
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "showers",
        "weather_code",
        "wind_speed_10m",
    )
    if (
        not isinstance(current, dict)
        or any(field not in current for field in current_fields)
        or not isinstance(current.get("time"), str)
    ):
        raise HTTPException(
            status_code=502,
            detail="The weather service returned incomplete current conditions.",
        )

    # STEP 3: Find tomorrow's local date in the forecast
    daily = weather_data.get("daily")
    if not isinstance(daily, dict):
        raise HTTPException(
            status_code=502,
            detail="The weather service returned incomplete daily data.",
        )

    dates = daily.get("time", [])

    if (
        not isinstance(dates, list)
        or not dates
        or any(not isinstance(item, str) for item in dates)
    ):
        raise HTTPException(
            status_code=502,
            detail="No daily forecast dates were returned.",
        )

    daily_fields = (
        "precipitation_sum",
        "precipitation_probability_max",
        "temperature_2m_max",
        "temperature_2m_min",
        "weather_code",
    )
    if any(
        not isinstance(daily.get(field), list)
        or len(daily[field]) != len(dates)
        for field in daily_fields
    ):
        raise HTTPException(
            status_code=502,
            detail="The weather service returned incomplete daily data.",
        )

    try:
        tomorrow = (
            date.fromisoformat(dates[0]) + timedelta(days=1)
        ).isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="The weather service returned an invalid forecast date.",
        ) from exc

    if tomorrow not in dates:
        raise HTTPException(
            status_code=502,
            detail="Tomorrow's forecast was not returned.",
        )

    i = dates.index(tomorrow)

    rainfall = daily["precipitation_sum"][i]
    probability = daily["precipitation_probability_max"][i]
    temp_max = daily["temperature_2m_max"][i]
    temp_min = daily["temperature_2m_min"][i]
    weather_code = daily["weather_code"][i]

    # STEP 4: Return the forecast
    return {
        "status": "success",
        "source": "Open-Meteo forecast API",
        "location": {
            "city": resolved_city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_data.get("timezone"),
        },
        "current_conditions": {
            "time": current["time"],
            "temperature_c": current["temperature_2m"],
            "relative_humidity_percent": current["relative_humidity_2m"],
            "feels_like_c": current["apparent_temperature"],
            "precipitation_mm": current["precipitation"],
            "rain_mm": current["rain"],
            "showers_mm": current["showers"],
            "weather_code": current["weather_code"],
            "wind_speed_kmh": current["wind_speed_10m"],
            "summary": describe_weather_code(current["weather_code"]),
        },
        "forecast_date": tomorrow,
        "forecast": {
            "rainfall_mm": rainfall,
            "precipitation_probability_percent": probability,
            "temperature_max_c": temp_max,
            "temperature_min_c": temp_min,
            "weather_code": weather_code,
            "summary": describe_weather_code(weather_code),
        },
        "note": (
            "Current conditions and forecasts are supplied by Open-Meteo "
            "and are not verified predictions from the trained ML model."
        ),
    }

# Historical rainfall dataset
DATASET_PATH = (
    PROJECT_ROOT / "data" / "raw" / "ludhiana_rainfall_reference_2022_2025.csv"
)


@app.get("/analytics/monthly")
def monthly_rainfall_analytics():
    """Summarize historical rainfall by calendar month."""

    if not DATASET_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Historical dataset not found: {DATASET_PATH.name}",
        )

    monthly = defaultdict(
        lambda: {
            "total_mm": 0.0,
            "days": 0,
            "rainy_days": 0,
        }
    )

    try:
        with DATASET_PATH.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            required = {
                "date",
                "observed_rainfall_mm",
            }

            if not reader.fieldnames or not required.issubset(
                set(reader.fieldnames)
            ):
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "The CSV must contain date and "
                        "observed_rainfall_mm columns."
                    ),
                )

            for row in reader:
                date_value = row.get("date", "").strip()
                rainfall_value = row.get(
                    "observed_rainfall_mm", ""
                ).strip()

                if not date_value or not rainfall_value:
                    continue

                try:
                    month = int(date_value[5:7])
                    rainfall = float(rainfall_value)
                except (ValueError, IndexError):
                    continue

                if not 1 <= month <= 12 or rainfall < 0:
                    continue

                monthly[month]["total_mm"] += rainfall
                monthly[month]["days"] += 1

                if rainfall >= 0.1:
                    monthly[month]["rainy_days"] += 1

    except HTTPException:
        raise
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read the historical rainfall dataset.",
        ) from exc

    month_names = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December",
    ]

    results = []

    for month_number in range(1, 13):
        stats = monthly[month_number]
        days = stats["days"]

        results.append({
            "month": month_names[month_number - 1],
            "month_number": month_number,
            "days_with_data": days,
            "total_rainfall_mm": round(stats["total_mm"], 2),
            "average_daily_rainfall_mm": (
                round(stats["total_mm"] / days, 2)
                if days else None
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
            "These statistics are not tomorrow's forecast."
        ),
        "wettest_month_by_average_daily_rainfall": wettest_month,
        "monthly_statistics": results,
    }

@app.get("/predict/weekly")
def predict_weekly(
    city: str = Query(
        "Ludhiana",
        min_length=2,
        max_length=100,
    )
):
    """Return the next seven days of provider-supplied forecasts."""

    # 1. Resolve the city within Punjab, India
    try:
        location = find_punjab_city(city)
        latitude = location["latitude"]
        longitude = location["longitude"]

        # The main and weekly routes share the same cached provider payload.
        weather_data = get_weather_forecast(location)

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="The weather service returned unexpected data.",
        ) from exc

    # 3. Prepare the response
    if not isinstance(weather_data, dict):
        raise HTTPException(
            status_code=502,
            detail="The weather service returned unexpected data.",
        )

    daily = weather_data.get("daily")
    if not isinstance(daily, dict):
        raise HTTPException(
            status_code=502,
            detail="The weather service returned incomplete daily data.",
        )

    dates = daily.get("time", [])

    if (
        not isinstance(dates, list)
        or not dates
        or any(not isinstance(item, str) for item in dates)
    ):
        raise HTTPException(
            status_code=502,
            detail="No daily forecast dates were returned.",
        )

    try:
        for forecast_date in dates:
            date.fromisoformat(forecast_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="The weather service returned an invalid forecast date.",
        ) from exc

    required_fields = [
        "precipitation_sum",
        "precipitation_probability_max",
        "temperature_2m_max",
        "temperature_2m_min",
        "weather_code",
    ]

    if any(
        not isinstance(daily.get(field), list)
        or len(daily[field]) != len(dates)
        for field in required_fields
    ):
        raise HTTPException(
            status_code=502,
            detail="The weather service returned incomplete daily data.",
        )

    forecasts = []

    for i, forecast_date in enumerate(dates):
        forecasts.append({
            "date": forecast_date,
            "rainfall_mm": daily["precipitation_sum"][i],
            "precipitation_probability_percent":
                daily["precipitation_probability_max"][i],
            "temperature_max_c": daily["temperature_2m_max"][i],
            "temperature_min_c": daily["temperature_2m_min"][i],
            "weather_code": daily["weather_code"][i],
            "summary": describe_weather_code(
                daily["weather_code"][i]
            ),
        })

    return {
        "status": "success",
        "source": "Open-Meteo forecast API",
        "location": {
            "city": location["name"],
            "country": location.get("country", "Unknown"),
            "latitude": latitude,
            "longitude": longitude,
        },
        "daily_forecasts": forecasts,
        "note": (
            "These are weather-provider forecasts, not verified "
            "predictions from the trained machine-learning model."
        ),
    }


app.mount("/", StaticFiles(directory=FRONTEND_PATH), name="frontend")
