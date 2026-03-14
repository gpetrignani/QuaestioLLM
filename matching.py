from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from schemas import ExtractedDocument, MatchResult


COMPARE_FIELDS = [
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


def match_document(
    document: ExtractedDocument,
    existing_documents: List[Dict],
) -> MatchResult:
    if not existing_documents:
        return MatchResult(
            matched_record_id=None,
            match_status="NEW_DOCUMENT",
            supersedes_record_id=None,
            changed_fields=[],
            change_summary="No historical documents found.",
            score=0.0,
        )

    best_record = None
    best_score = 0.0
    for record in existing_documents:
        score = _score_candidate(document, record)
        if score > best_score:
            best_score = score
            best_record = record

    if best_record is None:
        return MatchResult(
            matched_record_id=None,
            match_status="NO_MATCH",
            supersedes_record_id=None,
            changed_fields=[],
            change_summary="No candidate exceeded the minimum matching threshold.",
            score=0.0,
        )

    changed_fields = _compute_changed_fields(document, best_record)
    if best_score < 2.0:
        return MatchResult(
            matched_record_id=best_record["id"],
            match_status="NO_MATCH",
            supersedes_record_id=None,
            changed_fields=changed_fields,
            change_summary="Potentially related record found, but match score is too low.",
            score=best_score,
        )

    if _is_newer_version(document, best_record):
        summary = "Detected a newer version with changes in: {0}".format(
            ", ".join(changed_fields) if changed_fields else "no structured fields"
        )
        return MatchResult(
            matched_record_id=best_record["id"],
            match_status="NEW_VERSION_OF_EXISTING",
            supersedes_record_id=best_record["id"],
            changed_fields=changed_fields,
            change_summary=summary,
            score=best_score,
        )

    if best_score >= 3.0:
        summary = "Related historical record found with overlapping identity fields."
        return MatchResult(
            matched_record_id=best_record["id"],
            match_status="RELATED_TO_EXISTING",
            supersedes_record_id=None,
            changed_fields=changed_fields,
            change_summary=summary,
            score=best_score,
        )

    return MatchResult(
        matched_record_id=None,
        match_status="NEW_DOCUMENT",
        supersedes_record_id=None,
        changed_fields=[],
        change_summary="No strong historical match found; storing as a new document.",
        score=best_score,
    )


def _score_candidate(document: ExtractedDocument, record: Dict) -> float:
    score = 0.0
    if _equals(document.fund_name, record.get("fund_name")):
        score += 1.5
    if _equals(document.manager_name, record.get("manager_name")):
        score += 1.0
    if _equals(document.document_type, record.get("document_type")):
        score += 1.0
    if _equals(document.reference_code, record.get("reference_code")):
        score += 2.0
    title_similarity = _similarity(document.document_title, record.get("document_title"))
    if title_similarity >= 0.8:
        score += 1.5
    elif title_similarity >= 0.6:
        score += 0.75
    return score


def _compute_changed_fields(document: ExtractedDocument, record: Dict) -> List[str]:
    changed = []
    payload = document.dict()
    for field in COMPARE_FIELDS:
        if payload.get(field) != record.get(field):
            changed.append(field)
    return changed


def _is_newer_version(document: ExtractedDocument, record: Dict) -> bool:
    document_date = document.version_date or document.report_date
    record_date = record.get("version_date") or record.get("report_date")
    if document_date and record_date:
        return document_date > record_date
    return False


def _equals(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    return left.strip().lower() == str(right).strip().lower()


def _similarity(left: Optional[str], right: Optional[str]) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left.lower(), str(right).lower()).ratio()
