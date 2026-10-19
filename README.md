# Ludhiana Historical Rainfall Estimates

A Ludhiana-focused dashboard that serves offline historical rainfall estimates
and monthly rainfall analysis from data included in the repository.

> **Estimate transparency:** daily estimates compare the requested calendar
> date with observed rainfall on that date in the included Ludhiana
> 2022–2025 dataset. These historical averages are not live forecasts and do
> not predict actual future weather. The dataset only covers Ludhiana.

## Features

- Offline daily and seven-day historical rainfall estimates for Ludhiana.
- Historical monthly rainfall analytics using the included Ludhiana reference
  dataset.
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

The dashboard, API, and historical rainfall dataset are served by the same
service. Forecast estimates and analytics do not call an external weather API.
The dashboard uses Chart.js from a CDN for charts, so the charts require an
internet connection; the forecast data itself is read from the local CSV.

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
| `GET /predict?city=Ludhiana` | Historical estimate for tomorrow |
| `GET /predict/weekly?city=Ludhiana` | Seven daily historical estimates |
| `GET /analytics/monthly` | Historical monthly rainfall statistics |

Daily estimate endpoints currently support Ludhiana only. Other cities return
HTTP 404 because the included historical dataset does not contain their
rainfall observations.

## Data and attribution

Historical estimates and analytics use
`data/raw/ludhiana_rainfall_reference_2022_2025.csv`. Other raw and processed
CSVs support the research notebooks and evaluation reports. The saved trained
model is retained for notebook evaluation; it is not used for these estimates
because its inputs do not provide a future weather forecast.

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
