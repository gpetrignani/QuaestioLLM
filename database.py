import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from schemas import ExtractedDocument


DOCUMENT_COLUMNS = [
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
    "matched_record_id",
    "match_status",
    "change_summary",
    "changed_fields",
    "supersedes_record_id",
]


class DocumentRepository(object):
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    document_type TEXT,
                    document_title TEXT,
                    fund_name TEXT,
                    manager_name TEXT,
                    report_date TEXT,
                    version_date TEXT,
                    reference_code TEXT,
                    currency TEXT,
                    nav REAL,
                    commitment_amount REAL,
                    distribution_amount REAL,
                    status TEXT,
                    notes TEXT,
                    matched_record_id INTEGER,
                    match_status TEXT,
                    change_summary TEXT,
                    changed_fields TEXT,
                    supersedes_record_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    artifact_type TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def insert_document(self, document: ExtractedDocument) -> int:
        values = document.dict()
        values["changed_fields"] = json.dumps(values.get("changed_fields") or [])
        placeholders = ", ".join("?" for _ in DOCUMENT_COLUMNS)
        columns = ", ".join(DOCUMENT_COLUMNS)
        ordered = [values.get(column) for column in DOCUMENT_COLUMNS]
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO documents ({0}) VALUES ({1})".format(columns, placeholders),
                ordered,
            )
            connection.commit()
            return int(cursor.lastrowid)

    def insert_artifact(self, document_id: int, artifact_type: str, artifact_path: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO artifacts (document_id, artifact_type, artifact_path)
                VALUES (?, ?, ?)
                """,
                (document_id, artifact_type, artifact_path),
            )
            connection.commit()

    def fetch_all_documents(self) -> List[Dict]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def fetch_document_by_id(self, document_id: int) -> Optional[Dict]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        payload = dict(row)
        try:
            payload["changed_fields"] = json.loads(payload.get("changed_fields") or "[]")
        except json.JSONDecodeError:
            payload["changed_fields"] = []
        return payload
