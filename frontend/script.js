
const API_BASE_URL = "";

const searchForm = document.getElementById("search-form");
const cityInput = document.getElementById("city-input");
const forecastButton = document.getElementById("forecast-button");
const buttonText = document.getElementById("button-text");
const messageBox = document.getElementById("message");
const cityOptions = document.getElementById("city-options");
let activeCityOption = -1;

const punjabCities = [
    "Abohar",
    "Adampur",
    "Ahmedgarh",
    "Ajnala",
    "Amloh",
    "Amritsar",
    "Badhni Kalan",
    "Bagha Purana",
    "Balachaur",
    "Banga",
    "Banur",
    "Barnala",
    "Batala",
    "Bathinda",
    "Begowal",
    "Behrampur",
    "Bhagta",
    "Bhawanigarh",
    "Bhikhi",
    "Bhogpur",
    "Bilga",
    "Budhlada",
    "Chamkaur Sahib",
    "Dasuya",
    "Dera Baba Nanak",
    "Dhuri",
    "Dinanagar",
    "Dirba",
    "Faridkot",
    "Fatehgarh Churian",
    "Fazilka",
    "Ferozepur",
    "Garhshankar",
    "Ghanaur",
    "Goniana Mandi",
    "Gurdaspur",
    "Guru Har Sahai",
    "Hajipur",
    "Hariana",
    "Hoshiarpur",
    "Jagraon",
    "Jalandhar",
    "Jandiala",
    "Kapurthala",
    "Kartarpur",
    "Khamanon",
    "Khanna",
    "Kharar",
    "Khem Karan",
    "Kotkapura",
    "Ludhiana",
    "Machhiwara",
    "Majitha",
    "Maler Kotla",
    "Malout",
    "Mansa",
    "Moga",
    "Mohali",
    "Moonak",
    "Morinda",
    "Mukerian",
    "Muktsar",
    "Nabha",
    "Nakodar",
    "Nangal",
    "Nawanshahr",
    "Nurmahal",
    "Pathankot",
    "Patiala",
    "Patti",
    "Phagwara",
    "Phillaur",
    "Qadian",
    "Rahon",
    "Raikot",
    "Rajpura",
    "Rampura Phul",
    "Rupnagar",
    "Samana",
    "Samrala",
    "Sanaur",
    "Sangrur",
    "Sardulgarh",
    "Shahkot",
    "Sirhind",
    "Sultanpur Lodhi",
    "Sunam",
    "Talwandi Sabo",
    "Tanda",
    "Tarn Taran",
    "Zira",
    "Zirakpur",
];

function closeCityOptions() {
    cityOptions.hidden = true;
    cityInput.setAttribute("aria-expanded", "false");
    cityInput.removeAttribute("aria-activedescendant");
    activeCityOption = -1;
}

function renderCityOptions(search = "") {
    const query = search.trim().toLocaleLowerCase();
    const matches = punjabCities.filter((city) =>
        city.toLocaleLowerCase().includes(query)
    );

    cityOptions.replaceChildren();
    activeCityOption = -1;
    cityInput.removeAttribute("aria-activedescendant");

    if (!matches.length) {
        const emptyState = document.createElement("p");
        emptyState.className = "city-options-empty";
        emptyState.textContent = "No matching city. You can still type a Punjab place name.";
        cityOptions.append(emptyState);
    } else {
        matches.forEach((city, index) => {
            const option = document.createElement("button");
            option.type = "button";
            option.className = "city-option";
            option.id = `city-option-${index}`;
            option.setAttribute("role", "option");
            option.setAttribute("aria-selected", "false");
            option.dataset.city = city;

            const cityName = document.createElement("span");
            cityName.className = "city-option-name";
            cityName.textContent = city;

            const locationLabel = document.createElement("span");
            locationLabel.className = "city-option-detail";
            locationLabel.textContent = "Punjab";

            option.append(cityName, locationLabel);
            option.addEventListener("click", () => {
                cityInput.value = city;
                closeCityOptions();
                cityInput.focus();
            });
            cityOptions.append(option);
        });
    }

    cityOptions.hidden = false;
    cityInput.setAttribute("aria-expanded", "true");
}

cityInput.addEventListener("focus", () => renderCityOptions());
cityInput.addEventListener("input", () => renderCityOptions(cityInput.value));
cityInput.addEventListener("keydown", (event) => {
    if (
        (event.key === "ArrowDown" || event.key === "ArrowUp")
        && cityOptions.hidden
    ) {
        renderCityOptions(cityInput.value);
    }
    const options = [...cityOptions.querySelectorAll(".city-option")];

    if (event.key === "ArrowDown" && options.length) {
        event.preventDefault();
        if (cityOptions.hidden) renderCityOptions(cityInput.value);
        activeCityOption = Math.min(activeCityOption + 1, options.length - 1);
    } else if (event.key === "ArrowUp" && options.length) {
        event.preventDefault();
        activeCityOption = Math.max(activeCityOption - 1, 0);
    } else if (
        event.key === "Enter"
        && !cityOptions.hidden
        && activeCityOption >= 0
        && options[activeCityOption]
    ) {
        event.preventDefault();
        cityInput.value = options[activeCityOption].dataset.city;
        closeCityOptions();
    } else if (event.key === "Escape") {
        closeCityOptions();
        return;
    } else {
        return;
    }

    options.forEach((option, index) => {
        option.setAttribute(
            "aria-selected",
            String(index === activeCityOption)
        );
    });
    if (options[activeCityOption]) {
        cityInput.setAttribute(
            "aria-activedescendant",
            options[activeCityOption].id
        );
        options[activeCityOption].scrollIntoView({ block: "nearest" });
    } else {
        cityInput.removeAttribute("aria-activedescendant");
    }
});

cityInput.addEventListener("blur", (event) => {
    if (!cityOptions.contains(event.relatedTarget)) closeCityOptions();
});

document.addEventListener("pointerdown", (event) => {
    if (!event.target.closest(".city-picker")) closeCityOptions();
});

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
    const icons = {
        0: "☀️",
        1: "🌤️",
        2: "⛅",
        3: "☁️",
        45: "🌫️",
        48: "🌫️",
        51: "🌦️",
        53: "🌦️",
        55: "🌧️",
        56: "🌧️",
        57: "🌧️",
        61: "🌦️",
        63: "🌧️",
        65: "🌧️",
        66: "🌧️",
        67: "🌧️",
        71: "🌨️",
        73: "🌨️",
        75: "❄️",
        77: "🌨️",
        80: "🌦️",
        81: "🌧️",
        82: "⛈️",
        85: "🌨️",
        86: "❄️",
        95: "⛈️",
        96: "⛈️",
        99: "⛈️",
    };

    return icons[code] || "🌤️";
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
    const current = data.current_conditions;

    document.getElementById("current-temperature").textContent =
        `${formatNumber(current.temperature_c)}°C`;
    document.getElementById("current-precipitation").textContent =
        `${formatNumber(current.precipitation_mm)} mm`;
    document.getElementById("current-humidity").textContent =
        `${formatNumber(current.relative_humidity_percent, 0)}%`;
    document.getElementById("current-wind").textContent =
        `${formatNumber(current.wind_speed_kmh)} km/h`;
    document.getElementById("current-feels-like").textContent =
        `Feels like ${formatNumber(current.feels_like_c)}°C`;
    document.getElementById("current-weather-summary").textContent =
        `${current.summary} · ${location.city}`;
    document.getElementById("current-weather-updated").textContent =
        `Latest provider update: ${current.time.replace("T", " ")} (${location.timezone || "local time"})`;

    // Update the new live forecast card
    const liveRainfall = document.getElementById("live-rainfall");
    const liveSummary = document.getElementById("live-forecast-summary");
    const liveProbability = document.getElementById("live-rain-probability");
    const liveMaxTemp = document.getElementById("live-temp-max");
    const liveMinTemp = document.getElementById("live-temp-min");
    const liveDate = document.getElementById("live-forecast-date");
    const liveIcon = document.querySelector(".forecast-weather-icon");

    if (liveRainfall) {
        liveRainfall.innerHTML =
            `${formatNumber(forecast.rainfall_mm)} <span>mm</span>`;
    }

    if (liveSummary) {
        liveSummary.textContent =
            forecast.summary || "Forecast available";
    }

    if (liveProbability) {
        liveProbability.textContent =
            forecast.precipitation_probability_percent == null
                ? "Unavailable"
                : `${forecast.precipitation_probability_percent}%`;
    }

    if (liveMaxTemp) {
        liveMaxTemp.textContent =
            `${formatNumber(forecast.temperature_max_c)}°C`;
    }

    if (liveMinTemp) {
        liveMinTemp.textContent =
            `${formatNumber(forecast.temperature_min_c)}°C`;
    }

    if (liveDate) {
        liveDate.textContent =
            `Forecast date: ${formatDate(data.forecast_date)} · ${location.city}`;
    }

    if (liveIcon) {
        liveIcon.textContent = weatherIcon(forecast.weather_code);
    }


    document.getElementById("forecast-location").textContent =
        `${location.city}'s forecast`;

    document.getElementById("forecast-date").textContent =
        formatDate(data.forecast_date);

    document.getElementById("rainfall-value").textContent =
        formatNumber(forecast.rainfall_mm);

    document.getElementById("weather-summary").textContent =
        forecast.summary || "Forecast available";

    document.getElementById("weather-icon").textContent =
        weatherIcon(forecast.weather_code);

    const rainfall = forecast.rainfall_mm;

    document.getElementById("rainfall-description").textContent =
        rainfall === null || rainfall === undefined
            ? "The provider did not return a rainfall amount."
            : `${formatNumber(rainfall)} mm of total rainfall is forecast for this day.`;

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

    document.getElementById("max-temperature").textContent =
        `${formatNumber(forecast.temperature_max_c)}°C`;

    document.getElementById("min-temperature").textContent =
        `${formatNumber(forecast.temperature_min_c)}°C`;

    document.getElementById("rain-category").textContent =
        rainfallCategory(rainfall);

    document.getElementById("location-name").textContent =
        location.city;

    document.getElementById("location-country").textContent =
        location.country || "Country unavailable";

    updateApiStatus("Connected", true);
}

async function loadForecast(city, showSuccess = true) {
    hideMessage();

    forecastButton.disabled = true;
    buttonText.textContent = "Loading...";

    updateApiStatus("Fetching forecast...", false);

    try {
        const url = new URL(`${API_BASE_URL}/predict`, window.location.origin);
        url.searchParams.set("city", city);

        const response = await fetch(url);

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error("The backend returned an unreadable response.");
        }

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

        if (showSuccess) {
            showMessage(
                `Current conditions and forecast loaded for ${data.location.city}, Punjab.`,
                "success"
            );
        }
    } catch (error) {
        let errorMessage = error.message || "An unexpected error occurred.";

        if (error instanceof TypeError) {
            updateApiStatus("Connection issue", false);
            errorMessage =
                `Cannot connect to the backend. Start the app and open ${window.location.origin}.`;
        } else {
            updateApiStatus("Connected", true);
        }

        showMessage(errorMessage, "error");
    } finally {
        forecastButton.disabled = false;
        buttonText.textContent = "Get forecast";
    }
}

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const city = cityInput.value.trim();

    if (city.length < 2) {
        showMessage("Please enter a city name with at least two characters.", "error");
        return;
    }

    loadForecast(city);
});

// Load the default city when the page opens.
loadForecast(cityInput.value.trim());

// Refresh provider conditions and forecasts hourly without a key.
setInterval(() => {
    const city = cityInput.value.trim();
    if (city.length >= 2) {
        loadForecast(city, false);
    }
}, 60 * 60 * 1000);

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

async function loadMonthlyAnalytics() {
    const status = document.getElementById("analytics-status");
    const canvas = document.getElementById("monthly-rainfall-chart");

    if (!status || !canvas) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/analytics/monthly`
        );

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

        if (typeof Chart === "undefined") {
            throw new Error(
                "Chart.js did not load. Check your internet connection."
            );
        }

        const months = data.monthly_statistics;


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
            `Loaded historical data from ${data.source}. ` +
            `Wettest month by average daily rainfall: ` +
            `${data.wettest_month_by_average_daily_rainfall || "Unavailable"}.`;

    } catch (error) {
        status.textContent = error.message;
        console.error("Monthly analytics error:", error);
    }
}

loadMonthlyAnalytics();


let weeklyRainfallChart = null;

async function loadWeeklyForecast(city) {
    const status = document.getElementById("weekly-forecast-status");
    const canvas = document.getElementById("weekly-rainfall-chart");

    if (!status || !canvas) {
        return;
    }

    if (!city || city.trim().length < 2) {
        status.textContent = "Please enter a valid city name.";
        return;
    }

    status.textContent = `Loading 7-day forecast for ${city}...`;

    try {
        const url = new URL(
            `${API_BASE_URL}/predict/weekly`,
            window.location.origin
        );
        url.searchParams.set("city", city.trim());

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
                        label: "Expected rainfall (mm)",
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
                        label: "Rain probability (%)",
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
                                    return `Rain probability: ${context.parsed.y ?? "N/A"}%`;
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
                            text: "Rain probability (%)",
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
            `Showing the 7-day forecast for ${data.location.city}. ` +
            "Rainfall is measured in millimetres (mm).";


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

                const maxTemp = item.temperature_max_c == null
                    ? "N/A"
                    : `${item.temperature_max_c}°C`;

                const minTemp = item.temperature_min_c == null
                    ? "N/A"
                    : `${item.temperature_min_c}°C`;

                const summary = item.summary || "Forecast unavailable";

                const icon = Number(item.rainfall_mm) > 0
                    ? "🌧️"
                    : "🌤️";

                return `
            <article class="weekly-card">
                <div class="weekly-card-top">
                    <span class="weekly-card-icon">${icon}</span>
                    <div>
                        <h3>${day}</h3>
                        <p>${dateLabel}</p>
                    </div>
                </div>

                <p class="weekly-card-summary">${summary}</p>

                <div class="weekly-card-rain">
                    <span>Expected rainfall</span>
                    <strong>${rainfall}</strong>
                </div>

                <div class="weekly-card-detail">
                    <span>☔ Rain chance</span>
                    <strong>${probability}</strong>
                </div>

                <div class="weekly-card-detail">
                    <span>🌡️ Temperature</span>
                    <strong>${maxTemp} / ${minTemp}</strong>
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
