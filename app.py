import json
import tempfile
from pathlib import Path

import streamlit as st

from config import DEFAULT_MODEL
from pipeline import DocumentPipeline


st.set_page_config(page_title="Quaestio Capital ETL MVP", layout="wide")
st.title("Quaestio Capital Document ETL MVP")
st.caption("Local-first parsing, extraction, matching, versioning, and diff generation.")

with st.sidebar:
    model_name = st.text_input("Ollama model", value=DEFAULT_MODEL)
    use_llm = st.checkbox("Use local Ollama extraction", value=True)

uploaded = st.file_uploader(
    "Drag and drop a PDF, Excel, CSV, or TXT file",
    type=["pdf", "xlsx", "xls", "csv", "txt"],
)

if uploaded is not None:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        temp_path = Path(tmp.name)

    pipeline = DocumentPipeline(model=model_name, use_llm=use_llm)
    try:
        result = pipeline.process_file(temp_path)
        st.success("Document processed successfully.")
        left, right = st.columns(2)
        with left:
            st.subheader("Structured JSON")
            st.code(
                json.dumps(result.extracted_record.dict(), indent=2, ensure_ascii=True),
                language="json",
            )
        with right:
            st.subheader("Comparison Report")
            st.markdown(result.diff_markdown)
            if result.diff_html_path:
                st.caption("HTML diff saved to {0}".format(result.diff_html_path))
        st.subheader("Normalized Segments")
        st.json(result.parsed_document.segments)
    except Exception as exc:
        st.error("Processing failed: {0}".format(exc))
