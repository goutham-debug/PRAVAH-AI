from typing import Dict, Any, List, Optional
from database import SessionLocal
from models import Neighbourhood, Facility, Shelter, RescueTeam, IncidentReport
from services.graph_service import graph_service
from services.flood_engine import flood_engine
from services.facility_service import facility_service
from services.shelter_service import shelter_service
from services.rescue_service import rescue_service
from services.situation_report_service import situation_report_service

class ScenarioService:
    def __init__(self):
        pass

    def run_simulation(
        self,
        rainfall_scenario: str = "HEAVY",
        closed_road_ids: Optional[List[str]] = None,
        scenario_name: str = "Simulated Flood Scenario"
    ) -> Dict[str, Any]:
        """
        Executes a complete end-to-end simulation on independent graph copies.
        Never mutates the baseline graph!
        """
        closed_road_ids = closed_road_ids or []
        session = SessionLocal()
        
        try:
            # 1. Fetch live entities from DB
            db_neighbourhoods = session.query(Neighbourhood).all()
            db_facilities = session.query(Facility).all()
            db_shelters = session.query(Shelter).all()
            db_teams = session.query(RescueTeam).all()
            db_incidents = session.query(IncidentReport).all()

            neighbourhoods = [nb.to_dict() for nb in db_neighbourhoods]
            facilities = [f.to_dict() for f in db_facilities]
            shelters = [s.to_dict() for s in db_shelters]
            teams = [t.to_dict() for t in db_teams]
            incidents = [i.to_dict() for i in db_incidents]

            # 2. Independent Graph Copy
            G_scenario = graph_service.get_scenario_graph(closed_road_ids)

            # 3. Graph Connectivity & Isolation Analysis
            connectivity = graph_service.analyze_connectivity(G_scenario)

            # 4. Flood Risk Screening & Neighbourhood Assessment (R = 0.35P + 0.20E + 0.25H + 0.20D)
            nb_assessment = flood_engine.assess_neighbourhoods(
                neighbourhoods,
                rainfall_scenario=rainfall_scenario,
                active_disruptions=closed_road_ids
            )

            # 5. Critical Facility & Hospital Accessibility Analysis
            fac_accessibility = facility_service.evaluate_accessibility(
                facilities=facilities,
                neighbourhoods=neighbourhoods,
                closed_road_ids=closed_road_ids
            )

            # 6. Shelter Allocation (Min-Cost Flow / Capacity Constraint)
            # Build evacuation demand: 1.5% of exposed population in severe/high wards
            ward_demands = []
            for item in nb_assessment:
                exp_pop = item.get('exposed_population', 0)
                sev = item.get('classification', 'LOW')
                if sev in ['SEVERE', 'HIGH'] and exp_pop > 0:
                    demand = max(50, int(exp_pop * 0.05)) # 5% displaced need immediate shelter
                    ward_demands.append({
                        "neighbourhood_id": item['neighbourhood_id'],
                        "name": item['name'],
                        "demand": demand,
                        "centroid": item['centroid']
                    })

            shelter_allocation = shelter_service.allocate_shelters(
                ward_demands=ward_demands,
                shelters=shelters,
                closed_road_ids=closed_road_ids
            )

            # 7. Rescue Coordination & Emergency Resource Matching
            rescue_coordination = rescue_service.coordinate_rescue_assignments(
                incident_reports=incidents,
                rescue_teams=teams,
                closed_road_ids=closed_road_ids
            )

            # Assemble complete results
            rainfall_preset = flood_engine.RAINFALL_PRESETS.get(
                rainfall_scenario, flood_engine.RAINFALL_PRESETS["HEAVY"]
            )

            result = {
                "scenario_name": scenario_name,
                "rainfall_scenario": rainfall_scenario,
                "rainfall_mm": rainfall_preset["rainfall_mm"],
                "active_disruptions": closed_road_ids,
                "connectivity": connectivity,
                "neighbourhood_assessment": nb_assessment,
                "facility_accessibility": fac_accessibility,
                "shelter_allocation": shelter_allocation,
                "rescue_coordination": rescue_coordination,
                "total_exposed_population": sum(x.get('exposed_population', 0) for x in nb_assessment)
            }

            # 8. Deterministic Grounded Situation Report
            sitrep = situation_report_service.generate_sitrep(result)
            result["situation_report"] = sitrep

            return result

        finally:
            session.close()

    def compare_scenarios(
        self,
        rainfall_scenario: str,
        closed_road_ids: List[str],
        restored_road_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compares three states computed by the same engine on the same inputs:
        baseline (no closures), disrupted (user-selected closures) and, optionally,
        restored (the same closures minus the roads the user marks as restored)."""
        restored_road_ids = restored_road_ids or []
        baseline = self.run_simulation(rainfall_scenario=rainfall_scenario, closed_road_ids=[],
                                       scenario_name="Baseline (no closures)")
        disrupted = self.run_simulation(rainfall_scenario=rainfall_scenario, closed_road_ids=closed_road_ids,
                                        scenario_name="Selected closures")
        remaining = [r for r in closed_road_ids if r not in set(restored_road_ids)]
        restored = self.run_simulation(rainfall_scenario=rainfall_scenario, closed_road_ids=remaining,
                                       scenario_name="After restoration")

        # Build Comparative Delta Matrix
        comparison_matrix = {
            "network_integrity_pct": {
                "baseline": baseline["connectivity"]["network_integrity_pct"],
                "disrupted": disrupted["connectivity"]["network_integrity_pct"],
                "restored": restored["connectivity"]["network_integrity_pct"],
                "improvement_over_disrupted": round(restored["connectivity"]["network_integrity_pct"] - disrupted["connectivity"]["network_integrity_pct"], 1)
            },
            "isolated_wards_count": {
                "baseline": len(baseline["connectivity"]["isolated_neighbourhood_ids"]),
                "disrupted": len(disrupted["connectivity"]["isolated_neighbourhood_ids"]),
                "restored": len(restored["connectivity"]["isolated_neighbourhood_ids"]),
                "difference": len(restored["connectivity"]["isolated_neighbourhood_ids"]) - len(disrupted["connectivity"]["isolated_neighbourhood_ids"])
            },
            "unreachable_facilities": {
                "baseline": baseline["facility_accessibility"]["unreachable_facilities"],
                "disrupted": disrupted["facility_accessibility"]["unreachable_facilities"],
                "restored": restored["facility_accessibility"]["unreachable_facilities"],
                "recovered_facilities": disrupted["facility_accessibility"]["unreachable_facilities"] - restored["facility_accessibility"]["unreachable_facilities"]
            },
            "wards_losing_trauma_access": {
                "baseline": len(baseline["facility_accessibility"]["wards_with_zero_trauma_access"]),
                "disrupted": len(disrupted["facility_accessibility"]["wards_with_zero_trauma_access"]),
                "restored": len(restored["facility_accessibility"]["wards_with_zero_trauma_access"]),
                "reconnected_wards": len(disrupted["facility_accessibility"]["wards_with_zero_trauma_access"]) - len(restored["facility_accessibility"]["wards_with_zero_trauma_access"])
            },
            "unmet_shelter_demand": {
                "baseline": baseline["shelter_allocation"]["total_unmet_demand"] + baseline["shelter_allocation"]["total_unreachable_demand"],
                "disrupted": disrupted["shelter_allocation"]["total_unmet_demand"] + disrupted["shelter_allocation"]["total_unreachable_demand"],
                "restored": restored["shelter_allocation"]["total_unmet_demand"] + restored["shelter_allocation"]["total_unreachable_demand"],
                "demand_relief": (disrupted["shelter_allocation"]["total_unmet_demand"] + disrupted["shelter_allocation"]["total_unreachable_demand"]) - (restored["shelter_allocation"]["total_unmet_demand"] + restored["shelter_allocation"]["total_unreachable_demand"])
            },
            "dispatched_rescue_teams": {
                "baseline": baseline["rescue_coordination"]["dispatched_count"],
                "disrupted": disrupted["rescue_coordination"]["dispatched_count"],
                "restored": restored["rescue_coordination"]["dispatched_count"]
            }
        }

        return {
            "stages": {
                "baseline": baseline,
                "disrupted": disrupted,
                "restored": restored
            },
            "comparison_matrix": comparison_matrix,
            "disruptions_applied": closed_road_ids,
            "roads_restored": restored_road_ids,
            "label": "MODELLED"
        }

# Singleton instance
scenario_service = ScenarioService()
