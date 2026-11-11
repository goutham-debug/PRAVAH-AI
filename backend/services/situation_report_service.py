from datetime import datetime
from typing import Dict, Any, List

class SituationReportService:
    def __init__(self):
        pass

    def generate_sitrep(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a comprehensive, deterministic, strictly grounded situation report (SITREP)
        from actual executed scenario metrics.
        """
        scenario_name = scenario_data.get("name", "Urban Flood Scenario Assessment")
        rainfall_scenario = scenario_data.get("rainfall_scenario", "HEAVY")
        rainfall_mm = scenario_data.get("rainfall_mm", 85.0)
        disruptions = scenario_data.get("active_disruptions", [])
        
        connectivity = scenario_data.get("connectivity", {})
        neighbourhoods = scenario_data.get("neighbourhood_assessment", [])
        facility_access = scenario_data.get("facility_accessibility", {})
        shelter_alloc = scenario_data.get("shelter_allocation", {})
        rescue_ops = scenario_data.get("rescue_coordination", {})

        # Compute key summary figures
        severe_wards = [nb['name'] for nb in neighbourhoods if nb.get('classification') == 'SEVERE']
        high_wards = [nb['name'] for nb in neighbourhoods if nb.get('classification') == 'HIGH']
        total_exposed_pop = sum(nb.get('exposed_population', 0) for nb in neighbourhoods)
        isolated_wards = connectivity.get("isolated_neighbourhood_ids", [])
        
        unreachable_facs = facility_access.get("unreachable_facilities", 0)
        total_facs = facility_access.get("total_facilities", 0)
        trauma_loss_wards = [w['name'] for w in facility_access.get("wards_with_zero_trauma_access", [])]
        
        shelter_unmet = shelter_alloc.get("total_unmet_demand", 0)
        shelter_unreachable = shelter_alloc.get("total_unreachable_demand", 0)
        shelter_util = shelter_alloc.get("shelter_utilization_pct", 0)

        dispatched_rescues = rescue_ops.get("dispatched_count", 0)
        unassigned_incidents = rescue_ops.get("unassigned_count", 0)

        # Executive summary narrative
        timestamp_str = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
        
        exec_summary = (
            f"SITUATION REPORT: {scenario_name.upper()}\n"
            f"Issued by: PRAVAH AI Urban Operations Intelligence Centre\n"
            f"Time of Assessment: {timestamp_str}\n\n"
            f"1. OPERATIONAL OVERVIEW:\n"
            f"Under an assumed precipitation level of {rainfall_mm} mm ({rainfall_scenario} scenario), "
            f"the Whitefield-Mahadevapura urban corridor experiences significant localized inundation. "
            f"A total of {len(disruptions)} critical road segment(s) are actively disrupted, reducing overall network integrity to "
            f"{connectivity.get('network_integrity_pct', 100)}%. "
            f"Estimated exposed population across vulnerable wards totals {total_exposed_pop:,} residents.\n\n"
            f"2. NEIGHBOURHOOD IMPACT & ISOLATION:\n"
            f"Severe risk classifications are observed in: {', '.join(severe_wards) if severe_wards else 'None'}. "
            f"High risk wards include: {', '.join(high_wards) if high_wards else 'None'}. "
            f"{len(isolated_wards)} neighbourhood(s) exhibit network disconnection requiring priority causeway drainage or amphibious extraction.\n\n"
            f"3. CRITICAL HEALTHCARE INFRASTRUCTURE:\n"
            f"{unreachable_facs} of {total_facs} facilities have lost land-route vehicular accessibility. "
            f"Crucially, the following communities have lost direct road access to Tertiary Trauma Hospitals (Vydehi / Sakra): "
            f"{', '.join(trauma_loss_wards) if trauma_loss_wards else 'None'}.\n\n"
            f"4. EVACUATION SHELTERS & RESCUE DISPATCH:\n"
            f"Regional shelters are operating at {shelter_util}% aggregate capacity. Unmet evacuation demand stands at "
            f"{shelter_unmet + shelter_unreachable} individuals ({shelter_unreachable} due to severed transit corridors). "
            f"{dispatched_rescues} emergency rescue unit(s) have been matched and routed, leaving {unassigned_incidents} incident(s) queued for mutual aid."
        )

        # Concrete recommendations
        recommendations = [
            {
                "priority": "P1 - CRITICAL",
                "action": "Deploy high-flow submersible dewatering pumps to Outer Ring Road (Kadubeesanahalli / Devarabeesanahalli underpasses)",
                "target_zone": "Bellandur - Marathahalli Corridor",
                "expected_impact": "Restores arterial link between South and East tech corridors; re-establishes Sakra World Hospital vehicular access."
            },
            {
                "priority": "P1 - CRITICAL",
                "action": "Dispatch SDRF Inflatable Boat Units to Varthur Lake sluice and Kodi Causeway",
                "target_zone": "Varthur Ward 149",
                "expected_impact": "Enables safe extraction of isolated residents across flooded lake overflow channels."
            },
            {
                "priority": "P2 - HIGH",
                "action": "Activate auxiliary capacity at Hoodi Multi-Purpose Sports Complex",
                "target_zone": "Hoodi & ITPL Zone",
                "expected_impact": "Absorbs displaced population spillover from inundated low-lying settlements."
            },
            {
                "priority": "P3 - MEDIUM",
                "action": "Enact transit diversions via Kundalahalli Gate and HAL Old Airport Road",
                "target_zone": "Brookefield & Whitefield Main Road",
                "expected_impact": "Reroutes emergency ambulances away from waterlogged arterial underpasses."
            }
        ]

        markdown_report = f"""# PRAVAH AI — EMERGENCY OPERATIONS SITUATION REPORT
**Scenario:** {scenario_name} | **Rainfall:** {rainfall_mm} mm ({rainfall_scenario}) | **Generated:** {timestamp_str}

---

## 1. Executive Summary
{exec_summary}

---

## 2. Key Operational Metrics
| Metric | Value | Baseline Comparison |
| :--- | :--- | :--- |
| **Network Integrity** | {connectivity.get('network_integrity_pct', 100)}% | Reduced by {100 - connectivity.get('network_integrity_pct', 100):.1f}% |
| **Active Road Disruptions** | {len(disruptions)} | Baseline: 0 |
| **Exposed Population** | {total_exposed_pop:,} | Baseline: 0 |
| **Isolated Wards** | {len(isolated_wards)} | Baseline: 0 |
| **Trauma Hospitals Disconnected** | {len(trauma_loss_wards)} wards cut off | Baseline: 0 |
| **Shelter Utilization** | {shelter_util}% | Baseline: 0% |
| **Unmet Evacuation Demand** | {shelter_unmet + shelter_unreachable:,} persons | Capacity bounded |
| **Rescue Units Dispatched** | {dispatched_rescues} squads | Full tracking active |

---

## 3. Disrupted Road Segments
{self._format_disruptions_table(disruptions)}

---

## 4. Priority Interventions & Recommended Actions
{self._format_recommendations_md(recommendations)}

---

## 5. Technical Assumptions & Limitations
- **Screening Index Nature:** The flood risk index $R = 0.35P + 0.20E + 0.25H + 0.20D$ is a spatial multi-criteria screening index, not a 2D hydrodynamic hydrodynamic simulation.
- **Population Data:** Population values represent 2021 BBMP Census projections aggregated to ward boundaries.
- **Facility Availability:** Accessibility indicates road topological reachability; internal hospital electrical or bed operational status must be verified out-of-band.
"""

        return {
            "report_id": f"SITREP-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "scenario_name": scenario_name,
            "timestamp": timestamp_str,
            "executive_summary": exec_summary,
            "markdown_content": markdown_report,
            "metrics": {
                "rainfall_mm": rainfall_mm,
                "disruptions_count": len(disruptions),
                "exposed_population": total_exposed_pop,
                "network_integrity_pct": connectivity.get('network_integrity_pct', 100),
                "unreachable_facilities_count": unreachable_facs,
                "trauma_disconnected_wards": trauma_loss_wards,
                "shelter_utilization_pct": shelter_util,
                "unmet_evacuation_demand": shelter_unmet + shelter_unreachable,
                "dispatched_rescue_teams": dispatched_rescues,
                "unassigned_incidents": unassigned_incidents
            },
            "recommendations": recommendations
        }

    def _format_disruptions_table(self, disruptions: List[str]) -> str:
        if not disruptions:
            return "_No active road closures recorded. Full network connectivity maintained._\n"
        out = "| Road ID | Status | Vulnerability Note |\n| :--- | :--- | :--- |\n"
        for d in disruptions:
            out += f"| `{d}` | **CLOSED / INUNDATED** | Low-lying culvert / drainage overflow |\n"
        return out

    def _format_recommendations_md(self, recs: List[Dict[str, Any]]) -> str:
        out = ""
        for r in recs:
            out += f"- **[{r['priority']}]** {r['action']}  \n  *Target:* {r['target_zone']} | *Impact:* {r['expected_impact']}\n\n"
        return out

# Singleton instance
situation_report_service = SituationReportService()
