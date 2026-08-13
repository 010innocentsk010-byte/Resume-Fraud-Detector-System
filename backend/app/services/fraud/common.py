import re

from app.schemas.analysis import FraudFlag

YEAR_RE = re.compile(r"(19|20)\d{2}")


def extract_year(value: str | None) -> int | None:
    if not value:
        return None
    match = YEAR_RE.search(value)
    return int(match.group(0)) if match else None


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def make_flag(category: str, severity: str, title: str, message: str, evidence: list[str] | None = None) -> FraudFlag:
    return FraudFlag(category=category, severity=severity, title=title, message=message, evidence=evidence or [])
