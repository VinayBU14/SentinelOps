import pytest
from app.services.risk_engine import (
    calculate_asset_risk,
    determine_risk_level,
    VULNERABILITY_SEVERITY_SCORES,
    ASSET_CRITICALITY_SCORES,
)

def test_vulnerability_severity_mappings():
    assert VULNERABILITY_SEVERITY_SCORES["critical"] == 100.0
    assert VULNERABILITY_SEVERITY_SCORES["high"] == 75.0
    assert VULNERABILITY_SEVERITY_SCORES["medium"] == 50.0
    assert VULNERABILITY_SEVERITY_SCORES["low"] == 25.0
    assert VULNERABILITY_SEVERITY_SCORES["informational"] == 0.0
    assert VULNERABILITY_SEVERITY_SCORES["none"] == 0.0

def test_criticality_mappings():
    assert ASSET_CRITICALITY_SCORES["critical"] == 100.0
    assert ASSET_CRITICALITY_SCORES["high"] == 75.0
    assert ASSET_CRITICALITY_SCORES["medium"] == 50.0
    assert ASSET_CRITICALITY_SCORES["low"] == 25.0

def test_spec_worked_example():
    """
    Section 6.4 Worked example:
    Vulnerability severity = High (75)
    Criticality = Critical (100)
    Owner missing = 100
    Risk = (0.50 * 75) + (0.30 * 100) + (0.20 * 100)
         = 37.5 + 30 + 20 = 87.5
    Level = Critical
    """
    res = calculate_asset_risk(
        vulnerability_severity="High",
        criticality="Critical",
        owner_name=""
    )
    assert res.vulnerability_score == 75.0
    assert res.criticality_score == 100.0
    assert res.ownership_score == 100.0
    assert res.risk_score == 87.5
    assert res.risk_level == "Critical"
    assert "87.5/100" in res.explanation
    assert "no assigned owner" in res.explanation

def test_owner_present_no_penalty():
    res = calculate_asset_risk(
        vulnerability_severity="High",
        criticality="Critical",
        owner_name="Jane Doe"
    )
    assert res.ownership_score == 0.0
    # 37.5 + 30 + 0 = 67.5 -> High
    assert res.risk_score == 67.5
    assert res.risk_level == "High"
    assert "Jane Doe" in res.explanation

def test_boundary_conditions():
    # Low: 0 - 29.99
    assert determine_risk_level(0.0) == "Low"
    assert determine_risk_level(29.99) == "Low"

    # Medium: 30 - 59.99
    assert determine_risk_level(30.0) == "Medium"
    assert determine_risk_level(59.99) == "Medium"

    # High: 60 - 79.99
    assert determine_risk_level(60.0) == "High"
    assert determine_risk_level(79.99) == "High"

    # Critical: 80 - 100
    assert determine_risk_level(80.0) == "Critical"
    assert determine_risk_level(100.0) == "Critical"

def test_min_and_max_possible_scores():
    # Minimum: None (0) + Low (25) + Owner (0) = 0 + 7.5 + 0 = 7.5
    min_res = calculate_asset_risk("None", "Low", "Admin")
    assert min_res.risk_score == 7.5
    assert min_res.risk_level == "Low"

    # Maximum: Critical (100) + Critical (100) + No Owner (100) = 50 + 30 + 20 = 100.0
    max_res = calculate_asset_risk("Critical", "Critical", "")
    assert max_res.risk_score == 100.0
    assert max_res.risk_level == "Critical"

def test_informational_severity():
    # Informational (0) + Medium (50) + Owner (0) = 0 + 15 + 0 = 15.0 (Low)
    res = calculate_asset_risk("Informational", "Medium", "Custodian")
    assert res.vulnerability_score == 0.0
    assert res.risk_score == 15.0
    assert res.risk_level == "Low"

