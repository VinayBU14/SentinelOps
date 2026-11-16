from typing import Dict, Any, Tuple
from app.services.normalization import clean_str

VULNERABILITY_SEVERITY_SCORES: Dict[str, float] = {
    "critical": 100.0,
    "high": 75.0,
    "medium": 50.0,
    "low": 25.0,
    "informational": 0.0,
    "none": 0.0,
}

ASSET_CRITICALITY_SCORES: Dict[str, float] = {
    "critical": 100.0,
    "high": 75.0,
    "medium": 50.0,
    "low": 25.0,
}

VULNERABILITY_WEIGHT: float = 0.50
CRITICALITY_WEIGHT: float = 0.30
OWNERSHIP_WEIGHT: float = 0.20

class RiskScoreResult:
    def __init__(
        self,
        vulnerability_score: float,
        criticality_score: float,
        ownership_score: float,
        vulnerability_weight: float,
        criticality_weight: float,
        ownership_weight: float,
        risk_score: float,
        risk_level: str,
        explanation: str,
        vulnerability_label: str,
        criticality_label: str,
        owner_present: bool,
    ):
        self.vulnerability_score = vulnerability_score
        self.criticality_score = criticality_score
        self.ownership_score = ownership_score
        self.vulnerability_weight = vulnerability_weight
        self.criticality_weight = criticality_weight
        self.ownership_weight = ownership_weight
        self.risk_score = risk_score
        self.risk_level = risk_level
        self.explanation = explanation
        self.vulnerability_label = vulnerability_label
        self.criticality_label = criticality_label
        self.owner_present = owner_present

def determine_risk_level(unrounded_score: float) -> str:
    """
    Determine risk category from unrounded score per specification Section 6.3:
    0 - 29.99: Low
    30 - 59.99: Medium
    60 - 79.99: High
    80 - 100: Critical
    """
    if unrounded_score >= 80.0:
        return "Critical"
    elif unrounded_score >= 60.0:
        return "High"
    elif unrounded_score >= 30.0:
        return "Medium"
    else:
        return "Low"

def calculate_asset_risk(
    vulnerability_severity: str | None,
    criticality: str | None,
    owner_name: str | None
) -> RiskScoreResult:
    """
    Calculate deterministic explainable risk score for an eligible asset.
    Formula:
        Risk Score = (0.50 * VulnScore) + (0.30 * CritScore) + (0.20 * OwnerScore)
    Uses unrounded full precision for categorization and rounds to 2 decimal places for storage/display.
    """
    raw_vuln = clean_str(vulnerability_severity).lower()
    raw_crit = clean_str(criticality).lower()
    raw_owner = clean_str(owner_name)

    # 1. Vulnerability score
    vuln_score = VULNERABILITY_SEVERITY_SCORES.get(raw_vuln, 0.0)
    vuln_label = clean_str(vulnerability_severity).title() or "None"

    # 2. Criticality score
    crit_score = ASSET_CRITICALITY_SCORES.get(raw_crit, 25.0)
    crit_label = clean_str(criticality).title() or "Low"

    # 3. Ownership score
    owner_present = bool(raw_owner)
    ownership_score = 0.0 if owner_present else 100.0

    # 4. Calculate unrounded risk score
    unrounded_score = (
        (VULNERABILITY_WEIGHT * vuln_score) +
        (CRITICALITY_WEIGHT * crit_score) +
        (OWNERSHIP_WEIGHT * ownership_score)
    )

    # Clamp between 0.0 and 100.0
    unrounded_score = max(0.0, min(100.0, unrounded_score))

    # Determine risk level using unrounded score
    risk_level = determine_risk_level(unrounded_score)

    # Round for display/storage
    rounded_score = round(unrounded_score, 2)

    # 5. Deterministic explanation generation (no LLM)
    owner_desc = (
        f"an assigned owner ({raw_owner}, 0/100 ownership-risk input)"
        if owner_present
        else "no assigned owner (100/100 ownership-risk input)"
    )

    explanation = (
        f"{risk_level} risk ({rounded_score:g}/100). "
        f"The asset has a {vuln_label} vulnerability-severity input ({vuln_score:g}/100), "
        f"{crit_label} business criticality ({crit_score:g}/100), and {owner_desc}."
    )

    return RiskScoreResult(
        vulnerability_score=vuln_score,
        criticality_score=crit_score,
        ownership_score=ownership_score,
        vulnerability_weight=VULNERABILITY_WEIGHT,
        criticality_weight=CRITICALITY_WEIGHT,
        ownership_weight=OWNERSHIP_WEIGHT,
        risk_score=rounded_score,
        risk_level=risk_level,
        explanation=explanation,
        vulnerability_label=vuln_label,
        criticality_label=crit_label,
        owner_present=owner_present,
    )

