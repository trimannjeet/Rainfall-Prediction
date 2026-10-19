
const API_BASE_URL = "";
const searchForm = document.getElementById("search-form");
const cityInput = document.getElementById("city-input");
const forecastButton = document.getElementById("forecast-button");
const buttonText = document.getElementById("button-text");
const messageBox = document.getElementById("message");

function showMessage(message, type = "success") {
    messageBox.textContent = message;
    messageBox.className = `message ${type}`;
}

function hideMessage() {
    messageBox.textContent = "";
    messageBox.className = "message hidden";
}

function formatDate(dateString) {
    const parsedDate = new Date(`${dateString}T12:00:00`);

    if (Number.isNaN(parsedDate.getTime())) {
        return dateString;
    }

    return parsedDate.toLocaleDateString(undefined, {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
    });
}

function formatNumber(value, decimals = 1) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) {
        return "--";
    }

    return Number(value).toFixed(decimals);
}

function rainfallCategory(rainfall) {
    if (rainfall === null || rainfall === undefined || !Number.isFinite(Number(rainfall))) {
        return "Unavailable";
    }

    const amount = Number(rainfall);

    if (amount < 0.1) return "Dry";
    if (amount < 2.5) return "Light";
    if (amount < 15) return "Moderate";
    if (amount < 64.5) return "Heavy";
    return "Very heavy";
}

function weatherIcon(code) {
    return code == null ? "📊" : "🌦️";
}

function updateApiStatus(text, healthy = false) {
    const status = document.getElementById("api-status");
    const indicator = document.querySelector(".status-indicator");

    status.textContent = text;
    indicator.style.background = healthy ? "#56e0a0" : "#ffbd69";
    indicator.style.boxShadow = healthy
        ? "0 0 12px rgba(86, 224, 160, 0.6)"
        : "0 0 12px rgba(255, 189, 105, 0.4)";
}

function renderForecast(data) {
    const forecast = data.forecast;
    const location = data.location;
    document.getElementById("estimate-sample-count").textContent =
        forecast.sample_count;
    document.getElementById("estimate-method").textContent =
        forecast.estimate_method;
    document.getElementById("current-weather-updated").textContent =
        `Rainfall summaries for the ERA5 grid point near ${location.city}, ${location.district} district.`;

    const liveRainfall = document.getElementById("live-rainfall");
    const liveSummary = document.getElementById("live-forecast-summary");
    const liveProbability = document.getElementById("live-rain-probability");
    const liveSampleCount = document.getElementById("live-sample-count");
    const liveEstimateMethod = document.getElementById("live-estimate-method");
    const liveDate = document.getElementById("live-forecast-date");
    const liveIcon = document.querySelector(".forecast-weather-icon");

    if (liveRainfall) {
        liveRainfall.innerHTML =
            `${formatNumber(forecast.rainfall_mm)} <span>mm</span>`;
    }

    if (liveSummary) {
        liveSummary.textContent =
            forecast.summary || "Historical estimate available";
    }

    if (liveProbability) {
        liveProbability.textContent =
            forecast.precipitation_probability_percent == null
                ? "Unavailable"
                : `${forecast.precipitation_probability_percent}%`;
    }

    if (liveSampleCount) {
        liveSampleCount.textContent = forecast.sample_count;
    }

    if (liveEstimateMethod) {
        liveEstimateMethod.textContent = forecast.estimate_method;
    }

    if (liveDate) {
        liveDate.textContent =
            `Estimate date: ${formatDate(data.forecast_date)} · ${location.district} district`;
    }

    if (liveIcon) {
        liveIcon.textContent = weatherIcon(forecast.weather_code);
    }


    document.getElementById("forecast-location").textContent =
        `${location.district} district historical estimate`;
    document.getElementById("selected-district-title").textContent =
        `Historical rainfall for ${location.district} district`;
    document.getElementById("live-forecast-description").textContent =
        `Average historical rainfall on matching calendar dates for ${location.district} district.`;
    document.getElementById("live-estimate-disclaimer").textContent =
        `This is a historical estimate for the ERA5 grid point near ${location.city}, not a live weather forecast or a verified prediction from the trained model.`;
    document.getElementById("analytics-description").textContent =
        `Historical daily averages from the ERA5 grid point near ${location.city}, ${location.district} district.`;

    document.getElementById("forecast-date").textContent =
        formatDate(data.forecast_date);

    document.getElementById("rainfall-value").textContent =
        formatNumber(forecast.rainfall_mm);

    document.getElementById("weather-summary").textContent =
        "Historical rainfall estimate";

    document.getElementById("weather-icon").textContent =
        weatherIcon(forecast.weather_code);

    const rainfall = forecast.rainfall_mm;

    document.getElementById("rainfall-description").textContent =
        rainfall === null || rainfall === undefined
            ? "No matching historical rainfall data is available."
            : `${formatNumber(rainfall)} mm is the historical average for a matching calendar date; this is not a live forecast.`;

    const probability = forecast.precipitation_probability_percent;

    document.getElementById("rain-probability").textContent =
        probability === null || probability === undefined
            ? "Unavailable"
            : `${probability}%`;

    const safeProbability = Number.isFinite(Number(probability))
        ? Math.max(0, Math.min(100, Number(probability)))
        : 0;

    document.getElementById("probability-fill").style.width =
        `${safeProbability}%`;

    document.getElementById("rain-category").textContent =
        rainfallCategory(rainfall);

    document.getElementById("location-name").textContent =
        location.district;

    document.getElementById("location-country").textContent =
        `${location.state}, ${location.country}`;

    updateApiStatus("Offline data loaded", true);
}

async function loadForecast(city = cityInput.value) {
    hideMessage();
    forecastButton.disabled = true;
    buttonText.textContent = "Loading...";
    updateApiStatus("Loading local dataset...", false);

    try {
        const url = new URL(`${API_BASE_URL}/predict`, window.location.origin);
        url.searchParams.set("city", city);
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            const detail = typeof data.detail === "string"
                ? data.detail
                : "Unable to retrieve the forecast.";

            throw new Error(detail);
        }

        if (
            data.status !== "success"
            || !data.forecast
            || !data.location
            || !data.current_conditions
        ) {
            throw new Error("The backend response is missing forecast information.");
        }

        renderForecast(data);
        loadWeeklyForecast(city);
        loadMonthlyAnalytics(city);
        showMessage(
            `Showing offline historical rainfall estimates for ${data.location.district} district. These are not live forecasts.`,
            "success"
        );
    } catch (error) {
        if (error instanceof TypeError) {
            updateApiStatus("App connection issue", false);
            showMessage(
                `Cannot connect to the app at ${window.location.origin}.`,
                "error"
            );
            return;
        }
        updateApiStatus("Dataset unavailable", false);
        showMessage(error.message || "Could not load historical rainfall estimates.", "error");
    } finally {
        forecastButton.disabled = false;
        buttonText.textContent = "Show estimates";
    }
}

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    loadForecast(cityInput.value);
});

// Update the selected sidebar link when clicked.
document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
        document.querySelectorAll(".nav-link").forEach((item) => {
            item.classList.remove("active");
        });

        link.classList.add("active");
    });
});

/* HISTORICAL RAINFALL ANALYTICS */

let monthlyRainfallChart = null;

async function loadMonthlyAnalytics(city) {
    const status = document.getElementById("analytics-status");
    const canvas = document.getElementById("monthly-rainfall-chart");

    if (!status || !canvas) return;

    try {
        const url = new URL(
            `${API_BASE_URL}/analytics/monthly`,
            window.location.origin
        );
        url.searchParams.set("city", city);
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Could not load historical rainfall analytics.");
        }

        const data = await response.json();

        if (
            data.status !== "success" ||
            !Array.isArray(data.monthly_statistics)
        ) {
            throw new Error("The analytics response has an unexpected format.");
        }

        const months = data.monthly_statistics;
        const totalRainfall = months.reduce(
            (sum, item) => sum + Number(item.total_rainfall_mm || 0),
            0
        );
        const totalDays = months.reduce(
            (sum, item) => sum + Number(item.days_with_data || 0),
            0
        );
        const rainyDays = months.reduce(
            (sum, item) => sum + Number(item.rainy_days || 0),
            0
        );
        const annualRainfall = totalRainfall / 4;

        document.getElementById("historical-annual-rainfall").textContent =
            `${formatNumber(annualRainfall)} mm`;
        document.getElementById("historical-daily-rainfall").textContent =
            `${formatNumber(totalRainfall / totalDays)} mm`;
        document.getElementById("historical-rainy-frequency").textContent =
            `${formatNumber(rainyDays / totalDays * 100)}%`;
        document.getElementById("historical-wettest-month").textContent =
            data.wettest_month_by_average_daily_rainfall || "Unavailable";
        const wettestMonth = months.find(
            (item) => item.month === data.wettest_month_by_average_daily_rainfall
        );
        document.getElementById("historical-wettest-month-rainfall").textContent =
            wettestMonth
                ? `${formatNumber(wettestMonth.average_daily_rainfall_mm)} mm/day average`
                : "No historical monthly data";


        // Update the wettest month card
        document.getElementById("wettest-month").textContent =
            data.wettest_month_by_average_daily_rainfall || "Unavailable";

        // Find the driest month from the monthly statistics
        const validMonths = months.filter(
            (item) => item.average_daily_rainfall_mm !== null
        );

        if (validMonths.length > 0) {
            const driestMonth = [...validMonths].sort(
                (a, b) =>
                    Number(a.average_daily_rainfall_mm) -
                    Number(b.average_daily_rainfall_mm)
            )[0];

            document.getElementById("driest-month").textContent =
                driestMonth.month;

            // Calculate the mean of the monthly daily averages
            const averageRainfall =
                validMonths.reduce(
                    (sum, item) =>
                        sum + Number(item.average_daily_rainfall_mm),
                    0
                ) / validMonths.length;

            document.getElementById("average-rainfall").textContent =
                `${averageRainfall.toFixed(2)} mm/day`;
        }

        if (typeof Chart === "undefined") {
            throw new Error(
                "Historical summary loaded, but Chart.js did not load. Check your internet connection."
            );
        }

        const labels = months.map((item) => item.month);
        const values = months.map((item) =>
            item.average_daily_rainfall_mm === null
                ? 0
                : Number(item.average_daily_rainfall_mm)
        );

        if (monthlyRainfallChart) {
            monthlyRainfallChart.destroy();
        }

        monthlyRainfallChart = new Chart(canvas, {
            type: "bar",

            data: {
                labels,

                datasets: [{
                    label: "Average daily rainfall (mm)",
                    data: values,
                    backgroundColor: "rgba(86, 190, 255, 0.65)",
                    borderColor: "#62b5ff",
                    borderWidth: 1,
                    borderRadius: 6,
                    hoverBackgroundColor: "#56e0dc",
                    maxBarThickness: 35
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                interaction: {
                    intersect: false,
                    mode: "index"
                },

                plugins: {
                    legend: {
                        labels: {
                            color: "#c9d8ec",
                            font: {
                                family: "Inter",
                                size: 11
                            }
                        }
                    },

                    tooltip: {
                        callbacks: {
                            label(context) {
                                return ` ${context.parsed.y.toFixed(2)} mm/day`;
                            }
                        }
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            color: "#91a2bc",
                            maxRotation: 45,
                            minRotation: 0,
                            font: {
                                size: 10
                            }
                        },

                        grid: {
                            display: false
                        }
                    },

                    y: {
                        beginAtZero: true,

                        title: {
                            display: true,
                            text: "Average rainfall (mm/day)",
                            color: "#91a2bc"
                        },

                        ticks: {
                            color: "#91a2bc"
                        },

                        grid: {
                            color: "rgba(159, 183, 220, 0.10)"
                        }
                    }
                }
            }
        });

        status.textContent =
            `Loaded historical ${data.location} data from ${data.source}. ` +
            `Wettest month by average daily rainfall: ` +
            `${data.wettest_month_by_average_daily_rainfall || "Unavailable"}.`;

    } catch (error) {
        status.textContent = error.message;
        console.error("Monthly analytics error:", error);
    }
}


let weeklyRainfallChart = null;

async function loadWeeklyForecast(city) {
    const status = document.getElementById("weekly-forecast-status");
    const canvas = document.getElementById("weekly-rainfall-chart");

    if (!status || !canvas) {
        return;
    }

    status.textContent = "Loading seven-day historical estimates...";

    try {
        const url = new URL(
            `${API_BASE_URL}/predict/weekly`,
            window.location.origin
        );
        url.searchParams.set("city", city);
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Unable to load the weekly forecast."
            );
        }

        if (
            data.status !== "success" ||
            !Array.isArray(data.daily_forecasts)
        ) {
            throw new Error("The backend returned an unexpected response.");
        }

        const forecasts = data.daily_forecasts;

        const labels = forecasts.map(item => {
            const forecastDate = new Date(`${item.date}T12:00:00`);

            return forecastDate.toLocaleDateString("en-IN", {
                weekday: "short",
                day: "numeric",
                month: "short"
            });
        });

        const rainfall = forecasts.map(item =>
            item.rainfall_mm == null ? null : Number(item.rainfall_mm)
        );

        const probability = forecasts.map(item =>
            item.precipitation_probability_percent == null
                ? null
                : Number(item.precipitation_probability_percent)
        );

        if (typeof Chart === "undefined") {
            throw new Error("Chart.js did not load. Check your internet connection.");
        }

        if (weeklyRainfallChart) {
            weeklyRainfallChart.destroy();
        }

        weeklyRainfallChart = new Chart(canvas, {
            type: "bar",

            data: {
                labels: labels,

                datasets: [
                    {
                        type: "bar",
                        label: "Historical average rainfall (mm)",
                        data: rainfall,
                        yAxisID: "yRain",
                        backgroundColor: "rgba(91, 156, 255, 0.75)",
                        borderColor: "#5b9cff",
                        borderWidth: 1,
                        borderRadius: 6,
                        maxBarThickness: 40
                    },
                    {
                        type: "line",
                        label: "Historical rainy-day frequency (%)",
                        data: probability,
                        yAxisID: "yProbability",
                        borderColor: "#39d5c8",
                        backgroundColor: "#39d5c8",
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        tension: 0.3,
                        spanGaps: true
                    }
                ]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                interaction: {
                    mode: "index",
                    intersect: false
                },

                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: "#e8eef8"
                        }
                    },

                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                if (context.dataset.yAxisID === "yProbability") {
                                    return `Historical rainy-day frequency: ${context.parsed.y ?? "N/A"}%`;
                                }

                                return `Rainfall: ${context.parsed.y ?? "N/A"} mm`;
                            }
                        }
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            color: "#c5d0e0"
                        },
                        grid: {
                            display: false
                        }
                    },

                    yRain: {
                        type: "linear",
                        position: "left",
                        beginAtZero: true,

                        title: {
                            display: true,
                            text: "Rainfall (mm)",
                            color: "#c5d0e0"
                        },

                        ticks: {
                            color: "#c5d0e0"
                        }
                    },

                    yProbability: {
                        type: "linear",
                        position: "right",
                        beginAtZero: true,
                        min: 0,
                        max: 100,

                        title: {
                            display: true,
                            text: "Rainy-day frequency in historical samples (%)",
                            color: "#c5d0e0"
                        },

                        ticks: {
                            color: "#c5d0e0",
                            callback: function (value) {
                                return `${value}%`;
                            }
                        },

                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });

        status.textContent =
            `Historical estimates for ${data.location.district} district, using the nearby headquarters grid point. ` +
            "These are not live forecasts.";


        const cardsContainer = document.getElementById("weekly-forecast-cards");

        if (cardsContainer) {
            cardsContainer.innerHTML = forecasts.map(item => {
                const forecastDate = new Date(`${item.date}T12:00:00`);

                const day = forecastDate.toLocaleDateString("en-IN", {
                    weekday: "short"
                });

                const dateLabel = forecastDate.toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short"
                });

                const rainfall = item.rainfall_mm == null
                    ? "N/A"
                    : `${Number(item.rainfall_mm).toFixed(1)} mm`;

                const probability = item.precipitation_probability_percent == null
                    ? "N/A"
                    : `${item.precipitation_probability_percent}%`;

                const summary = item.summary || "Historical estimate";

                return `
            <article class="weekly-card">
                <div class="weekly-card-top">
                    <span class="weekly-card-icon">📊</span>
                    <div>
                        <h3>${day}</h3>
                        <p>${dateLabel}</p>
                    </div>
                </div>

                <p class="weekly-card-summary">${summary}</p>

                <div class="weekly-card-rain">
                    <span>Historical average rainfall</span>
                    <strong>${rainfall}</strong>
                </div>

                <div class="weekly-card-detail">
                    <span>☔ Historical rainy-day frequency</span>
                    <strong>${probability}</strong>
                </div>

                <div class="weekly-card-detail">
                    <span>Historical samples</span>
                    <strong>${item.sample_count}</strong>
                </div>
            </article>
        `;
            }).join("");
        }


    } catch (error) {
        console.error("Weekly forecast error:", error);
        status.textContent = error.message;
    }
}

loadForecast(cityInput.value);
