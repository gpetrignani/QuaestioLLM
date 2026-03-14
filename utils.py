import json
import re
from datetime import datetime
from typing import Any, Dict, Optional


DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%d %B %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %b %Y",
    "%Y/%m/%d",
)


def clean_text(value: str) -> str:
    value = value.replace("\x00", " ")
    value = re.sub(r"\r\n?", "\n", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def segment_text(value: str, max_chars: int = 2500) -> list:
    lines = [line.strip() for line in value.splitlines()]
    segments = []
    buffer = []
    size = 0
    for line in lines:
        if not line:
            if buffer and size >= max_chars:
                segments.append("\n".join(buffer).strip())
                buffer = []
                size = 0
            continue
        buffer.append(line)
        size += len(line)
        if size >= max_chars:
            segments.append("\n".join(buffer).strip())
            buffer = []
            size = 0
    if buffer:
        segments.append("\n".join(buffer).strip())
    return [segment for segment in segments if segment]


def parse_possible_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    match = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", text)
    if match:
        return "-".join(match.groups())
    return None


def parse_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^0-9,.\-]", "", text)
    if cleaned.count(",") > 0 and cleaned.count(".") > 0:
        cleaned = cleaned.replace(",", "")
    elif cleaned.count(",") > 0 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_nullable_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def safe_json_loads(value: str) -> Dict[str, Any]:
    start = value.find("{")
    end = value.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output.")
    return json.loads(value[start : end + 1])
