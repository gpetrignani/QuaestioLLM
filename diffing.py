from html import escape
from pathlib import Path
from typing import Dict, List, Optional

from config import ARTIFACT_DIR
from schemas import ExtractedDocument


def build_diff_artifacts(
    old_record: Optional[Dict],
    new_record: ExtractedDocument,
    changed_fields: List[str],
    document_id: int,
) -> Dict[str, str]:
    markdown = _build_markdown(old_record, new_record, changed_fields)
    html = _build_html(old_record, new_record, changed_fields)

    markdown_path = ARTIFACT_DIR / "document_{0}_diff.md".format(document_id)
    html_path = ARTIFACT_DIR / "document_{0}_diff.html".format(document_id)
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")

    return {
        "markdown": markdown,
        "markdown_path": str(markdown_path),
        "html_path": str(html_path),
    }


def _build_markdown(old_record: Optional[Dict], new_record: ExtractedDocument, changed_fields: List[str]) -> str:
    lines = [
        "# Comparison Report",
        "",
        "## Summary",
        new_record.change_summary or "No summary available.",
        "",
        "## Changed Fields",
    ]
    if not changed_fields:
        lines.append("- None")
    else:
        for field in changed_fields:
            lines.append("- {0}".format(field))

    lines.extend(["", "## Old vs New", "", "| Field | Old | New |", "|---|---|---|"])
    payload = new_record.dict()
    fields = [
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
    for field in fields:
        old_value = old_record.get(field) if old_record else None
        new_value = payload.get(field)
        marker = " **changed**" if field in changed_fields else ""
        lines.append(
            "| {0}{1} | {2} | {3} |".format(
                field,
                marker,
                _stringify(old_value),
                _stringify(new_value),
            )
        )
    return "\n".join(lines) + "\n"


def _build_html(old_record: Optional[Dict], new_record: ExtractedDocument, changed_fields: List[str]) -> str:
    payload = new_record.dict()
    rows = []
    for field in [
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
    ]:
        css_class = "changed" if field in changed_fields else ""
        old_value = old_record.get(field) if old_record else None
        rows.append(
            "<tr class='{0}'><td>{1}</td><td>{2}</td><td>{3}</td></tr>".format(
                css_class,
                escape(field),
                escape(_stringify(old_value)),
                escape(_stringify(payload.get(field))),
            )
        )
    summary = escape(new_record.change_summary or "No summary available.")
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Comparison Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .changed td {{ background: #fff2cc; }}
    table {{ border-collapse: collapse; width: 100%; }}
    td, th {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
  </style>
</head>
<body>
  <h1>Comparison Report</h1>
  <h2>Summary</h2>
  <p>{0}</p>
  <table>
    <thead><tr><th>Field</th><th>Old</th><th>New</th></tr></thead>
    <tbody>{1}</tbody>
  </table>
</body>
</html>
""".format(summary, "".join(rows))


def _stringify(value) -> str:
    if value is None or value == "":
        return "null"
    return str(value)
