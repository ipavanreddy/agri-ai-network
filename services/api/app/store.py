"""Document store adapter: Firestore when FIREBASE_PROJECT_ID is set, local SQLite otherwise.

Collections used: farmers, fields, advisories, diagnoses, crop_recommendations.
"""

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Protocol

from app.config import settings

log = logging.getLogger(__name__)


class Store(Protocol):
    kind: str

    def put(self, collection: str, doc_id: str, data: dict[str, Any]) -> None: ...
    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None: ...
    def list(self, collection: str, **where: Any) -> list[dict[str, Any]]: ...


class SqliteStore:
    kind = "sqlite"

    def __init__(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS docs (collection TEXT, id TEXT, data TEXT, PRIMARY KEY (collection, id))"
        )
        self._conn.commit()

    def put(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO docs (collection, id, data) VALUES (?, ?, ?)",
                (collection, doc_id, json.dumps(data, default=str)),
            )
            self._conn.commit()

    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM docs WHERE collection = ? AND id = ?", (collection, doc_id)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, collection: str, **where: Any) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT data FROM docs WHERE collection = ? ORDER BY rowid", (collection,)).fetchall()
        docs = [json.loads(r[0]) for r in rows]
        return [d for d in docs if all(d.get(k) == v for k, v in where.items())]


class FirestoreStore:
    kind = "firestore"

    def __init__(self, project_id: str) -> None:
        import firebase_admin
        from firebase_admin import firestore

        app = firebase_admin.initialize_app(options={"projectId": project_id}) if not firebase_admin._apps else None
        self._db = firestore.client(app)

    def put(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        self._db.collection(collection).document(doc_id).set(json.loads(json.dumps(data, default=str)))

    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        snap = self._db.collection(collection).document(doc_id).get()
        return snap.to_dict() if snap.exists else None

    def list(self, collection: str, **where: Any) -> list[dict[str, Any]]:
        query = self._db.collection(collection)
        for k, v in where.items():
            query = query.where(k, "==", v)
        return [s.to_dict() for s in query.stream()]


_store: Store | None = None
_store_note: str | None = None


def get_store() -> Store:
    global _store, _store_note
    if _store is None:
        if settings.firestore_enabled:
            try:
                _store = FirestoreStore(settings.firebase_project_id)
            except Exception as exc:  # credentials missing etc. -> keep the demo running locally
                _store_note = f"Firestore unavailable ({type(exc).__name__}); using local SQLite"
                log.warning(_store_note)
        if _store is None:
            _store = SqliteStore(settings.store_path)
    return _store


def store_status() -> dict[str, Any]:
    s = get_store()
    return {"kind": s.kind, "mode": "live" if s.kind == "firestore" else "demo", "note": _store_note}


def reset_store(path: str | None = None) -> None:
    """Tests: point the store at a fresh SQLite file."""
    global _store, _store_note
    _store = SqliteStore(path) if path else None
    _store_note = None
