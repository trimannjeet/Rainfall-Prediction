# Punjab Rainfall Forecast

A Punjab-focused weather dashboard for current conditions, tomorrow's rainfall
forecast, and a seven-day outlook. Search or browse 90+ Punjab cities and towns
from the dashboard.

> **Forecast transparency:** live forecasts are supplied by Open-Meteo. The
> trained model and notebooks are included for research, but the live dashboard
> does not use that model to produce its forecasts. Provider data is updated
> periodically; it is not a live rain-gauge observation.

## Features

- Current weather, next-day rainfall, and a seven-day forecast.
- Searchable, scrollable place selector, plus support for typing another city.
- Backend validation that rejects locations not identified as Punjab, India.
- Historical monthly rainfall analytics using the included Ludhiana reference
  dataset.
- FastAPI serves the dashboard and API from one origin.

## Quick start

### Requirements

- Python 3.11 or newer
- An internet connection for Open-Meteo geocoding and forecast data

### Windows

Run these commands from the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8001
```

If PowerShell blocks virtual-environment activation, run the commands using
`.venv\Scripts\python.exe` instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8001
```

Open <http://127.0.0.1:8001>. Interactive API documentation is at
<http://127.0.0.1:8001/docs>, and the health check is at
<http://127.0.0.1:8001/health>.

## Tests

Run the backend regression tests from the repository root:

```bash
python -m unittest discover -s backend -v
```

Check the frontend JavaScript syntax (Node.js required):

```bash
node --check frontend/script.js
```

## Research notebooks

The notebooks document data collection, analysis, model training, and
evaluation. Install their additional dependencies with:

```bash
python -m pip install -r requirements-notebooks.txt
```

Run Jupyter from the repository root so notebook paths resolve to the
repository's `data/`, `model/`, and `reports/` directories:

```bash
jupyter lab
```

Run the notebooks in order. The evaluation notebook loads the saved model and
feature configuration from `model/`. The notebook requirements pin
scikit-learn to the version used to serialize that saved model. Re-running the
training notebook may regenerate the derived artifacts in `models/`; those
generated files are excluded from Git.

## API

| Endpoint | Description |
| --- | --- |
| `GET /health` | Backend health status |
| `GET /predict?city=Ludhiana` | Current conditions and tomorrow's forecast |
| `GET /predict/weekly?city=Amritsar` | Seven-day daily forecast |
| `GET /analytics/monthly` | Historical monthly rainfall statistics |

Forecast endpoints accept a `city` query parameter. The backend verifies the
resolved country and state with Open-Meteo geocoding before requesting weather
data. Non-Punjab locations are rejected.

## Data and attribution

Historical analysis uses `data/raw/ludhiana_rainfall_reference_2022_2025.csv`.
Other raw and processed CSVs support the research notebooks and evaluation
reports. Forecast and geocoding requests are served by
[Open-Meteo](https://open-meteo.com/); review its current terms and attribution
requirements before deploying or redistributing the application.

The historical dataset and research artifacts are included as project
materials. Verify the original source's redistribution terms before publishing
those datasets in a public repository.

## Project structure

```text
backend/       FastAPI app and regression tests
data/raw/      Source datasets
data/processed/Derived analysis and evaluation data
frontend/      Dashboard HTML, CSS, and JavaScript
model/         Model and feature configuration used by evaluation
models/        Regenerable training outputs (not committed)
notebooks/     Data collection, analysis, training, and evaluation
reports/       CSV evaluation reports
```

## License

No license has been added yet. Choose a license before publishing if you want
to grant others permission to use, modify, and redistribute this project.
