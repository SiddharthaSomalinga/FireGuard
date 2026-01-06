# FireGuard Fire Danger Index (McArthur-inspired)

**Short answer:** Yes, this FDI is McArthur-style, but it is an adapted/simplified implementation rather than the canonical McArthur Forest Fire Danger Index (FFDI).

## Canonical McArthur FFDI (reference)
$$
\text{FFDI} = 2 \cdot e^{-0.45 + 0.987 \ln(D) - 0.0345 H + 0.0338 T + 0.0234 V}
$$
- D: drought factor (0–10)
- H: relative humidity (%)
- T: temperature (°C)
- V: wind speed (km/h at 10 m)
- Traits: exponential response, formal drought-factor model, outputs map to Low → Catastrophic.

## What FireGuard implements
- Core function `calculate_fdi(temperature, humidity, wind, days_rain, rain)` in [fdi.py](fdi.py#L408-L419).
- Drivers match McArthur’s intent: temperature, relative humidity, wind speed, and rainfall-derived dryness.
- Dryness is approximated with rainfall amount + days since rain via lookup table [fdi.py](fdi.py#L368-L398), standing in for the McArthur drought factor.
- Wind amplification uses stepped additions rather than exponential terms [fdi.py](fdi.py#L399-L407).
- Output: scalar FDI then category mapping (Blue, Green, Yellow, Orange, Red) [fdi.py](fdi.py#L421-L429).

## Where it diverges from McArthur
1. Linear burn/humidity core instead of the exponential McArthur equation.
2. Implicit drought factor from rain + days, not the canonical drought-factor model.
3. Heuristic thresholds/lookup tables replace fixed McArthur coefficients.
4. Categories differ (Blue → Red vs Low → Catastrophic).

## Recommended wording
Do say
- “A physically motivated, McArthur-style fire danger index with rainfall-adjusted drought modeling.”
- “A deterministic fire danger index based on the principles of the McArthur FFDI, using temperature, humidity, wind, and rainfall-derived dryness.”

Do not say
- “This implements the McArthur Forest Fire Danger Index.”

## Why this adaptation
- Works globally with Open-Meteo data availability.
- Keeps strong sensitivity to wind and dryness while staying transparent and tunable.
- Avoids misrepresenting compliance with the Australian canonical standard.

## Inputs and outputs
- Inputs: temperature (°C), humidity (%), wind (km/h at 10 m), rain (mm for the last rain event), days_rain (days since that rain).
- Output: rounded FDI value and risk label via `fdi_to_category` [fdi.py](fdi.py#L421-L429).

## Limitations / honesty notes
- Not a drop-in replacement for the official McArthur FFDI; drought and fuel models are simplified.
- Exponential response of the canonical FFDI is approximated through wind additions and rainfall tables here.
- Accuracy depends on the quality of historical rain inputs (90-day lookback via Open-Meteo in `get_days_since_last_rain`).
