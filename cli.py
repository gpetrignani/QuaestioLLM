import argparse
import json
from pathlib import Path

from quaestio_mvp.config import DEFAULT_MODEL
from quaestio_mvp.pipeline import DocumentPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Quaestio Capital local ETL MVP")
    parser.add_argument("--file", required=True, help="Path to the input document")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip Ollama and use heuristic extraction only",
    )
    args = parser.parse_args()

    pipeline = DocumentPipeline(model=args.model, use_llm=not args.no_llm)
    result = pipeline.process_file(Path(args.file).expanduser().resolve())

    payload = result.extracted_record.dict()
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    print("\n---\n")
    print(result.diff_markdown)


if __name__ == "__main__":
    main()
