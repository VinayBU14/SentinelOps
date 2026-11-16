import ipaddress
import re
from typing import Optional, Tuple

def clean_str(val: Optional[str]) -> str:
    """Trim whitespace and return empty string if None or whitespace."""
    if val is None:
        return ""
    return str(val).strip()

def normalize_ip(val: Optional[str]) -> Tuple[Optional[str], bool]:
    """
    Validate and return canonical IP string.
    Returns (canonical_ip_str, is_valid).
    """
    cleaned = clean_str(val)
    if not cleaned:
        return None, False
    try:
        ip_obj = ipaddress.ip_address(cleaned)
        return str(ip_obj), True
    except ValueError:
        return cleaned, False

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(val: Optional[str]) -> bool:
    """Basic email syntax check."""
    cleaned = clean_str(val)
    if not cleaned:
        return False
    return bool(_EMAIL_REGEX.match(cleaned))

_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def is_valid_iso_date(val: Optional[str]) -> bool:
    """Check if date matches YYYY-MM-DD format."""
    cleaned = clean_str(val)
    if not cleaned:
        return False
    if not _DATE_REGEX.match(cleaned):
        return False
    try:
        from datetime import datetime
        datetime.strptime(cleaned, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def parse_non_negative_int(val: Optional[str]) -> Tuple[Optional[int], bool]:
    """
    Validate and return non-negative integer.
    Returns (int_val, is_valid).
    """
    cleaned = clean_str(val)
    if not cleaned:
        return None, False
    try:
        num = int(cleaned)
        if num >= 0:
            return num, True
        return num, False
    except ValueError:
        return None, False

