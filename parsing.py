from pathlib import Path
from typing import Dict, List

from config import MAX_TEXT_CHARS, SUPPORTED_EXTENSIONS
from schemas import ParsedDocument
from utils import clean_text, segment_text


def parse_document(file_path: Path) -> ParsedDocument:
    extension = file_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type: {0}".format(extension))

    if extension == ".pdf":
        normalized_text, metadata = _parse_pdf(file_path)
    elif extension in (".xlsx", ".xls"):
        normalized_text, metadata = _parse_excel(file_path)
    elif extension == ".csv":
        normalized_text, metadata = _parse_csv(file_path)
    else:
        normalized_text, metadata = _parse_text(file_path)

    normalized_text = clean_text(normalized_text)[:MAX_TEXT_CHARS]
    segments = segment_text(normalized_text)
    return ParsedDocument(
        source_file=str(file_path),
        file_name=file_path.name,
        file_extension=extension,
        normalized_text=normalized_text,
        segments=segments,
        parser_metadata=metadata,
    )


def _parse_pdf(file_path: Path) -> (str, Dict[str, int]):
    import fitz

    pages: List[str] = []
    with fitz.open(file_path) as document:
        for page in document:
            text = page.get_text("text")
            if text:
                pages.append("Page {0}\n{1}".format(page.number + 1, text))
    return "\n\n".join(pages), {"page_count": len(pages)}


def _parse_excel(file_path: Path) -> (str, Dict[str, int]):
    import pandas as pd

    excel = pd.read_excel(file_path, sheet_name=None)
    parts = []
    for sheet_name, frame in excel.items():
        frame = frame.fillna("")
        csv_like = frame.to_csv(index=False)
        parts.append("Sheet: {0}\n{1}".format(sheet_name, csv_like))
    return "\n\n".join(parts), {"sheet_count": len(parts)}


def _parse_csv(file_path: Path) -> (str, Dict[str, int]):
    import pandas as pd

    frame = pd.read_csv(file_path).fillna("")
    return frame.to_csv(index=False), {"row_count": len(frame.index)}


def _parse_text(file_path: Path) -> (str, Dict[str, int]):
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return text, {"char_count": len(text)}
