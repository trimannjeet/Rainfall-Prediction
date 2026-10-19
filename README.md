# Punjab District Rainfall Estimates

A dashboard for all 23 Punjab districts. It serves offline historical daily
rainfall estimates and monthly rainfall analysis from data included in the
repository.

> **Estimate transparency:** daily estimates compare the requested calendar
> date with 2022–2025 ERA5 gridded rainfall near the selected district's
> headquarters. This is a single representative grid point per district, not
> a district-wide average or local rain-gauge measurement. Estimates summarize
> past data and are not live forecasts or predictions of actual future weather.

## Features

- Offline daily and seven-day historical rainfall estimates for all 23 Punjab
  districts.
- District-specific monthly rainfall analytics.
- The downloaded dataset is served locally; the running app makes no weather
  API requests.
- FastAPI serves the dashboard and API from one origin.

## Quick start

### Requirements

- Python 3.11 or newer

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

## Deploy to Render

The repository includes a `render.yaml` Blueprint for the FastAPI web service.
In Render, create a new Blueprint and connect this repository. Make sure the
service root directory is the directory containing `render.yaml`,
`requirements.txt`, and `backend/`. Render will install the application
requirements, start Uvicorn on the port supplied by Render, and check
`/health` to verify the service is running.

The dashboard, API, and district rainfall dataset are served by the same
service. The app itself makes no external weather-data requests. Charts load
Chart.js from a CDN and therefore need an internet connection.

## Refreshing the historical dataset

The bundled dataset contains daily ERA5 `rain_sum` data for 23 representative
district-headquarters locations from 2022-01-01 through 2025-12-31. To fetch a
fresh copy manually, run this from the repository root:

```bash
python scripts/download_punjab_district_rainfall.py
```

This one-time download requires internet access. The script validates the date
coverage and values for every district and replaces the CSV only after all 23
downloads succeed. The deployed app reads the committed CSV and does not call
the archive API.

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
| `GET /districts` | The 23 supported Punjab districts and representative headquarters |
| `GET /predict?city=Amritsar` | Tomorrow's historical estimate for a district |
| `GET /predict/weekly?city=Amritsar` | Seven daily historical estimates |
| `GET /analytics/monthly?city=Amritsar` | District-specific monthly rainfall statistics |

The `city` query accepts district names and common headquarters aliases such as
`Mohali`, `Ropar`, `Firozpur`, `Nawanshahr`, and `Muktsar`.

## Data and attribution

The app uses `data/raw/punjab_district_rainfall_2022_2025.csv`. Daily rainfall
comes from the [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
using ERA5 reanalysis data. The representative headquarters coordinates are
resolved from the Open-Meteo geocoder; Malerkotla's coordinate is from
[OpenStreetMap](https://www.openstreetmap.org/copyright).

Open-Meteo API data is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); attribution links
are included in the dashboard. OpenStreetMap data is © OpenStreetMap
contributors and is licensed under the
[ODbL](https://www.openstreetmap.org/copyright).

The remaining Ludhiana raw/processed CSVs, model artifacts, notebooks, and
reports are retained as research material; they are not required by the
deployed district dashboard.

The historical dataset and research artifacts are included as project
materials. Verify the original source's redistribution terms before publishing
those datasets in a public repository.

## Project structure

```text
backend/       FastAPI app and regression tests
data/raw/      Source research data and Punjab district archive
data/processed/Derived analysis and evaluation data
frontend/      Dashboard HTML, CSS, and JavaScript
model/         Model and feature configuration used by evaluation
models/        Regenerable training outputs (not committed)
notebooks/     Data collection, analysis, training, and evaluation
reports/       CSV evaluation reports
scripts/       Historical dataset download utility
```

## License

No license has been added yet. Choose a license before publishing if you want
to grant others permission to use, modify, and redistribute this project.
