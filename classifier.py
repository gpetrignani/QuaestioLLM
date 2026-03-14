from prompts import render_prompt
from schemas import ClassificationResult, ParsedDocument
from utils import parse_possible_date


KNOWN_TYPES = {
    "fact sheet": "FUND_FACT_SHEET",
    "monthly portfolio": "MONTHLY_PORTFOLIO_REPORT",
    "investment committee": "INVESTMENT_COMMITTEE_MEMO",
    "due diligence": "DUE_DILIGENCE_REPORT",
}


def classify_document(parsed: ParsedDocument, llm_client=None) -> ClassificationResult:
    if llm_client is not None:
        prompt = render_prompt(
            "classifier_prompt.txt",
            {"document_text": parsed.normalized_text},
        )
        payload = llm_client.generate_json(prompt)
        return ClassificationResult(**payload)

    lowered = parsed.normalized_text.lower()
    document_type = None
    for needle, value in KNOWN_TYPES.items():
        if needle in lowered:
            document_type = value
            break

    title = parsed.file_name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
    report_date = None
    for line in parsed.normalized_text.splitlines():
        normalized = parse_possible_date(line)
        if normalized:
            report_date = normalized
            break

    return ClassificationResult(
        document_type=document_type,
        document_title=title,
        report_date=report_date,
        version_date=report_date,
    )
