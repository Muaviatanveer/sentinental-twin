from fastapi.testclient import TestClient
import pytest
from apps.api.app.main import app
from apps.api.app.schemas.contracts import PolicyRequirement
from engine.compose_parser.parser import ComposeParser
from engine.twin_builder.builder import TwinBuilder
from engine.graph_engine.analyzer import GraphAnalyzer
from engine.policy_engine.synthesizer import PolicySynthesizer

client = TestClient(app)


# LEVEL 1: Parser Tests
def test_level1_parser_valid_and_warnings():
    raw_yaml = """
services:
  web:
    image: busybox:1.36
    build: .
    privileged: true
    ports:
      - "8080:80"
"""
    parsed = ComposeParser.parse(raw_yaml)
    assert "web" in parsed["services"]
    assert len(parsed["warnings"]) == 2
    assert len(parsed["hash"]) == 64


def test_level1_parser_rejects_invalid_yaml():
    with pytest.raises(ValueError):
        ComposeParser.parse("not_a_compose_dict: [unclosed")


# LEVEL 2: Graph Engine Tests
def test_level2_graph_distinguishes_depends_on_from_network_reachability():
    raw_yaml = """
services:
  frontend:
    image: busybox
    depends_on:
      - db
    networks:
      - net_a
  db:
    image: busybox
    networks:
      - net_b
networks:
  net_a: {}
  net_b: {}
"""
    parsed = ComposeParser.parse(raw_yaml)
    topo = GraphAnalyzer.analyze_reachability(
        TwinBuilder.build_topology("proj_unit", parsed)
    )
    # Even though frontend depends_on db, they do NOT share a network
    assert topo.reachability_matrix["frontend"]["db"] == "blocked"


# LEVEL 3: Policy & Counterfactual Synthesizer Tests
def test_level3_policy_rejects_unknown_service_and_conflicts():
    raw_yaml = """
services:
  frontend:
    image: busybox
  database:
    image: busybox
"""
    topo = GraphAnalyzer.analyze_reachability(
        TwinBuilder.build_topology("proj_p", ComposeParser.parse(raw_yaml))
    )
    # Unknown service
    errs = PolicySynthesizer.validate_requirements(
        [PolicyRequirement(source="frontend", destination="redis", expected="deny")],
        topo,
    )
    assert any("Unknown destination service 'redis'" in e for e in errs)

    # Conflicting rules on same pair
    conflict_errs = PolicySynthesizer.validate_requirements(
        [
            PolicyRequirement(source="frontend", destination="database", expected="allow"),
            PolicyRequirement(source="frontend", destination="database", expected="deny"),
        ],
        topo,
    )
    assert any("Conflicting requirements" in e for e in conflict_errs)


# LEVEL 4: End-to-End API Workflow
def test_level4_e2e_sample_proposal_and_simulation():
    res_proj = client.post("/api/v1/projects/sample")
    assert res_proj.status_code == 201
    pid = res_proj.json()["id"]

    res_prop = client.post(
        f"/api/v1/projects/{pid}/proposals",
        json={
            "intent": "Allow frontend to talk to api, prevent frontend from accessing database directly, keep api to database working."
        },
    )
    assert res_prop.status_code == 201
    prop_id = res_prop.json()["id"]

    res_sim = client.post(
        f"/api/v1/projects/{pid}/simulations",
        json={"proposal_id": prop_id},
    )
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert (
        sim_data["candidate_reachability"]["frontend_to_database"]
        == "blocked_by_candidate_policy"
    )
