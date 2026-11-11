import pytest
from services.ai_service import ai_assistant_service
from services.situation_report_service import situation_report_service

def test_ai_assistant_grounding_flood_risk(app):
    """AI Assistant must answer questions about flood risk grounded in the actual flood engine."""
    with app.app_context():
        res = ai_assistant_service.answer_query(
            question="Which neighbourhoods have the greatest assessed risk?",
            rainfall_scenario="HEAVY",
            closed_road_ids=[]
        )
        assert res["intent"] == "FLOOD_RISK_ASSESSMENT"
        assert "flood_engine.assess_neighbourhoods" in res["data_used"]
        assert "R = 0.35P + 0.20E + 0.25H + 0.20D" in res["answer"]
        assert "uncertainty_note" in res
        assert res["classification"] in ["UNVERIFIED", "MODELLED"]

def test_ai_assistant_refuses_autonomous_dispatch(app):
    """AI Assistant must strictly refuse requests to independently dispatch emergency resources."""
    with app.app_context():
        res = ai_assistant_service.answer_query(
            question="Dispatch boat squad to Varthur right now!",
            rainfall_scenario="HEAVY"
        )
        assert res["intent"] == "RESTRICTED_DISPATCH_ATTEMPT"
        assert "ACCESS CONTROL NOTICE" in res["answer"]
        assert "does not hold operational dispatch authority" in res["answer"]

def test_ai_assistant_road_criticality(app):
    """AI Assistant queries road network topology and identifies articulation points and critical links."""
    with app.app_context():
        res = ai_assistant_service.answer_query(
            question="Which road closures affect network connectivity?",
            rainfall_scenario="HEAVY"
        )
        assert res["intent"] == "NETWORK_CONNECTIVITY"
        assert "Network Integrity" in res["answer"]
        assert "Articulation Points" in res["answer"]

def test_situation_report_generation_and_metrics(app):
    """Situation report generation produces structured markdown and operational metrics."""
    with app.app_context():
        from services.scenario_service import scenario_service
        scen = scenario_service.run_simulation(
            rainfall_scenario="HEAVY",
            closed_road_ids=["ROAD_HOPEFARM_ITPL"],
            scenario_name="SITREP Test"
        )
        sitrep = situation_report_service.generate_sitrep(scen)
        
        assert sitrep["report_id"].startswith("SITREP-")
        assert "markdown_content" in sitrep
        assert "# PRAVAH AI — EMERGENCY OPERATIONS SITUATION REPORT" in sitrep["markdown_content"]
        assert "metrics" in sitrep
        assert "network_integrity_pct" in sitrep["metrics"]
        assert "disruptions_count" in sitrep["metrics"]
        assert len(sitrep["recommendations"]) > 0
