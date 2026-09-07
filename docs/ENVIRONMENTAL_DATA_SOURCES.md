# Environmental Data Sources

Ambient Guard uses free public APIs for environmental data. This document provides
attribution and resolution details for each provider.

---

## Open-Meteo (Weather + UV)

**Provider:** Open-Meteo
**URL:** https://open-meteo.com/
**Attribution:** Open-Meteo (CC BY 4.0)

### Variables Used
- `temperature_2m` — Temperature at 2m height
- `relative_humidity_2m` — Relative humidity at 2m
- `wind_speed_10m` — Wind speed at 10m
- `precipitation` — Precipitation
- `uv_index` — UV index
- `weather_code` — WMO weather code

### Resolution
- **Geographic coverage:** Global
- **Spatial resolution:** ~25-50 km (varies by region)
- **Native temporal resolution:** Hourly
- **API output resolution:** Hourly
- **Forecast horizon:** 16 days

### Known Limitations
- UV index is clear-sky; actual UV depends on cloud cover
- No pollen data
- No real-time observations; model-based estimates

---

## Open-Meteo Air Quality (CAMS Global)

**Provider:** Open-Meteo (air-quality-api.open-meteo.com)
**Upstream Model:** CAMS Global Atmospheric Composition Forecast
**Attribution:** 
- Open-Meteo (CC BY 4.0)
- Copernicus Atmosphere Monitoring Service (CAMS)

### Variables Used
- `pm2_5` — PM2.5 (µg/m³)
- `pm10` — PM10 (µg/m³)
- `ozone` — Ozone (µg/m³)
- `nitrogen_dioxide` — NO2 (µg/m³)
- `us_aqi` — US EPA Air Quality Index

### Resolution
- **Geographic coverage:** Global
- **Spatial resolution:** ~40 km (CAMS Global)
- **Native temporal resolution:** 3-hourly (CAMS Global)
- **API output resolution:** Hourly (interpolated from 3-hourly model)
- **Forecast horizon:** 5 days

### Known Limitations
- **Critical:** Native CAMS Global resolution is 3-hourly; hourly API values are
  interpolated from 3-hourly model output.
- **Do NOT justify narrowly separated hourly recommendations** (e.g., 19:00 vs 20:00)
  based solely on interpolated air-quality values. The underlying model does not
  have hourly precision.
- Spatial resolution (~40 km) may not capture local pollution sources.
- No indoor air quality; outdoor estimates only.

### Attribution Requirements
- Open-Meteo: CC BY 4.0 — must cite Open-Meteo
- CAMS: Must cite Copernicus Atmosphere Monitoring Service

---

## Time Alignment Policy

### User Planned Time → Environmental Evidence

When a user plans an activity at a specific time (e.g., 21:48), the system:

1. **Snaps to nearest hour** for environmental data lookup
2. **Preserves both timestamps** in the response:
   - `planned_time`: User's intended time (e.g., 21:48)
   - `environmental_evidence_time`: The hour-aligned time used (e.g., 21:00 or 22:00)

### Example
```json
{
  "planned_time": "2026-09-07T21:48:00",
  "planned_window": {
    "time": "2026-09-07T21:48:00",
    "environmental_evidence_time": "2026-09-07T22:00:00",
    "data_kind": "forecast"
  }
}
```

### Implementation
- Weather data: Nearest hour is selected from hourly series
- Air quality: **Interpolated from 3-hourly CAMS Global model**
  - Hourly values between native model times (00:00, 03:00, 06:00, ...) are interpolated
  - **Do NOT claim hourly precision for air-quality forecasts**

### Forecast vs Observed
- `kind="observed"`: Hour is at or before the fetch time (current conditions)
- `kind="forecast"`: Hour is after the fetch time (predicted conditions)
- All air-quality data is forecast (model-based, not real-time sensor network)

---

## Data Quality Notes

### Air Quality Index Standard
Ambient Guard uses **US EPA AQI** as provided by Open-Meteo:
- Good: 0-50
- Moderate: 51-100
- Unhealthy for Sensitive Groups: 101-150
- Unhealthy: 151-200
- Very Unhealthy: 201-300
- Hazardous: 301+

### Quality Classification
Each AQI observation carries:
- `aqi_standard: "us_epa"` — Explicit standard
- `quality: "moderate"` — Category label

### Missing Data
- If a metric is unavailable, it is skipped (never fabricated)
- `missing_metrics` field in response lists unavailable data

---

## Interpolation Disclaimer

**Air quality hourly values are interpolated from 3-hourly model output.**

Ambient Guard does **NOT** claim hourly precision for air-quality forecasts. The
system reports the interpolated values but users should understand:

1. The underlying CAMS Global model has 3-hourly native resolution
2. Hourly differences in air quality may not be physically meaningful
3. Do not make fine-grained decisions (e.g., "wait 30 minutes for better air")
   based on interpolated hourly values

This is documented in the `limitations` field when alternative windows are evaluated.
