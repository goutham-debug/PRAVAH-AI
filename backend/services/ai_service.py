"""
AI Assistant service for PRAVAH AI.
Answers queries grounded STRICTLY in actual backend assessment results.
Never invents data, statistics, facilities, or incidents.
If credentials for external LLM are not provided, operates in deterministic grounded-synthesis mode.
"""
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from database import SessionLocal
from models import Neighbourhood, Facility, Shelter, RescueTeam, IncidentReport
from services.flood_engine import flood_engine
from services.graph_service import graph_service
from services.facility_service import facility_service
from services.shelter_service import shelter_service
from services.scenario_service import scenario_service
from services.event_logger import event_logger


class AIAssistantService:
    def __init__(self):
        pass

    def answer_query(
        self,
        question: str,
        assessment_id: Optional[str] = None,
        rainfall_scenario: str = "HEAVY",
        closed_road_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Grounded AI response generation.
        1. Identifies operational intent from the question.
        2. Retrieves actual metrics from authoritative backend engines.
        3. Formulates a deterministic, verified answer.
        4. Explicitly adds metadata, data classification, and uncertainty disclaimers.
        """
        closed_road_ids = closed_road_ids or []
        start_time = datetime.now(timezone.utc)
        q_lower = question.lower().strip()

        # Check for emergency dispatch / operational command attempt
        if any(term in q_lower for term in ["dispatch", "order team", "close road now", "evacuate ward now"]):
            return {
                "answer": (
                    "DISCLAIMER & ACCESS CONTROL NOTICE: PRAVAH AI Assistant is an informational intelligence tool "
                    "and does not hold operational dispatch authority. Field dispatches, road closure orders, and "
                    "mandatory evacuation notices must be formally authorized by designated Incident Commanders "
                    "or BBMP/SDRF Disaster Officers via the Command Centre."
                ),
                "data_used": [],
                "intent": "RESTRICTED_DISPATCH_ATTEMPT",
                "classification": "OFFICIAL_RESTRICTION",
                "assessment_id": assessment_id or "ASSESS-REALTIME",
                "timestamp": start_time.isoformat(),
                "uncertainty_note": "Automated resource command execution is disabled by policy."
            }

        data_used = []
        intent = "GENERAL"
        answer_parts = []

        session = SessionLocal()
        try:
            # Intent 1: Risk Assessment / Highest Risk Neighbourhoods
            if any(term in q_lower for term in ["risk", "neighbourhood", "ward", "highest", "vulnerable", "inundat"]):
                intent = "FLOOD_RISK_ASSESSMENT"
                db_nbs = session.query(Neighbourhood).all()
                nbs = [n.to_dict() for n in db_nbs]
                
                assessments = flood_engine.assess_neighbourhoods(
                    nbs,
                    rainfall_scenario=rainfall_scenario,
                    active_disruptions=closed_road_ids
                )
                data_used.append("flood_engine.assess_neighbourhoods")
                
                # Sort by risk score
                assessed_only = [a for a in assessments if a.get('risk_score') is not None]
                unassessed = [a for a in assessments if a.get('risk_score') is None]
                assessed_only.sort(key=lambda x: x.get('risk_score', 0), reverse=True)

                answer_parts.append(f"### Assessed Flood Susceptibility ({rainfall_scenario} Rainfall Scenario)\n")
                if assessed_only:
                    answer_parts.append("**Wards Ranked by Assessed Susceptibility Score (R = 0.35P + 0.20E + 0.25H + 0.20D):**\n")
                    for idx, w in enumerate(assessed_only[:5], 1):
                        factors = w.get('components', {})
                        p_val = factors.get('P_rainfall', {}).get('normalized_value', 'N/A')
                        e_val = factors.get('E_elevation', {}).get('normalized_value', 'N/A')
                        h_val = factors.get('H_history', {}).get('normalized_value', 'N/A')
                        d_val = factors.get('D_drainage', {}).get('normalized_value', 'N/A')
                        answer_parts.append(
                            f"{idx}. **{w['name']}** — Risk Score: **{w['risk_score']} / 100** ({w['classification']})\n"
                            f"   - Factor breakdown: P={p_val}, E={e_val}, H={h_val}, D={d_val}\n"
                            f"   - Primary Risk Driver: *{w.get('primary_driver', 'Composite')}*\n"
                        )
                if unassessed:
                    unassessed_names = [u['name'] for u in unassessed]
                    answer_parts.append(f"\n*Note: {len(unassessed)} ward(s) marked `NOT_ASSESSED` due to missing elevation/drainage inputs: {', '.join(unassessed_names)}.*\n")

            # Intent 2: Road Closures, Critical Links & Network Connectivity
            elif any(term in q_lower for term in ["road", "closure", "connectivity", "critical", "bridge", "isolated", "cut off"]):
                intent = "NETWORK_CONNECTIVITY"
                crit_links = graph_service.identify_critical_road_links()
                conn = graph_service.analyze_connectivity()
                data_used.extend(["graph_service.identify_critical_road_links", "graph_service.analyze_connectivity"])

                answer_parts.append("### Road Network Topology & Vulnerability Audit\n")
                answer_parts.append(f"- **Overall Network Integrity:** {conn.get('network_integrity_pct', 'N/A')}%\n")
                answer_parts.append(f"- **Topological Articulation Points:** {len(conn.get('articulation_points', []))} critical junctions\n")
                answer_parts.append(f"- **Bridge Segments:** {len(conn.get('bridges', []))} cut-edges whose loss fragments the corridor\n\n")

                if crit_links:
                    answer_parts.append("**Top Critical Road Links (by Betweenness & Inundation Risk):**\n")
                    for idx, link in enumerate(crit_links[:4], 1):
                        is_br = " (TOPOLOGICAL BRIDGE)" if link.get('is_bridge') else ""
                        answer_parts.append(
                            f"{idx}. **{link.get('name')}**{is_br}\n"
                            f"   - Length: {link.get('length_km')} km | Flood Vulnerability: {link.get('flood_risk')}\n"
                            f"   - Structural Impact: {link.get('why_critical')}\n"
                        )
                if closed_road_ids:
                    answer_parts.append(f"\n**Currently Active Disruptions:** {len(closed_road_ids)} segments flagged closed.\n")

            # Intent 3: Healthcare & Hospital Accessibility
            elif any(term in q_lower for term in ["hospital", "facility", "health", "trauma", "medical", "doctor"]):
                intent = "HOSPITAL_ACCESSIBILITY"
                db_facs = session.query(Facility).all()
                db_nbs = session.query(Neighbourhood).all()
                fac_res = facility_service.evaluate_accessibility(
                    facilities=[f.to_dict() for f in db_facs],
                    neighbourhoods=[n.to_dict() for n in db_nbs],
                    closed_road_ids=closed_road_ids
                )
                data_used.append("facility_service.evaluate_accessibility")

                answer_parts.append("### Healthcare Facility & Trauma Access Assessment\n")
                answer_parts.append(f"- **Overall Healthcare Accessibility:** {fac_res.get('overall_accessibility_pct', 'N/A')}%\n")
                answer_parts.append(f"- **Unreachable Facilities:** {fac_res.get('unreachable_facilities', 0)} of {fac_res.get('total_facilities', 0)}\n")

                zero_trauma = fac_res.get('wards_with_zero_trauma_access', [])
                if zero_trauma:
                    zt_names = [w.get('name', 'Unknown') for w in zero_trauma]
                    answer_parts.append(f"- **CRITICAL ALERT:** The following communities currently have **ZERO** road access to Tertiary Trauma Centres: **{', '.join(zt_names)}**\n")
                else:
                    answer_parts.append("- Direct road access to Tertiary Trauma facilities (Vydehi / Sakra) is currently preserved for all assessed wards.\n")

                deps = fac_res.get('critical_facility_dependency_roads', [])
                if deps:
                    answer_parts.append("\n**Key Road Segments Sustaining Hospital Transit Corridors:**\n")
                    for d in deps[:3]:
                        answer_parts.append(f"- **{d['name']}**: Supports {d['hospital_routes_supported']} hospital transit routes.\n")

            # Intent 4: Shelters and Evacuation Capacity
            elif any(term in q_lower for term in ["shelter", "evacuat", "capacity", "displace", "relief"]):
                intent = "SHELTER_CAPACITY"
                db_shelters = session.query(Shelter).all()
                db_nbs = session.query(Neighbourhood).all()
                
                # Compute allocation
                demands = []
                for nb in db_nbs:
                    if nb.hazard_factor >= 50.0:
                        demands.append({
                            "neighbourhood_id": nb.id,
                            "name": nb.name,
                            "demand": int(nb.population * 0.04),
                            "centroid": [nb.centroid_lon, nb.centroid_lat]
                        })

                sh_res = shelter_service.allocate_shelters(
                    ward_demands=demands,
                    shelters=[s.to_dict() for s in db_shelters],
                    closed_road_ids=closed_road_ids
                )
                data_used.append("shelter_service.allocate_shelters")

                answer_parts.append("### Relief Shelter Capacity & Evacuation Allocation\n")
                answer_parts.append(f"- **Total Evacuation Demand:** {sh_res.get('total_evacuation_demand', 0):,} individuals\n")
                answer_parts.append(f"- **Successfully Allocated:** {sh_res.get('total_allocated_population', 0):,} ({sh_res.get('allocation_fulfillment_pct', 0)}%)\n")
                answer_parts.append(f"- **Total System Capacity:** {sh_res.get('total_shelter_capacity', 0):,} | Remaining: {sh_res.get('remaining_shelter_capacity', 0):,}\n")
                answer_parts.append(f"- **Aggregate Utilization:** {sh_res.get('shelter_utilization_pct', 0)}%\n\n")

                unmet = sh_res.get('unmet_records', [])
                if unmet:
                    answer_parts.append("**Unmet Evacuation Demand Notice:**\n")
                    for u in unmet:
                        answer_parts.append(f"- **{u['name']}:** {u['unmet_count']} persons unmet ({u['reason']})\n")

            # Intent 5: Scenario Comparison & Restoration Delta
            elif any(term in q_lower for term in ["scenario", "baseline", "compare", "restor", "interven", "delta", "difference"]):
                intent = "SCENARIO_COMPARISON"
                cmp_res = scenario_service.compare_scenarios(
                    rainfall_scenario=rainfall_scenario,
                    closed_road_ids=closed_road_ids,
                    restored_road_ids=[]
                )
                data_used.append("scenario_service.compare_scenarios")
                matrix = cmp_res.get('comparison_matrix', {})

                answer_parts.append("### Scenario Comparison (Baseline vs Disrupted)\n")
                answer_parts.append(f"- **Network Integrity:** Baseline={matrix.get('network_integrity_pct', {}).get('baseline')}% vs Disrupted={matrix.get('network_integrity_pct', {}).get('disrupted')}%\n")
                answer_parts.append(f"- **Isolated Wards:** Baseline={matrix.get('isolated_wards_count', {}).get('baseline')} vs Disrupted={matrix.get('isolated_wards_count', {}).get('disrupted')}\n")
                answer_parts.append(f"- **Unreachable Healthcare Facilities:** Baseline={matrix.get('unreachable_facilities', {}).get('baseline')} vs Disrupted={matrix.get('unreachable_facilities', {}).get('disrupted')}\n")
                answer_parts.append(f"- **Unmet Shelter Demand:** Baseline={matrix.get('unmet_shelter_demand', {}).get('baseline')} vs Disrupted={matrix.get('unmet_shelter_demand', {}).get('disrupted')}\n")

            # Fallback: General Situation Summary
            else:
                intent = "OPERATIONAL_SUMMARY"
                db_nbs = session.query(Neighbourhood).all()
                db_facs = session.query(Facility).all()
                db_shelters = session.query(Shelter).all()
                db_teams = session.query(RescueTeam).all()

                answer_parts.append("### PRAVAH AI Urban Operations Intelligence Overview\n")
                answer_parts.append(f"Operating in **{rainfall_scenario}** rainfall scenario across Whitefield-Mahadevapura.\n\n")
                answer_parts.append(f"- **Tracked Neighbourhood Wards:** {len(db_nbs)}\n")
                answer_parts.append(f"- **Registered Critical Facilities:** {len(db_facs)}\n")
                answer_parts.append(f"- **Designated Evacuation Shelters:** {len(db_shelters)}\n")
                answer_parts.append(f"- **Emergency Response Units:** {len(db_teams)}\n")
                answer_parts.append(f"- **Active Disruptions Applied:** {len(closed_road_ids)}\n\n")
                answer_parts.append("You can ask specific questions regarding:\n")
                answer_parts.append("1. *Highest risk neighbourhoods and factor contributions*\n")
                answer_parts.append("2. *Critical road links and articulation points*\n")
                answer_parts.append("3. *Hospital accessibility and trauma cut-offs*\n")
                answer_parts.append("4. *Shelter capacity and evacuation allocation*\n")
                answer_parts.append("5. *Scenario delta between baseline and closures*\n")

        finally:
            session.close()

        # Log backend event
        elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0
        event_logger.log(
            event_name="ai_query_processed",
            status="success",
            assessment_id=assessment_id or "ASSESS-REALTIME",
            duration_ms=elapsed_ms,
            details={"intent": intent, "data_used": data_used, "question_len": len(question)}
        )

        return {
            "answer": "".join(answer_parts),
            "data_used": data_used,
            "intent": intent,
            "classification": "MODELLED" if closed_road_ids else "UNVERIFIED",
            "assessment_id": assessment_id or "ASSESS-REALTIME",
            "timestamp": start_time.isoformat(),
            "uncertainty_note": (
                "Data Grounding Notice: All figures are extracted directly from active PRAVAH AI "
                "algorithmic assessments. The flood susceptibility index is an explainable multi-criteria "
                "screening index (R = 0.35P + 0.20E + 0.25H + 0.20D), not a 2D hydrodynamic simulation."
            )
        }


# Singleton
ai_assistant_service = AIAssistantService()
