# 🌍 Earth Data Lab — Climate Intelligence Assistant

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/pytest-20%20passed-brightgreen.svg)](https://pytest.org/)
[![Repository Size](https://img.shields.io/badge/Repo%20Size-%3C%201%20MB-success.svg)]()
[![Branch](https://img.shields.io/badge/Branch-main%20only-informational.svg)]()

> A context-aware, deterministic climate intelligence assistant and scientific dashboard.  
> **No paid API keys, no opaque black-box hallucinations, 100% mathematically verified statistical calculations directly from observed climate records.**

---

## 📌 Executive Summary & Challenge Alignment

| Attribute | Specification |
| :--- | :--- |
| **Intended Persona** | Scientific Climate Data Assistant & Research Analyst |
| **Target Audience** | Researchers, educators, students, and climate analysts seeking reproducible anomaly data |
| **Provisional Vertical** | **Climate Intelligence & Environmental Data Science** *(Provisional — modularly designed to adapt if another challenge vertical is officially confirmed)* |
| **Repository Size** | **~0.22 MB** (Strictly under the 10 MB ceiling) |
| **Deployment Target** | Render / Any WSGI container (`0.0.0.0:$PORT`) |
| **Core Architecture** | Lightweight Flask microservice + NumPy/Pandas compute engine + Chart.js dynamic visualization |

---

## 🧭 Problem Statement & Design Philosophy

Understanding historical global temperature trends is often hindered by two extremes:
1. **Raw static spreadsheets** that are difficult for non-specialists to query and visualize.
2. **Generative AI chatbots** that suffer from hallucinations, fabricated numbers, opaque reasoning, and expensive API token costs.

### The Earth Data Lab Solution
**Earth Data Lab** bridges this gap by combining an interactive visual dashboard with a **transparent, rule-based conversational assistant**. 
- Every number returned by the assistant is calculated on-the-fly using **NumPy and Pandas** from verified time-series data.
- The assistant explicitly separates **empirical observations** (what the instruments recorded) from **physical causal explanations** (what climate models attribute to greenhouse gas forcing or natural cycles).
- The system works **100% offline and free of third-party API dependencies**.

---

## 🏗️ Architecture & Decision Logic Flow

```
+-------------------------------------------------------------------------+
|                              USER BROWSER                               |
|   - Responsive Scientific Dashboard (Chart.js, HTML5, CSS Grid)         |
|   - Conversational Chat Interface & Quick-Prompt Chips                  |
|   - Year Range Filtering, Dataset Switcher & CSV Exporter               |
+------------------------------------+------------------------------------+
                                     |  HTTP REST (JSON)
                                     v
+-------------------------------------------------------------------------+
|                           FLASK APP (app.py)                            |
|   - Security Headers (nosniff, SAMEORIGIN, XSS protection)              |
|   - Routes: / (UI), /api/data, /api/query, /api/export, /api/health     |
+-------------------+--------------------------------+--------------------+
                    |                                |
                    v                                v
+-----------------------------------+  +----------------------------------+
|    ASSISTANT (core/assistant.py)  |  |  DATA LOADER (core/data_loader)  |
| - Intent Classification (Regex)   |  | - Schema & Type Validation       |
| - Entity & Year Extraction        |  | - Monotonic Ordering & Bounds    |
| - Clarification on Ambiguity      |  | - In-Memory Clean DataFrame      |
| - Out-of-Scope Query Guardrails   |  +----------------+-----------------+
+-------------------+---------------+                   |
                    |                                   |
                    v                                   v
+-------------------------------------------------------------------------+
|                  STATISTICS ENGINE (core/statistics_engine.py)          |
| - Ordinary Least Squares (OLS) Linear Trend Slope & Decadal Rate        |
| - Pearson Correlation & Coefficient of Determination (R²)               |
| - Descriptive Statistics (Mean, Median, Standard Deviation, IQR)        |
| - Top N Warmest / Coldest Record Rankings                               |
| - Inter-Era Comparison & Cohen's d Effect Size                          |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                 INSIGHTS ENGINE (core/insights_engine.py)               |
| - Post-1970 Acceleration Detection                                      |
| - Separation: Observed Pattern vs Physical/Causal Attribution           |
+-------------------------------------------------------------------------+
```

### 🧠 Intent Classification State Machine
When a user submits a query, the assistant executes this deterministic decision tree:
1. **Guardrail Check:** If the query asks for daily weather forecasts (e.g. *"will it rain tomorrow"*), stock prices, or unrelated topics, return an informative `OUT_OF_SCOPE` response explaining system boundaries.
2. **Intent Matching:** Regular expression pattern scoring maps the query into one of 7 recognized intents:
   - `TREND_ANALYSIS`: OLS regression, warming rates (°C/decade), acceleration.
   - `WARMEST_COLDEST`: Peak anomaly rankings with uncertainty bounds.
   - `PERIOD_COMPARISON`: Difference between historical baseline vs modern decades + Cohen's d.
   - `AVERAGE_CALCULATION`: Mean, median, and IQR for specified decades or year intervals.
   - `VARIABILITY_ANALYSIS`: Standard deviation ($\sigma$), variance, and decadal spread.
   - `DATA_QUALITY`: Completeness audit, instrument uncertainty, and documented limitations.
   - `DATASET_OVERVIEW`: Provenance, baseline, citations, and spatial coverage.
3. **Parameter Extraction:** Extracts calendar years (e.g., `1880`, `2024`), decades (`1990s`), and top $N$ counts.
4. **Data Slicing & Calculation:** Executes vectorized NumPy/Pandas routines on the active dataset.
5. **Synthesis:** Returns formatted Markdown containing the direct answer, exact numbers, mathematical formula, scientific context, and limitation disclaimers.

---

## 📊 Climate Datasets & Scientific Methodology

### 1. NASA GISTEMP v4 (Observed Instrumental Record)
- **Source:** NASA Goddard Institute for Space Studies (GISS).
- **Official Citation:** GISTEMP Team, 2025: *GISS Surface Temperature Analysis (GISTEMP), version 4*. NASA GISS; Lenssen et al., 2019, *JGR Atmospheres*.
- **Parameter:** Global Land-Ocean Temperature Index (LOTI) anomaly in degrees Celsius (°C).
- **Temporal Span:** 1880 to 2025 (146 annual observations).
- **Climatological Baseline:** **1951–1980 mean** (estimated absolute global mean: **14.0°C / 57.2°F**).
- **Uncertainty Bounds:** Documented 95% confidence intervals ($\pm 0.12^\circ\text{C}$ in the 1880s due to sparse coverage; $\pm 0.04^\circ\text{C}$ in the modern satellite/buoy era).

### 2. Synthetic Scenario (Demonstration & Offline Testing)
- **Source:** Deterministic mathematical simulator (`scripts/create_synthetic_data.py`).
- **Equation:** $y(t) = -0.05 + 0.018t + 0.08\sin\left(\frac{2\pi t}{4.5}\right) + \epsilon$ (linear trend + ENSO-like oscillation + Gaussian noise).
- **Temporal Span:** 1950 to 2030 (81 annual records).
- **Notice:** Clearly marked as **SYNTHETIC** across the UI and assistant answers. Never labeled as real-world measurements.

### 🔬 Scientific Integrity & Attribution Distinction
- **What Statistics Show (Observed Patterns):** Time-series analysis confirms an empirical warming rate of $\approx +0.083^\circ\text{C}/\text{decade}$ across 1880–2025, accelerating to over $+0.20^\circ\text{C}/\text{decade}$ post-1970.
- **What Statistics Cannot Show (Causal Attribution):** Statistical correlation does not establish physical causation. In scientific consensus (e.g. IPCC AR6 WGI Chapter 3), attribution of observed warming to anthropogenic greenhouse gas emissions requires coupled ocean-atmosphere general circulation models (GCMs/CMIP6) with and without human forcings.

---

## 📂 Project Structure

```
Earth_Data_Lab/
├── app.py                     # Flask entry point and REST API routes
├── requirements.txt           # Minimal, pinned dependencies
├── Procfile                   # Process file for Render/Gunicorn
├── render.yaml                # Infrastructure-as-code for 1-click Render deploy
├── .gitignore                 # Excludes caches, venvs, and temp files
├── README.md                  # Comprehensive documentation & student viva guide
├── core/
│   ├── __init__.py
│   ├── data_loader.py         # CSV reader, schema validator, and cacher
│   ├── statistics_engine.py   # Pure NumPy/Pandas math (OLS, Cohen's d, stats)
│   ├── insights_engine.py     # Observed vs Causal research insight generator
│   └── assistant.py           # Context-aware rule-based conversational engine
├── data/
│   ├── metadata.json          # Dataset provenance, citations, and limitations
│   ├── global_temperature_anomalies_nasa_gistemp.csv  # Verified NASA GISTEMP
│   └── synthetic_demo_climate.csv                     # Clearly labeled synthetic demo
├── scripts/
│   ├── fetch_data.py          # NASA GISTEMP automated data updater
│   └── create_synthetic_data.py # Reproducible synthetic dataset generator
├── templates/
│   └── index.html             # Accessible, responsive scientific UI
├── static/
│   ├── css/
│   │   └── styles.css         # WCAG AA accessible theme & layout
│   └── js/
│       └── dashboard.js       # Chart.js rendering, assistant controller, filters
└── tests/
    ├── __init__.py
    ├── test_statistics.py     # 7 unit tests for mathematical accuracy
    ├── test_assistant.py      # 6 unit tests for NLP intent classification
    └── test_api.py            # 7 integration tests for Flask endpoints
```

---

## 🚀 Installation & Local Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.11 and 3.14).
- Windows PowerShell, Command Prompt, or Linux/macOS terminal.

### Step 1: Clone the Repository
```powershell
git clone https://github.com/Shriyash-V/Earth_Data_Lab.git
cd Earth_Data_Lab
```

### Step 2: Create and Activate Virtual Environment (Optional but Recommended)
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Automated Test Suite
```bash
pytest tests/
```
*Expected output:* `20 passed in ~1.3s`.

### Step 5: Launch the Application
```bash
python app.py
```
Open your browser to: **[http://localhost:5000](http://localhost:5000)**

---

## 🧪 Testing Coverage Summary

All core capabilities are covered by 20 automated tests:
1. **Mathematical Accuracy (`tests/test_statistics.py`):**
   - Correctness of sample mean, median, IQR, and standard deviation.
   - Ordinary Least Squares regression slope ($m$) and R² calculation.
   - Top $N$ warmest/coldest sorting and uncertainty retention.
   - Period comparison, mean delta, and Cohen's d effect size.
   - Decadal grouping and temporal completeness percentage.
2. **Intent Classification & Assistant Reasoning (`tests/test_assistant.py`):**
   - Correct detection across 7 core intents.
   - Handling of out-of-scope queries (e.g. daily weather, non-climate topics).
   - Extraction of 4-digit years and top $N$ parameters.
   - Synthetic data disclaimers.
3. **API Integration (`tests/test_api.py`):**
   - `/api/health`: Health monitoring response.
   - `/api/datasets`: Dataset registry payload.
   - `/api/data`: Query filtering and JSON output.
   - `/api/query`: Post request handling and error bounds.
   - `/api/export`: CSV stream generation with metadata comment headers.

---

## ☁️ Step-by-Step Render Deployment Guide

Follow these steps to deploy Earth Data Lab onto [Render](https://render.com) for free:

1. **Sign in to Render:** Go to [dashboard.render.com](https://dashboard.render.com/) and log in with your GitHub account.
2. **Create New Web Service:**
   - Click **New +** > **Web Service**.
   - Select **Build and deploy from a Git repository**.
   - Choose your repository: `Shriyash-V/Earth_Data_Lab`.
3. **Configure Service Settings:**
   - **Name:** `earth-data-lab`
   - **Region:** Choose the closest region (e.g., Singapore, Frankfurt, or Oregon).
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan Type:** `Free`
4. **Environment Variables:**
   - `PYTHON_VERSION`: `3.11.9`
   - `FLASK_ENV`: `production`
5. **Deploy:** Click **Create Web Service**. Render will automatically clone the repository, install dependencies, run Gunicorn, and provide a public HTTPS URL (e.g., `https://earth-data-lab.onrender.com`).
6. **Verify Deployment:** Visit `https://<your-render-url>/api/health` — it should return:
   ```json
   { "status": "healthy", "service": "Earth Data Lab", "version": "1.0.0" }
   ```

---

## 🎓 Viva / Presentation Defense Guide (For B.Tech CSE Students)

If an examiner or judge asks you about this project, here is how to explain and defend every component:

### Q1: "Why did you build a rule-based assistant instead of using an LLM like GPT-4?"
> *"LLMs are generative and probabilistic; they can hallucinate numbers, miscalculate decadal warming rates, and require paid API keys and network connectivity. For scientific data analysis, determinism is paramount. Our assistant parses user intent deterministically and executes exact mathematical calculations using NumPy and Pandas directly on verified climate records. It is fast, free, explainable, and guarantees 100% calculation reproducibility."*

### Q2: "How is the warming rate calculated?"
> *"We use Ordinary Least Squares (OLS) linear regression where the annual temperature anomaly is modeled as $y = mx + c$. The slope $m$ represents the annual rate of temperature change in °C/year. We multiply $m$ by 10 to obtain the decadal warming rate (°C/decade), and compute $R^2$ to measure how much variance in historical temperatures is explained by the linear time trend."*

### Q3: "What is an anomaly and why not use absolute temperatures?"
> *"Absolute temperatures vary greatly over short distances due to elevation and local topography (e.g., a mountain valley vs a hill station). In contrast, temperature anomalies—the departure from a 30-year climatological baseline like 1951–1980—have a spatial correlation radius of up to 1,200 km. Using anomalies allows accurate global averaging even with sparse station distributions."*

### Q4: "How does the assistant distinguish observed patterns from causal explanations?"
> *"Our `insights_engine` enforces a fundamental scientific boundary: statistical time-series analysis proves *that* global temperatures have risen by ~0.83°C since the late 19th century and accelerated post-1970. However, proving *why* (causality) requires physical climate modeling (such as IPCC AR6 CMIP6 simulations comparing natural vs anthropogenic forcings). The assistant explicitly alerts users to this distinction."*

---

## 🔒 Security, Accessibility & Production Best Practices

- **Security Headers:** Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `X-XSS-Protection: 1; mode=block`.
- **Payload Sanitization:** Restricts POST request payloads to 16 KB and input query strings to 500 characters to prevent buffer exhaustion and injection.
- **Zero Secret Exposure:** No API keys, passwords, or credentials are hardcoded or tracked in Git.
- **Accessibility (WCAG 2.1 AA):** High-contrast color palette, semantic HTML5 tags (`<main>`, `<header>`, `<section>`, `role="log"`), visible focus outlines (`:focus-visible`), and screen-reader status live-regions.

---

## 📜 License & Acknowledgments
- **Dataset License:** Public Domain (U.S. Federal Government work — NASA GISS / NOAA NCEI).
- **Application Code:** MIT Open Source License.
