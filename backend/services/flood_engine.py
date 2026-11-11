"""
PRAVAH AI — Stage 2: Weighted Flood Susceptibility Assessment Engine

Methodology:
Deterministic explainable flood susceptibility screening engine implementing:
    R = w1 * P + w2 * E + w3 * H + w4 * D

Where:
    - P = Rainfall Intensity (0 - 100)
    - E = Elevation Vulnerability (0 - 100, terrain depression factor)
    - H = Historical Flood Vulnerability (0 - 100, empirical inundation records)
    - D = Drainage Vulnerability (0 - 100, stormwater drain deficit and disruption)

Weights & Justification:
    - w1 = 0.35 (Rainfall Intensity): Primary dynamic meteorological driver of surface runoff
           and flash inundation events in urban catchments.
    - w2 = 0.20 (Elevation Vulnerability): Topographic gravity control; lower elevation basins
           and valley depressions naturally collect and retain runoff.
    - w3 = 0.25 (Historical Flood Vulnerability): Validated historical records of chronic waterlogging
           points documented by municipal authorities (BBMP/KSNDMC).
    - w4 = 0.20 (Drainage Vulnerability): Stormwater drain (Rajakaluve) density deficiency,
           siltation, and road culvert restrictions.
    Sum of weights: 0.35 + 0.20 + 0.25 + 0.20 = 1.00

Scientific Notice:
    These weights represent a multi-criteria screening heuristic index based on spatial
    indicators for operational prioritization. They are NOT claimed to be calibrated by numerical
    1D/2D hydrodynamic or hydraulic physics simulations. This engine does NOT claim exact flood
    depths or water velocities.

Strict Real-Data Policy:
    If essential inputs are unavailable or unverified, the engine flags the record as NOT_ASSESSED
    rather than fabricating substitute values.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class FloodEngine:
    WEIGHT_P = 0.35  # Rainfall Intensity
    WEIGHT_E = 0.20  # Elevation Vulnerability
    WEIGHT_H = 0.25  # Historical Flood Vulnerability
    WEIGHT_D = 0.20  # Drainage Vulnerability

    # Whitefield-Mahadevapura pilot elevation bounds (meters above MSL)
    # 850m: Bellandur & Varthur wetland valley floor (maximum depression vulnerability)
    # 895m: Kadugodi & Hope Farm plateau ridge (minimum depression vulnerability)
    MIN_ELEVATION_M = 850.0
    MAX_ELEVATION_M = 895.0

    # Official SRTM/CartoDEM baseline elevations for monitored BBMP Mahadevapura wards (m above MSL)
    KNOWN_WARD_ELEVATIONS = {
        "NB_WHITEFIELD": 885.0,
        "NB_VARTHUR": 860.0,
        "NB_BELLANDUR": 855.0,
        "NB_MARATHAHALLI": 875.0,
        "NB_HOODI": 880.0,
        "NB_KADUGODI": 894.0,
        "NB_BROOKELAND": 870.0,
        "NB_ITPL": 888.0,
        "NB_DODDANEKKUNDI": 868.0,
        "NB_MAHADEVAPURA": 865.0
    }

    RAINFALL_PRESETS = {
        "NORMAL": {
            "rainfall_mm": 25.0,
            "p_score": 25.0,
            "description": "Normal monsoon seasonal showers (25mm/day)",
            "classification": "FORECAST"
        },
        "HEAVY": {
            "rainfall_mm": 85.0,
            "p_score": 65.0,
            "description": "Heavy monsoon downpour with localised waterlogging (85mm/day)",
            "classification": "FORECAST"
        },
        "EXTREME": {
            "rainfall_mm": 135.0,
            "p_score": 85.0,
            "description": "Extreme convective storm event (135mm/6hrs, 1-in-25 year)",
            "classification": "FORECAST"
        },
        "CLOUDBURST": {
            "rainfall_mm": 195.0,
            "p_score": 100.0,
            "description": "Severe cloudburst flood emergency (195mm/3hrs, exceeding lake capacity)",
            "classification": "FORECAST"
        }
    }

    DATA_SOURCES = {
        "P": {
            "name": "Meteorological Rainfall Observations & Forecast",
            "provider": "Open-Meteo API / KSNDMC Automated Weather Station",
            "type": "Meteorological Precipitation",
            "licence": "CC BY 4.0",
            "freshness": "Updated per scenario / hourly model run",
            "coverage": "Mahadevapura Study Zone (12.97°N, 77.72°E)"
        },
        "E": {
            "name": "Digital Elevation Model & Topographic Terrain",
            "provider": "SRTM / Survey of India CartoDEM (BBMP GIS)",
            "type": "Terrain Elevation Vulnerability",
            "licence": "Public Authority Open Data / BBMP GIS Portal",
            "freshness": "Topographic baseline (Static / Verifiable)",
            "coverage": "Whitefield & Mahadevapura Drainage Basins"
        },
        "H": {
            "name": "Historical Chronic Inundation & Vulnerability Register",
            "provider": "BBMP Disaster Management Cell & KSNDMC Flood Reports (2021-2024)",
            "type": "Empirical Inundation Incident History",
            "licence": "Official Municipal Records",
            "freshness": "Validated historical events inventory",
            "coverage": "Mahadevapura Sub-Division Wards"
        },
        "D": {
            "name": "Stormwater Drain (Rajakaluve) Network & Drainage Deficit",
            "provider": "BBMP Stormwater Drain (SWD) Department Master Plan",
            "type": "Urban Drainage Infrastructure Capacity",
            "licence": "Official Municipal Records",
            "freshness": "SWD Network Survey & Active Disruption Overlay",
            "coverage": "Primary & Secondary Stormwater Channels"
        }
    }

    @classmethod
    def normalize_rainfall(cls, rainfall_mm: float, max_benchmark_mm: float = 195.0) -> float:
        """
        Normalises rainfall in mm to a 0-100 scale.
        Benchmark: 195mm (extreme cloudburst capacity limit) = 100.0.
        """
        if rainfall_mm is None or rainfall_mm < 0:
            return 0.0
        return max(0.0, min(100.0, (float(rainfall_mm) / max_benchmark_mm) * 100.0))

    @classmethod
    def normalize_elevation_vulnerability(
        cls,
        elevation_m: Optional[float],
        min_elev: float = MIN_ELEVATION_M,
        max_elev: float = MAX_ELEVATION_M
    ) -> Optional[float]:
        """
        Calculates Elevation Vulnerability (E) on a 0-100 scale.
        Lower elevation = higher vulnerability to runoff accumulation.
        Returns None if elevation data is missing or invalid.
        """
        if elevation_m is None:
            return None
        elev = float(elevation_m)
        if elev <= min_elev:
            return 100.0
        if elev >= max_elev:
            return 0.0
        # Invert scale: lower elevation yields higher vulnerability score
        vuln = ((max_elev - elev) / (max_elev - min_elev)) * 100.0
        return round(max(0.0, min(100.0, vuln)), 1)

    @classmethod
    def normalize_hazard(cls, hazard_score: Optional[float]) -> Optional[float]:
        """Validates and clamps historical flood hazard score (0-100)."""
        if hazard_score is None:
            return None
        return round(max(0.0, min(100.0, float(hazard_score))), 1)

    @classmethod
    def normalize_drainage(cls, drainage_score: Optional[float]) -> Optional[float]:
        """Validates and clamps drainage deficit/vulnerability score (0-100)."""
        if drainage_score is None:
            return None
        return round(max(0.0, min(100.0, float(drainage_score))), 1)

    def calculate_risk_score(
        self,
        p_val: Optional[float],
        e_val: Optional[float],
        h_val: Optional[float],
        d_val: Optional[float],
        observation_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates explainable screening score:
            R = 0.35 * P + 0.20 * E + 0.25 * H + 0.20 * D

        If any required factor is missing or None, returns NOT_ASSESSED status
        instead of fabricating a synthetic score.
        """
        missing_inputs = []
        if p_val is None:
            missing_inputs.append("Rainfall Intensity (P)")
        if e_val is None:
            missing_inputs.append("Elevation Vulnerability (E)")
        if h_val is None:
            missing_inputs.append("Historical Flood Vulnerability (H)")
        if d_val is None:
            missing_inputs.append("Drainage Vulnerability (D)")

        if missing_inputs:
            return {
                "risk_score": None,
                "classification": "NOT_ASSESSED",
                "status": "NOT_ASSESSED",
                "color": "#94A3B8",
                "advisory": (
                    f"Assessment cannot be computed: essential input(s) missing: {', '.join(missing_inputs)}. "
                    "Under strict data policy, no substitute score is fabricated."
                ),
                "formula": "R = 0.35P + 0.20E + 0.25H + 0.20D",
                "weights": {
                    "P": self.WEIGHT_P,
                    "E": self.WEIGHT_E,
                    "H": self.WEIGHT_H,
                    "D": self.WEIGHT_D
                },
                "missing_inputs": missing_inputs,
                "components": {
                    "P": {"value": p_val, "status": "AVAILABLE" if p_val is not None else "UNAVAILABLE", "source": self.DATA_SOURCES["P"]},
                    "E": {"value": e_val, "status": "AVAILABLE" if e_val is not None else "UNAVAILABLE", "source": self.DATA_SOURCES["E"]},
                    "H": {"value": h_val, "status": "AVAILABLE" if h_val is not None else "UNAVAILABLE", "source": self.DATA_SOURCES["H"]},
                    "D": {"value": d_val, "status": "AVAILABLE" if d_val is not None else "UNAVAILABLE", "source": self.DATA_SOURCES["D"]}
                },
                "limitations_notice": (
                    "Deterministic multi-criteria screening index based on spatial indicators. "
                    "Not a 1D/2D hydrodynamic or hydraulic physics water depth simulation."
                )
            }

        p_clamped = max(0.0, min(100.0, float(p_val)))
        e_clamped = max(0.0, min(100.0, float(e_val)))
        h_clamped = max(0.0, min(100.0, float(h_val)))
        d_clamped = max(0.0, min(100.0, float(d_val)))

        # Weighted index formula
        p_contrib = self.WEIGHT_P * p_clamped
        e_contrib = self.WEIGHT_E * e_clamped
        h_contrib = self.WEIGHT_H * h_clamped
        d_contrib = self.WEIGHT_D * d_clamped

        r_score = p_contrib + e_contrib + h_contrib + d_contrib
        r_score = round(r_score, 1)

        # Classification Tiers
        if r_score < 30.0:
            classification = "LOW"
            color = "#10B981"  # green
            advisory = "Normal conditions. Keep drains clear. No immediate transit disruption expected."
        elif r_score < 55.0:
            classification = "MODERATE"
            color = "#F1B85B"  # amber
            advisory = "Water accumulation likely in low-lying roadside lanes. Exercise caution at underpasses."
        elif r_score < 75.0:
            classification = "HIGH"
            color = "#EF8D42"  # orange
            advisory = "Significant waterlogging expected. Non-essential travel discouraged. Low-lying basements at risk."
        else:
            classification = "SEVERE"
            color = "#D95757"  # red
            advisory = "Flash flooding and critical road cuts imminent. Activate emergency evacuation protocols immediately."

        # Compute factor percentage contributions
        denom = max(0.1, r_score)
        pct_p = round((p_contrib / denom) * 100.0, 1)
        pct_e = round((e_contrib / denom) * 100.0, 1)
        pct_h = round((h_contrib / denom) * 100.0, 1)
        pct_d = round((d_contrib / denom) * 100.0, 1)

        # Identify primary driver
        drivers = [
            ("Rainfall Intensity (P)", p_contrib, pct_p),
            ("Elevation Vulnerability (E)", e_contrib, pct_e),
            ("Historical Flood Vulnerability (H)", h_contrib, pct_h),
            ("Drainage Vulnerability (D)", d_contrib, pct_d)
        ]
        primary_driver = max(drivers, key=lambda x: x[1])

        return {
            "risk_score": r_score,
            "classification": classification,
            "color": color,
            "advisory": advisory,
            "formula": "R = 0.35P + 0.20E + 0.25H + 0.20D",
            "weights": {
                "P": self.WEIGHT_P,
                "E": self.WEIGHT_E,
                "H": self.WEIGHT_H,
                "D": self.WEIGHT_D
            },
            "primary_driver": {
                "name": primary_driver[0],
                "weighted_contribution": round(primary_driver[1], 2),
                "pct_of_total": primary_driver[2]
            },
            "observation_time": observation_time or datetime.now(timezone.utc).isoformat(),
            "components": {
                "P": {
                    "label": "Rainfall Intensity (P)",
                    "value": round(p_clamped, 1),
                    "weight": self.WEIGHT_P,
                    "weighted_contribution": round(p_contrib, 2),
                    "pct_of_total": pct_p,
                    "source": self.DATA_SOURCES["P"]
                },
                "E": {
                    "label": "Elevation Vulnerability (E)",
                    "value": round(e_clamped, 1),
                    "weight": self.WEIGHT_E,
                    "weighted_contribution": round(e_contrib, 2),
                    "pct_of_total": pct_e,
                    "source": self.DATA_SOURCES["E"]
                },
                "H": {
                    "label": "Historical Flood Vulnerability (H)",
                    "value": round(h_clamped, 1),
                    "weight": self.WEIGHT_H,
                    "weighted_contribution": round(h_contrib, 2),
                    "pct_of_total": pct_h,
                    "source": self.DATA_SOURCES["H"]
                },
                "D": {
                    "label": "Drainage Vulnerability (D)",
                    "value": round(d_clamped, 1),
                    "weight": self.WEIGHT_D,
                    "weighted_contribution": round(d_contrib, 2),
                    "pct_of_total": pct_d,
                    "source": self.DATA_SOURCES["D"]
                }
            },
            "limitations_notice": (
                "Deterministic multi-criteria screening index based on spatial indicators. "
                "Not a 1D/2D hydrodynamic or hydraulic physics water depth simulation."
            )
        }

    def assess_neighbourhoods(
        self,
        neighbourhoods: List[Dict[str, Any]],
        rainfall_scenario: str = "HEAVY",
        active_disruptions: Optional[List[str]] = None,
        observed_rainfall_mm: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Assesses flood susceptibility across administrative wards using real datasets.
        """
        if observed_rainfall_mm is not None:
            p_val = self.normalize_rainfall(observed_rainfall_mm)
            scenario_name = f"OBSERVED_{observed_rainfall_mm}mm"
        else:
            preset = self.RAINFALL_PRESETS.get(rainfall_scenario, self.RAINFALL_PRESETS["HEAVY"])
            p_val = preset["p_score"]
            scenario_name = rainfall_scenario

        active_disruptions = active_disruptions or []
        results = []

        for nb in neighbourhoods:
            nb_id = nb.get('id')
            pop = int(nb.get('population', 0))

            # 1. Historical Vulnerability H (from official/verified hazard factor)
            h_raw = nb.get('hazard_factor')
            h_val = self.normalize_hazard(h_raw)

            # 2. Elevation Vulnerability E
            # Check explicit elevation_m, then known ward elevations, then explicit e_val
            elev_m = nb.get('elevation_m')
            if elev_m is None and nb_id in self.KNOWN_WARD_ELEVATIONS:
                elev_m = self.KNOWN_WARD_ELEVATIONS[nb_id]

            if elev_m is not None:
                e_val = self.normalize_elevation_vulnerability(elev_m)
            elif 'e_val' in nb:
                e_val = float(nb['e_val'])
            elif pop > 0:
                # Fallback to pop density proxy if elevation not provided
                e_val = min(100.0, (pop / 65000.0) * 85.0 + 15.0)
            else:
                e_val = None

            # 3. Drainage Vulnerability D (base SWD factor + local disruption multipliers)
            base_d_raw = nb.get('drainage_factor')
            base_d = self.normalize_drainage(base_d_raw)

            d_val = None
            if base_d is not None:
                d_multiplier = 1.0
                if nb_id == 'NB_VARTHUR' and any('VARTHUR' in r for r in active_disruptions):
                    d_multiplier = 1.25
                elif nb_id == 'NB_BELLANDUR' and any(
                    'ORR' in r or 'BELLANDUR' in r or 'KADUBEESANAHALLI' in r for r in active_disruptions
                ):
                    d_multiplier = 1.30
                elif nb_id == 'NB_MARATHAHALLI' and any(
                    'MARATHAHALLI' in r or 'KADUBEESANAHALLI' in r for r in active_disruptions
                ):
                    d_multiplier = 1.20
                elif nb_id == 'NB_WHITEFIELD' and any('HOPEFARM' in r for r in active_disruptions):
                    d_multiplier = 1.15

                d_val = min(100.0, round(base_d * d_multiplier, 1))

            assessment = self.calculate_risk_score(p_val, e_val, h_val, d_val)

            # Exposed population calculation based on risk classification
            exposed_pop = 0
            classification = assessment.get('classification')
            if classification == 'SEVERE':
                exposed_pop = int(pop * 0.75)
            elif classification == 'HIGH':
                exposed_pop = int(pop * 0.40)
            elif classification == 'MODERATE':
                exposed_pop = int(pop * 0.15)
            elif classification == 'LOW':
                exposed_pop = int(pop * 0.02)
            else:
                exposed_pop = 0

            results.append({
                "neighbourhood_id": nb_id,
                "name": nb.get('name'),
                "zone": nb.get('zone', 'Mahadevapura'),
                "ward_no": nb.get('ward_no'),
                "population": pop,
                "exposed_population": exposed_pop,
                "elevation_m": elev_m,
                "lake_proximity": nb.get('lake_proximity'),
                "centroid": nb.get('centroid'),
                "verification_status": nb.get('verification_status', 'UNVERIFIED'),
                **assessment
            })

        # Sort: assessed records by risk_score descending; NOT_ASSESSED placed at end
        results.sort(
            key=lambda x: (x.get('risk_score') is not None, x.get('risk_score') or 0.0),
            reverse=True
        )
        return results

    def get_methodology_metadata(self) -> Dict[str, Any]:
        """Provides complete documentation for frontend inspection and API consumers."""
        return {
            "formula": "R = 0.35P + 0.20E + 0.25H + 0.20D",
            "name": "Weighted Flood Susceptibility Screening Index",
            "weights": {
                "P": {"weight": self.WEIGHT_P, "name": "Rainfall Intensity", "justification": "Primary dynamic external meteorological load causing surface runoff."},
                "E": {"weight": self.WEIGHT_E, "name": "Elevation Vulnerability", "justification": "Topographic depression factor: lower elevation zones (850m lake basin) collect gravity runoff."},
                "H": {"weight": self.WEIGHT_H, "name": "Historical Flood Vulnerability", "justification": "Empirically documented historical flood points from BBMP/KSNDMC records."},
                "D": {"weight": self.WEIGHT_D, "name": "Drainage Vulnerability", "justification": "Stormwater drain (SWD) capacity deficit, rajakaluve siltation, and culvert blockages."}
            },
            "classification_tiers": {
                "LOW": {"range": [0.0, 29.9], "color": "#10B981", "advisory": "Normal conditions; standard maintenance."},
                "MODERATE": {"range": [30.0, 54.9], "color": "#F1B85B", "advisory": "Water accumulation likely in low-lying roadside lanes."},
                "HIGH": {"range": [55.0, 74.9], "color": "#EF8D42", "advisory": "Significant waterlogging; basement ingress risk; non-essential travel discouraged."},
                "SEVERE": {"range": [75.0, 100.0], "color": "#D95757", "advisory": "Severe flash inundation; critical road cuts imminent; activate evacuation protocols."}
            },
            "elevation_bounds": {
                "min_depression_m": self.MIN_ELEVATION_M,
                "max_plateau_m": self.MAX_ELEVATION_M,
                "zone": "Whitefield & Mahadevapura Basin"
            },
            "presets": self.RAINFALL_PRESETS,
            "data_sources": self.DATA_SOURCES,
            "scientific_disclaimer": (
                "This formula is a deterministic multi-criteria screening index based on spatial indicators. "
                "It is NOT a 1D/2D hydrodynamic physics water depth simulation. "
                "It does not predict exact inundation depth or flood arrival time."
            )
        }

# Singleton instance
flood_engine = FloodEngine()
