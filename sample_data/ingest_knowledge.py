#!/usr/bin/env python3
"""Ingest curated synthetic knowledge docs into Qdrant + Postgres."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database.session import SessionLocal
from app.embeddings.qdrant_client import ensure_collections_exist, get_qdrant_client
from app.knowledge.ingestion_service import KnowledgeIngestionService
from app.knowledge.sources import SourceType


SOURCE_TYPE_MAP = {
    "medlineplus": SourceType.MEDLINEPLUS,
    "nih": SourceType.NIH_NIDDK,
    "niddk": SourceType.NIH_NIDDK,
    "nih_niddk": SourceType.NIH_NIDDK,
    "nhs": SourceType.NHS,
}


def main() -> None:
    knowledge_dir = Path(__file__).parent / "medical_knowledge"
    files = sorted(knowledge_dir.glob("*.json"))
    if not files:
        print("No knowledge JSON files found")
        sys.exit(1)

    ensure_collections_exist()
    client = get_qdrant_client()
    db = SessionLocal()
    service = KnowledgeIngestionService(db, client)

    ingested = 0
    for path in files:
        data = json.loads(path.read_text())
        source_key = (data.get("source_type") or "").lower()
        source_type = SOURCE_TYPE_MAP.get(source_key, SourceType.MEDLINEPLUS)
        source = service.ingest_content(
            url=data["source_url"],
            source_type=source_type,
            title=data["title"],
            content=data["content"],
            metadata={
                "access_date": data.get("access_date"),
                "topics": data.get("topics", []),
                "curated_file": path.name,
            },
        )
        print(f"Ingested {path.name} -> {source.id} ({source.publisher})")
        ingested += 1

    db.close()
    print(f"Done. {ingested} documents processed.")


if __name__ == "__main__":
    main()
