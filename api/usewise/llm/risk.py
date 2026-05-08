import re

WEIGHTS = {
    "sharing": 0.30,
    "tracking": 0.20,
    "retention": 0.25,
    "deletion": 0.15,
    "policy_changes": 0.10,
}

ANSWER_KEYS = ["sharing", "tracking", "retention", "deletion", "policy_changes"]

RETENTION_THRESHOLDS = {
    1: 0.0,
    6: 0.25,
    12: 0.5,
    24: 0.75,
}


def parse_months(answer: str | None) -> float | None:
    if not answer:
        return None

    v = answer.strip().lower()

    # Exact match against TIME_BUCKETS
    bucket_map = {
        "< 1 month": 0.5,
        "1-6 months": 3.5,
        "6-12 months": 9.0,
        "1-3 years": 18.0,
        "3+ years": 48.0,
        "indefinitely": None,
        "when account deleted": None,
    }

    if v in bucket_map:
        return bucket_map[v]

    # Fallback: regex pattern matching
    match = re.search(r"(\d+(?:\.\d+)?)\s*year", v)
    if match:
        return float(match.group(1)) * 12

    match = re.search(r"(\d+)\s*month", v)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d+)\s*day", v)
    if match:
        return float(match.group(1)) / 30

    return None


def flag_risk(answer: bool | None) -> tuple[float, bool]:  # noqa: FBT001
    if answer is True:
        return 0.0, False
    if answer is False:
        return 1.0, False
    return 0.5, True


def retention_risk(answer: str | None) -> tuple[float, bool]:
    months = parse_months(answer) if answer else None
    if months is None:
        return 0.6, True
    for threshold in sorted(RETENTION_THRESHOLDS.keys()):
        if months <= threshold:
            return RETENTION_THRESHOLDS[threshold], False
    return 1.0, False


def _clamp(value: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(max_val, value))


def calculate_risk(answers: dict[str, bool | str | None]) -> int:
    score = 0.0
    unclear = 0.0

    for key in ["sharing", "tracking", "retention", "deletion", "policy_changes"]:
        answer = answers[key]
        if key == "retention":
            risk, is_unclear = retention_risk(answer if isinstance(answer, str) else None)
        else:
            risk, is_unclear = flag_risk(answer if isinstance(answer, bool) else None)
        score += WEIGHTS[key] * risk
        unclear += WEIGHTS[key] * float(is_unclear)

    return _clamp(round(1 + 4 * (score + 0.15 * unclear)), 1, 5)
