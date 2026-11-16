from collections import Counter
from typing import Dict, List, Any, Tuple
from app.services.normalization import (
    clean_str,
    normalize_ip,
    is_valid_email,
    is_valid_iso_date,
    parse_non_negative_int,
)

# Canonical allowed values (stored normalized in uppercase/titlecase sets for lookup)
ALLOWED_ASSET_TYPES = {
    "server", "workstation", "network device", "database",
    "application", "cloud asset", "security appliance", "storage", "iot device"
}

ALLOWED_CRITICALITIES = {"critical", "high", "medium", "low"}

ALLOWED_SEVERITIES = {"critical", "high", "medium", "low", "informational", "none"}

ALLOWED_ENVIRONMENTS = {"production", "staging", "development", "testing"}

ALLOWED_BOOLEANS = {"yes", "no"}

ALLOWED_DATA_CLASSIFICATIONS = {"public", "internal", "confidential", "restricted"}

ALLOWED_LIFECYCLES = {"active", "maintenance", "retiring"}

class ValidationIssueDTO:
    def __init__(
        self,
        row_number: int,
        asset_id: str | None,
        issue_code: str,
        severity: str,
        blocking: bool,
        field_name: str,
        observed_value: str | None,
        message: str,
        suggested_action: str,
    ):
        self.row_number = row_number
        self.asset_id = asset_id
        self.issue_code = issue_code
        self.severity = severity
        self.blocking = blocking
        self.field_name = field_name
        self.observed_value = str(observed_value)[:250] if observed_value is not None else None
        self.message = message
        self.suggested_action = suggested_action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_number": self.row_number,
            "asset_id": self.asset_id,
            "issue_code": self.issue_code,
            "severity": self.severity,
            "blocking": self.blocking,
            "field_name": self.field_name,
            "observed_value": self.observed_value,
            "message": self.message,
            "suggested_action": self.suggested_action,
        }

class ValidationResult:
    def __init__(self):
        self.parsed_rows: List[Dict[str, Any]] = []
        self.row_issues: Dict[int, List[ValidationIssueDTO]] = {}
        self.row_statuses: Dict[int, str] = {}  # row_number -> 'valid' | 'warning' | 'blocked'
        self.all_issues: List[ValidationIssueDTO] = []
        self.total_rows: int = 0
        self.valid_rows: int = 0
        self.warning_rows: int = 0
        self.blocked_rows: int = 0
        self.error_count: int = 0
        self.warning_count: int = 0
        self.blank_rows: int = 0

def validate_dataset(rows: List[Dict[str, Any]], blank_rows_count: int = 0) -> ValidationResult:
    """
    Validate dataset records deterministically following SentinelOps specification Section 5.
    rows: list of raw row dictionaries with 'source_row_number' and 24 columns.
    """
    result = ValidationResult()
    result.blank_rows = blank_rows_count
    result.total_rows = len(rows)

    if not rows:
        return result

    # Pass 1: Collect identifiers for duplicate detection across this batch
    asset_id_counts = Counter()
    canonical_ip_counts = Counter()
    canonical_ips: Dict[int, str | None] = {}

    for row in rows:
        row_num = row.get("source_row_number", 0)
        raw_asset_id = clean_str(row.get("asset_id"))
        if raw_asset_id:
            asset_id_counts[raw_asset_id.lower()] += 1

        raw_ip = clean_str(row.get("ip_address"))
        if raw_ip:
            canon_ip, is_valid = normalize_ip(raw_ip)
            if is_valid and canon_ip:
                canonical_ips[row_num] = canon_ip
                canonical_ip_counts[canon_ip] += 1
            else:
                canonical_ips[row_num] = None
        else:
            canonical_ips[row_num] = None

    # Pass 2: Field-level validation on each row
    for row in rows:
        row_num = row.get("source_row_number", 0)
        issues: List[ValidationIssueDTO] = []
        raw_asset_id = clean_str(row.get("asset_id"))
        display_asset_id = raw_asset_id if raw_asset_id else None

        # 1. Asset ID
        if not raw_asset_id:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=None,
                issue_code="MISSING_ASSET_ID",
                severity="error",
                blocking=True,
                field_name="asset_id",
                observed_value="",
                message="Asset ID is required but was empty or missing.",
                suggested_action="Assign a unique asset identifier to this record."
            ))
        elif asset_id_counts[raw_asset_id.lower()] > 1:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="DUPLICATE_ASSET_ID",
                severity="error",
                blocking=True,
                field_name="asset_id",
                observed_value=raw_asset_id,
                message=f"Duplicate asset ID '{raw_asset_id}' occurs {asset_id_counts[raw_asset_id.lower()]} times in this batch.",
                suggested_action="Deduplicate or provide distinct asset IDs for each record."
            ))

        # 2. Hostname
        raw_hostname = clean_str(row.get("hostname"))
        if not raw_hostname:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="MISSING_HOSTNAME",
                severity="error",
                blocking=True,
                field_name="hostname",
                observed_value="",
                message="Hostname is required but was empty.",
                suggested_action="Provide a valid hostname for the asset."
            ))

        # 3. IP Address
        raw_ip = clean_str(row.get("ip_address"))
        if not raw_ip:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="MISSING_IP",
                severity="error",
                blocking=True,
                field_name="ip_address",
                observed_value="",
                message="IP address is required but was empty.",
                suggested_action="Provide a valid IPv4 or IPv6 address."
            ))
        else:
            canon_ip, is_valid_ip = normalize_ip(raw_ip)
            if not is_valid_ip:
                issues.append(ValidationIssueDTO(
                    row_number=row_num,
                    asset_id=display_asset_id,
                    issue_code="INVALID_IP",
                    severity="error",
                    blocking=True,
                    field_name="ip_address",
                    observed_value=raw_ip,
                    message=f"'{raw_ip}' is not a valid IPv4 or IPv6 address.",
                    suggested_action="Correct the IP address format."
                ))
            elif canon_ip and canonical_ip_counts[canon_ip] > 1:
                issues.append(ValidationIssueDTO(
                    row_number=row_num,
                    asset_id=display_asset_id,
                    issue_code="DUPLICATE_IP",
                    severity="warning",
                    blocking=False,
                    field_name="ip_address",
                    observed_value=raw_ip,
                    message=f"IP address '{canon_ip}' is shared by {canonical_ip_counts[canon_ip]} records in this batch.",
                    suggested_action="Verify if this represents shared virtual hosting, NAT, or a duplicate entry."
                ))

        # 4. Asset Type
        raw_asset_type = clean_str(row.get("asset_type"))
        if not raw_asset_type:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="MISSING_ASSET_TYPE",
                severity="error",
                blocking=True,
                field_name="asset_type",
                observed_value="",
                message="Asset type is required but was empty.",
                suggested_action="Specify an asset type from the allowed categories."
            ))
        elif raw_asset_type.lower() not in ALLOWED_ASSET_TYPES:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="INVALID_ASSET_TYPE",
                severity="error",
                blocking=True,
                field_name="asset_type",
                observed_value=raw_asset_type,
                message=f"Asset type '{raw_asset_type}' is not recognized.",
                suggested_action=f"Allowed values: {', '.join(sorted([s.title() for s in ALLOWED_ASSET_TYPES]))}."
            ))

        # 5. Criticality
        raw_criticality = clean_str(row.get("criticality"))
        if not raw_criticality:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="MISSING_CRITICALITY",
                severity="error",
                blocking=True,
                field_name="criticality",
                observed_value="",
                message="Criticality is required for risk assessment.",
                suggested_action="Assign a criticality level (Critical, High, Medium, Low)."
            ))
        elif raw_criticality.lower() not in ALLOWED_CRITICALITIES:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="INVALID_CRITICALITY",
                severity="error",
                blocking=True,
                field_name="criticality",
                observed_value=raw_criticality,
                message=f"Criticality '{raw_criticality}' is invalid.",
                suggested_action="Allowed values: Critical, High, Medium, Low."
            ))

        # 6. Vulnerability Severity
        raw_vuln_sev = clean_str(row.get("vulnerability_severity"))
        if not raw_vuln_sev:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="MISSING_SEVERITY",
                severity="error",
                blocking=True,
                field_name="vulnerability_severity",
                observed_value="",
                message="Vulnerability severity is required for risk scoring.",
                suggested_action="Specify severity (Critical, High, Medium, Low, Informational, None)."
            ))
        elif raw_vuln_sev.lower() not in ALLOWED_SEVERITIES:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="INVALID_SEVERITY",
                severity="error",
                blocking=True,
                field_name="vulnerability_severity",
                observed_value=raw_vuln_sev,
                message=f"Vulnerability severity '{raw_vuln_sev}' is invalid.",
                suggested_action="Allowed values: Critical, High, Medium, Low, Informational, None."
            ))

        # 7. Owner Name and Owner Email
        raw_owner_name = clean_str(row.get("owner_name"))
        raw_owner_email = clean_str(row.get("owner_email"))

        if not raw_owner_name:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="MISSING_OWNER",
                severity="warning",
                blocking=False,
                field_name="owner_name",
                observed_value="",
                message="Asset has no assigned owner name.",
                suggested_action="Assign an asset custodian/owner to reduce unmanaged asset risk."
            ))
        else:
            if not raw_owner_email:
                issues.append(ValidationIssueDTO(
                    row_number=row_num,
                    asset_id=display_asset_id,
                    issue_code="MISSING_OWNER_EMAIL",
                    severity="warning",
                    blocking=False,
                    field_name="owner_email",
                    observed_value="",
                    message=f"Owner '{raw_owner_name}' has no contact email.",
                    suggested_action="Provide a contact email address for the owner."
                ))
            elif not is_valid_email(raw_owner_email):
                issues.append(ValidationIssueDTO(
                    row_number=row_num,
                    asset_id=display_asset_id,
                    issue_code="INVALID_OWNER_EMAIL",
                    severity="warning",
                    blocking=False,
                    field_name="owner_email",
                    observed_value=raw_owner_email,
                    message=f"Owner email '{raw_owner_email}' has invalid syntax.",
                    suggested_action="Provide a properly formatted email (user@domain.tld)."
                ))

        # 8. Vulnerability Count
        raw_vuln_count = clean_str(row.get("vulnerability_count"))
        if raw_vuln_count:
            _, is_valid_count = parse_non_negative_int(raw_vuln_count)
            if not is_valid_count:
                issues.append(ValidationIssueDTO(
                    row_number=row_num,
                    asset_id=display_asset_id,
                    issue_code="INVALID_VULNERABILITY_COUNT",
                    severity="error",
                    blocking=True,
                    field_name="vulnerability_count",
                    observed_value=raw_vuln_count,
                    message=f"Vulnerability count '{raw_vuln_count}' is not a valid non-negative integer.",
                    suggested_action="Set vulnerability count to an integer >= 0."
                ))

        # 9. Dates (purchase_date, last_updated)
        for date_col in ["purchase_date", "last_updated"]:
            raw_date = clean_str(row.get(date_col))
            if raw_date and not is_valid_iso_date(raw_date):
                issues.append(ValidationIssueDTO(
                    row_number=row_num,
                    asset_id=display_asset_id,
                    issue_code="INVALID_DATE",
                    severity="warning",
                    blocking=False,
                    field_name=date_col,
                    observed_value=raw_date,
                    message=f"{date_col} '{raw_date}' is not a valid ISO date.",
                    suggested_action="Format date as YYYY-MM-DD."
                ))

        # 10. Yes/No Booleans (internet_facing, backup_enabled, edr_enabled)
        for bool_col in ["internet_facing", "backup_enabled", "edr_enabled"]:
            raw_b = clean_str(row.get(bool_col))
            if raw_b and raw_b.lower() not in ALLOWED_BOOLEANS:
                issues.append(ValidationIssueDTO(
                    row_number=row_num,
                    asset_id=display_asset_id,
                    issue_code="INVALID_BOOLEAN_VALUE",
                    severity="warning",
                    blocking=False,
                    field_name=bool_col,
                    observed_value=raw_b,
                    message=f"{bool_col} contains '{raw_b}'. Expected Yes or No.",
                    suggested_action="Specify Yes or No."
                ))

        # 11. Environment
        raw_env = clean_str(row.get("environment"))
        if raw_env and raw_env.lower() not in ALLOWED_ENVIRONMENTS:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="INVALID_ENVIRONMENT",
                severity="warning",
                blocking=False,
                field_name="environment",
                observed_value=raw_env,
                message=f"Environment '{raw_env}' is not in standard list.",
                suggested_action=f"Allowed values: {', '.join(sorted([s.title() for s in ALLOWED_ENVIRONMENTS]))}."
            ))

        # 12. Data Classification
        raw_dc = clean_str(row.get("data_classification"))
        if raw_dc and raw_dc.lower() not in ALLOWED_DATA_CLASSIFICATIONS:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="INVALID_DATA_CLASSIFICATION",
                severity="warning",
                blocking=False,
                field_name="data_classification",
                observed_value=raw_dc,
                message=f"Data classification '{raw_dc}' is not recognized.",
                suggested_action=f"Allowed values: {', '.join(sorted([s.title() for s in ALLOWED_DATA_CLASSIFICATIONS]))}."
            ))

        # 13. Lifecycle Status
        raw_lc = clean_str(row.get("lifecycle_status"))
        if raw_lc and raw_lc.lower() not in ALLOWED_LIFECYCLES:
            issues.append(ValidationIssueDTO(
                row_number=row_num,
                asset_id=display_asset_id,
                issue_code="INVALID_LIFECYCLE_STATUS",
                severity="warning",
                blocking=False,
                field_name="lifecycle_status",
                observed_value=raw_lc,
                message=f"Lifecycle status '{raw_lc}' is not recognized.",
                suggested_action=f"Allowed values: {', '.join(sorted([s.title() for s in ALLOWED_LIFECYCLES]))}."
            ))

        # Row Status Evaluation
        has_blocking_error = any(i.blocking for i in issues)
        has_warning_or_info = any(not i.blocking for i in issues)

        if has_blocking_error:
            status = "blocked"
            result.blocked_rows += 1
        elif has_warning_or_info:
            status = "warning"
            result.warning_rows += 1
        else:
            status = "valid"
            result.valid_rows += 1

        result.row_statuses[row_num] = status
        result.row_issues[row_num] = issues
        result.all_issues.extend(issues)

    # Issue severity counts
    for issue in result.all_issues:
        if issue.severity == "error":
            result.error_count += 1
        elif issue.severity == "warning":
            result.warning_count += 1

    return result

