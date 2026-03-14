import shutil
from pathlib import Path
from typing import Optional

from classifier import classify_document
from config import DB_PATH, DEFAULT_MODEL, UPLOAD_DIR, ensure_directories
from database import DocumentRepository
from diffing import build_diff_artifacts
from extraction import extract_structured_data
from llm import OllamaClient
from matching import match_document
from parsing import parse_document
from schemas import PipelineResult


class DocumentPipeline(object):
    def __init__(self, model: str = DEFAULT_MODEL, use_llm: bool = True):
        ensure_directories()
        self.repository = DocumentRepository(DB_PATH)
        self.repository.initialize()
        self.model = model
        self.use_llm = use_llm

    def process_file(self, file_path: Path) -> PipelineResult:
        stored_source = self._store_source_file(file_path)
        parsed = parse_document(stored_source)

        llm_client = self._create_llm_client() if self.use_llm else None
        try:
            classification = classify_document(parsed, llm_client=llm_client)
            extracted = extract_structured_data(parsed, classification, llm_client=llm_client)
        except Exception as exc:
            if not _is_llm_dependency_error(exc):
                raise
            classification = classify_document(parsed, llm_client=None)
            extracted = extract_structured_data(parsed, classification, llm_client=None)

        existing = self.repository.fetch_all_documents()
        match = match_document(extracted, existing)
        extracted.matched_record_id = match.matched_record_id
        extracted.match_status = match.match_status
        extracted.change_summary = match.change_summary
        extracted.changed_fields = match.changed_fields
        extracted.supersedes_record_id = match.supersedes_record_id

        stored_record_id = self.repository.insert_document(extracted)
        old_record = None
        if match.matched_record_id:
            old_record = self.repository.fetch_document_by_id(match.matched_record_id)
        artifacts = build_diff_artifacts(
            old_record=old_record,
            new_record=extracted,
            changed_fields=match.changed_fields,
            document_id=stored_record_id,
        )
        self.repository.insert_artifact(stored_record_id, "markdown_diff", artifacts["markdown_path"])
        self.repository.insert_artifact(stored_record_id, "html_diff", artifacts["html_path"])

        return PipelineResult(
            extracted_record=extracted,
            diff_markdown=artifacts["markdown"],
            diff_html_path=artifacts["html_path"],
            stored_record_id=stored_record_id,
            parsed_document=parsed,
        )

    def _store_source_file(self, source_path: Path) -> Path:
        destination = UPLOAD_DIR / source_path.name
        counter = 1
        while destination.exists():
            destination = UPLOAD_DIR / "{0}_{1}{2}".format(
                source_path.stem,
                counter,
                source_path.suffix,
            )
            counter += 1
        shutil.copy2(str(source_path), str(destination))
        return destination

    def _create_llm_client(self) -> Optional[OllamaClient]:
        return OllamaClient(model=self.model)


def _is_llm_dependency_error(exc: Exception) -> bool:
    module_name = exc.__class__.__module__
    class_name = exc.__class__.__name__
    if module_name.startswith("requests"):
        return True
    if class_name in ("ConnectionError", "Timeout", "HTTPError"):
        return True
    return isinstance(exc, ImportError)
