from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ParsedDocument(BaseModel):
    source_file: str
    file_name: str
    file_extension: str
    normalized_text: str
    segments: List[str]
    parser_metadata: Dict[str, Any]


class ExtractedDocument(BaseModel):
    source_file: str
    document_type: Optional[str] = None
    document_title: Optional[str] = None
    fund_name: Optional[str] = None
    manager_name: Optional[str] = None
    report_date: Optional[str] = None
    version_date: Optional[str] = None
    reference_code: Optional[str] = None
    currency: Optional[str] = None
    nav: Optional[float] = None
    commitment_amount: Optional[float] = None
    distribution_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    matched_record_id: Optional[int] = None
    match_status: Optional[str] = None
    change_summary: Optional[str] = None
    changed_fields: List[str] = Field(default_factory=list)
    supersedes_record_id: Optional[int] = None

    @validator(
        "report_date",
        "version_date",
        pre=True,
    )
    def normalize_empty_dates(cls, value: Any) -> Optional[str]:
        if value in ("", "null", "None"):
            return None
        return value

    @validator("changed_fields", pre=True, always=True)
    def default_changed_fields(cls, value: Any) -> List[str]:
        if value is None:
            return []
        return value


class ClassificationResult(BaseModel):
    document_type: Optional[str] = None
    document_title: Optional[str] = None
    report_date: Optional[str] = None
    version_date: Optional[str] = None


class MatchResult(BaseModel):
    matched_record_id: Optional[int]
    match_status: str
    supersedes_record_id: Optional[int]
    changed_fields: List[str]
    change_summary: Optional[str]
    score: float


class PipelineResult(BaseModel):
    extracted_record: ExtractedDocument
    diff_markdown: str
    diff_html_path: Optional[str]
    stored_record_id: int
    parsed_document: ParsedDocument
