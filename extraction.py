from typing import Any, Dict, Optional

from pydantic import ValidationError

from config import MAX_VALIDATION_RETRIES
from prompts import render_prompt
from schemas import ClassificationResult, ExtractedDocument, ParsedDocument
from utils import normalize_nullable_string, parse_number, parse_possible_date


DOCUMENT_KEYS = [
    "source_file",
    "document_type",
    "document_title",
    "fund_name",
    "manager_name",
    "report_date",
    "version_date",
    "reference_code",
    "currency",
    "nav",
    "commitment_amount",
    "distribution_amount",
    "status",
    "notes",
]


def extract_structured_data(
    parsed: ParsedDocument,
    classification: ClassificationResult,
    llm_client=None,
) -> ExtractedDocument:
    if llm_client is None:
        return _heuristic_extract(parsed, classification)

    validation_feedback = ""
    for _ in range(MAX_VALIDATION_RETRIES):
        prompt = render_prompt(
            "extractor_prompt.txt",
            {
                "document_text": parsed.normalized_text,
                "classification_hint": classification.json(),
                "validation_feedback": validation_feedback or "None",
            },
        )
        payload = llm_client.generate_json(prompt)
        payload["source_file"] = parsed.source_file
        try:
            return _normalize_extracted(payload)
        except ValidationError as exc:
            validation_feedback = str(exc)
    return _heuristic_extract(parsed, classification)


def _normalize_extracted(payload: Dict[str, Any]) -> ExtractedDocument:
    normalized = {
        "source_file": payload.get("source_file"),
        "document_type": normalize_nullable_string(payload.get("document_type")),
        "document_title": normalize_nullable_string(payload.get("document_title")),
        "fund_name": normalize_nullable_string(payload.get("fund_name")),
        "manager_name": normalize_nullable_string(payload.get("manager_name")),
        "report_date": parse_possible_date(payload.get("report_date")),
        "version_date": parse_possible_date(payload.get("version_date")),
        "reference_code": normalize_nullable_string(payload.get("reference_code")),
        "currency": normalize_nullable_string(payload.get("currency")),
        "nav": parse_number(payload.get("nav")),
        "commitment_amount": parse_number(payload.get("commitment_amount")),
        "distribution_amount": parse_number(payload.get("distribution_amount")),
        "status": normalize_nullable_string(payload.get("status")),
        "notes": normalize_nullable_string(payload.get("notes")),
    }
    return ExtractedDocument(**normalized)


def _heuristic_extract(parsed: ParsedDocument, classification: ClassificationResult) -> ExtractedDocument:
    lines = [line.strip() for line in parsed.normalized_text.splitlines() if line.strip()]
    extracted: Dict[str, Optional[Any]] = {
        "source_file": parsed.source_file,
        "document_type": classification.document_type,
        "document_title": classification.document_title,
        "fund_name": None,
        "manager_name": None,
        "report_date": classification.report_date,
        "version_date": classification.version_date,
        "reference_code": None,
        "currency": None,
        "nav": None,
        "commitment_amount": None,
        "distribution_amount": None,
        "status": None,
        "notes": None,
    }

    field_aliases = {
        "fund name": "fund_name",
        "manager name": "manager_name",
        "reference code": "reference_code",
        "currency": "currency",
        "nav": "nav",
        "commitment amount": "commitment_amount",
        "distribution amount": "distribution_amount",
        "status": "status",
        "notes": "notes",
        "report date": "report_date",
        "version date": "version_date",
        "document title": "document_title",
    }

    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        target = field_aliases.get(key.strip().lower())
        if not target:
            continue
        value = value.strip()
        if target in ("nav", "commitment_amount", "distribution_amount"):
            extracted[target] = parse_number(value)
        elif target in ("report_date", "version_date"):
            extracted[target] = parse_possible_date(value)
        else:
            extracted[target] = normalize_nullable_string(value)

    return ExtractedDocument(**extracted)
