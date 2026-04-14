import re


def validate_insight_id(insight_id: str) -> str:
    if not re.fullmatch(r"^TZ-\d+", insight_id):
        raise ValueError(f"Invalid insight_id: {insight_id}")
    return insight_id


def extract_shortname(groups: str) -> str:
    match = re.search(r"SG/([^,/]+)", groups)
    if not match:
        raise ValueError("Cannot extract shortname from groups")
    return match.group(1)
