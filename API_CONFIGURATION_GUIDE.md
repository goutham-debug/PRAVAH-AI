# PRAVAH AI — External API Configuration & Credential Guide

This document provides exact, actionable instructions for configuring external data providers for the PRAVAH AI Urban Operations Intelligence Platform across all six methodology stages.

---

## 1. Open-Meteo Weather API

- **Provider Name:** Open-Meteo Weather & Climate Service
- **Official URL:** [https://open-meteo.com](https://open-meteo.com)
- **API Key Required:** **NO** (Free open-access for non-commercial & municipal evaluation)
- **Environment Variable:** `OPEN_METEO_BASE_URL` (defaults to `https://api.open-meteo.com/v1`)
- **Where to Obtain:** Pre-configured; no token needed.
- **Payment / Approval:** Free tier supports up to 10,000 calls/day without registration.
- **Configuration Instructions:**
  ```bash
  # In your .env file:
  OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1
  ```
- **How to Test Connection:**
  ```powershell
  python -c "import requests; r = requests.get('https://api.open-meteo.com/v1/forecast?latitude=12.9698&longitude=77.7499&hourly=precipitation', timeout=10); print('Status:', r.status_code, 'Hourly mm sample:', r.json()['hourly']['precipitation'][:3])"
  ```
- **Features Affected Without It:** Live hourly precipitation forecasts for the $P$ factor in flood susceptibility screening. (When unreachable, the system falls back to user-selected precipitation scenario presets: Normal, Heavy, Extreme, Cloudburst).

---

## 2. KSNDMC (Karnataka State Natural Disaster Monitoring Centre)

- **Provider Name:** KSNDMC Telemetric Weather & Rain Gauge Station Network
- **Official Registration URL:** [https://ksndmc.org](https://ksndmc.org)
- **API Key Required:** **YES**
- **Environment Variable:** `KSNDMC_API_KEY` and `KSNDMC_URL`
- **Where to Obtain:** Apply through Karnataka State Disaster Management Authority (KSDMA) portal under the Municipal Data Sharing Initiative or email `director@ksndmc.org`.
- **Payment / Approval:** Government departmental MoU required. Free for authorized state/municipal agencies (BBMP, KSDMA, SDRF).
- **Configuration Instructions:**
  ```bash
  KSNDMC_URL=https://ksndmc.org/api/v1/aws/rainfall
  KSNDMC_API_KEY=your_issued_departmental_token_here
  ```
- **How to Test Connection:**
  ```powershell
  python -c "from services.rainfall_service import RainfallService; print(RainfallService().get_rainfall())"
  ```
- **Features Affected Without It:** Real-time telemetric gauge observation for Mahadevapura wards. In its absence, the $P$ factor defaults to `FORECAST` or `MODELLED` rather than `OBSERVED`.

---

## 3. IMD (India Meteorological Department)

- **Provider Name:** India Meteorological Department District Weather Observation Service
- **Official Registration URL:** [https://imd.gov.in](https://imd.gov.in) / [https://mausam.imd.gov.in](https://mausam.imd.gov.in)
- **API Key Required:** **YES**
- **Environment Variable:** `IMD_API_KEY` and `IMD_URL`
- **Where to Obtain:** Submit API access request to IMD National Data Centre (NDC) Pune at `ndc@imd.gov.in`.
- **Payment / Approval:** Institutional access requires departmental approval for government disaster platforms.
- **Configuration Instructions:**
  ```bash
  IMD_URL=https://api.imd.gov.in/v1/weather/observations
  IMD_API_KEY=your_imd_api_key_here
  ```
- **How to Test Connection:**
  Navigate to **Data Operations** (`/authority/data-operations`) in the dashboard or run:
  ```powershell
  curl -s http://127.0.0.1:5000/api/monitor/health
  ```
- **Features Affected Without It:** Verified national gauge observations for HAL Airport / Bengaluru Urban station.

---

## 4. ISRO Bhuvan Geo-Portal (CartoDEM Elevation Data)

- **Provider Name:** ISRO National Remote Sensing Centre (NRSC) Bhuvan Portal
- **Official Registration URL:** [https://bhuvan.nrsc.gov.in](https://bhuvan.nrsc.gov.in)
- **API Key Required:** **YES** (User token)
- **Environment Variable:** `BHUVAN_API_KEY` and `BHUVAN_URL`
- **Where to Obtain:** Register on [bhuvan-app1.nrsc.gov.in/2dresources/thematicServices.php](https://bhuvan-app1.nrsc.gov.in), create an application token under OGC Web Services.
- **Payment / Approval:** Free for non-commercial and public administration use.
- **Configuration Instructions:**
  ```bash
  BHUVAN_URL=https://bhuvan.nrsc.gov.in/api/v1/dem
  BHUVAN_API_KEY=your_bhuvan_token_here
  ```
- **Features Affected Without It:** Live digital elevation tile queries. When unconfigured, PRAVAH AI uses pre-seeded validated SRTM/CartoDEM spot elevations (`KNOWN_WARD_ELEVATIONS`) for the 10 Mahadevapura wards (850m–895m MSL).

---

## 5. BBMP Road Closure & Municipal Inundation Feeds

- **Provider Name:** Bruhat Bengaluru Mahanagara Palike (BBMP) Disaster Operations
- **Official Registration URL:** [https://bbmp.gov.in](https://bbmp.gov.in)
- **API Key Required:** N/A (No public machine-readable API is currently published by BBMP)
- **Environment Variable:** N/A
- **Configuration Instructions:**
  Because BBMP does not publish an automated live road closure feed, road closures are managed through:
  1. The **Scenario Simulator** (`/authority/scenario`) where operators select verified closures.
  2. The **Incident Management** workflow (`/api/incidents`) where citizen reports are verified by officers.
- **How It Behaves:** Road closures applied via the interface are strictly classified as `MODELLED` or `UNVERIFIED` until confirmed by an on-duty officer.

---

## 6. AI Assistant LLM Service (Optional Grounding Adapter)

- **Provider Name:** OpenAI or Google Gemini API
- **Official Registration URL:**
  - OpenAI: [https://platform.openai.com](https://platform.openai.com)
  - Google Gemini: [https://aistudio.google.com](https://aistudio.google.com)
- **API Key Required:** **YES** (Optional)
- **Environment Variable:** `OPENAI_API_KEY` or `GEMINI_API_KEY`
- **Configuration Instructions:**
  ```bash
  OPENAI_API_KEY=sk-...
  # OR
  GEMINI_API_KEY=AIzaSy...
  ```
- **How to Test Connection:**
  Ask a question on the **AI Assistant** tab (`/authority/ai`).
- **Features Affected Without It:**
  **NONE.** If no LLM key is configured, PRAVAH AI uses its internal **deterministic grounded-synthesis engine**, which queries the same algorithmic backend services and formats verified operational answers with zero hallucination.
