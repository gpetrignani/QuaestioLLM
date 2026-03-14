# Quaestio Capital Local ETL MVP

Minimal local-first pipeline for ingesting investor documents, extracting structured JSON, matching against historical records, versioning new uploads, and generating a field-level comparison artifact.

## Architecture Overview

The pipeline is intentionally simple and local-only:

1. `Streamlit UI` accepts drag-and-drop uploads.
2. `Parser` converts PDF, Excel, CSV, or TXT into normalized text segments.
3. `Classifier` identifies document type, title, and dates.
4. `Structured extractor` calls a local Ollama model with strict JSON prompts.
5. `Validator` normalizes dates/numbers and retries extraction if validation fails.
6. `Matcher/versioning` compares the new record against historical SQLite records using deterministic heuristics.
7. `Storage layer` writes the new record and diff artifact paths to SQLite.
8. `Diff generator` produces Markdown and HTML old-vs-new comparison reports.

## Repository Structure

```text
quaestio_mvp/
  app.py
  cli.py
  classifier.py
  config.py
  database.py
  diffing.py
  extraction.py
  llm.py
  matching.py
  parsing.py
  pipeline.py
  prompts.py
  schemas.py
  utils.py
  prompt_templates/
    classifier_prompt.txt
    extractor_prompt.txt
samples/
  input/
    fund_fact_sheet_v1.txt
    fund_fact_sheet_v2.txt
  output/
    fund_fact_sheet_v2_expected.json
    fund_fact_sheet_v2_expected_diff.md
data/
  uploads/
  artifacts/
  quaestio_documents.db
requirements.txt
README.md
```

## Stack

- Python
- Ollama
- `qwen2.5:7b-instruct` by default
- PyMuPDF
- pandas + openpyxl
- Pydantic
- SQLite
- Streamlit

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:7b-instruct
```

## One-Command Run Flow

```bash
streamlit run quaestio_mvp/app.py
```

Open the local Streamlit URL, drag in a file, and the app will:

- parse and segment the document
- extract the structured JSON
- match it against stored records
- classify it as `NEW_DOCUMENT`, `NEW_VERSION_OF_EXISTING`, `RELATED_TO_EXISTING`, or `NO_MATCH`
- store the new row in SQLite
- generate Markdown and HTML diff artifacts in `data/artifacts/`

## CLI Flow

```bash
python3 -m quaestio_mvp.cli --file samples/input/fund_fact_sheet_v1.txt --no-llm
python3 -m quaestio_mvp.cli --file samples/input/fund_fact_sheet_v2.txt --no-llm
```

The second command will store a new version and create a comparison artifact against the first one.

## Matching and Versioning Rules

Deterministic matching prefers:

- same `fund_name`
- same `manager_name`
- same `document_type`
- same or similar `document_title`
- same `reference_code`
- newer `report_date` or `version_date`

Possible outcomes:

- `NEW_DOCUMENT`
- `NEW_VERSION_OF_EXISTING`
- `RELATED_TO_EXISTING`
- `NO_MATCH`

## JSON Contract

Extraction is constrained to the following primary schema:

```json
{
  "source_file": "string",
  "document_type": "string | null",
  "document_title": "string | null",
  "fund_name": "string | null",
  "manager_name": "string | null",
  "report_date": "YYYY-MM-DD | null",
  "version_date": "YYYY-MM-DD | null",
  "reference_code": "string | null",
  "currency": "string | null",
  "nav": "number | null",
  "commitment_amount": "number | null",
  "distribution_amount": "number | null",
  "status": "string | null",
  "notes": "string | null",
  "matched_record_id": "integer | null",
  "match_status": "string | null",
  "change_summary": "string | null",
  "changed_fields": [],
  "supersedes_record_id": "integer | null"
}
```

Rules enforced by prompt + validator:

- JSON only
- no invented values
- use `null` if missing
- ISO dates when possible
- numeric fields stay numeric

## Sample Input / Output

- Sample input: [`/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/input/fund_fact_sheet_v1.txt`](/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/input/fund_fact_sheet_v1.txt)
- Sample input: [`/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/input/fund_fact_sheet_v2.txt`](/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/input/fund_fact_sheet_v2.txt)
- Sample output JSON: [`/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/output/fund_fact_sheet_v2_expected.json`](/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/output/fund_fact_sheet_v2_expected.json)
- Sample diff report: [`/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/output/fund_fact_sheet_v2_expected_diff.md`](/Users/gianlucapetrignani/Desktop/terratium_SIM/samples/output/fund_fact_sheet_v2_expected_diff.md)

## Notes

- This MVP keeps everything local and does not use cloud APIs, vector databases, OCR, RAG, or microservices.
- If Ollama is unavailable, use `--no-llm` for a fully local heuristic fallback.
- PDF parsing uses PyMuPDF text extraction only; scanned PDFs are intentionally out of scope for the MVP.
