import argparse
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client.models import PointStruct

from ingestion.chunker import chunk_text
from ingestion.embedder import Embedder
from ingestion.excel_loader import load_reviews
from ingestion.pdf_loader import load_pdf_pages
from storage.qdrant_store import QdrantStore


@dataclass
class ChunkRecord:
    source: str
    text: str
    metadata: dict


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
logger = logging.getLogger("ingestion")

SOURCE_CONFIG = {
    "reviews": {
        "path": "data/bank_reviews_colombia.xlsx",
        "collection": "bank_reviews_colombia",
        "type": "excel",
    },
    "products": {
        "path": "data/portafolio_productos_bancarios_v2-1.pdf",
        "collection": "portafolio_productos_bancarios_v2_1",
        "type": "pdf",
    },
    "breb": {
        "path": "data/documento-tecnico-bre-b-febrero-2026.pdf",
        "collection": "documento_tecnico_bre_b_febrero_2026",
        "type": "pdf",
    },
}


def _stable_point_id(source: str, text: str, metadata: dict) -> int:
    raw = f"{source}|{text}|{metadata}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    # Qdrant soporta int64 para ids numericos
    return int(digest[:16], 16)


def _resolve_input_path(raw_path: str) -> Path:
    raw = Path(raw_path)
    candidates = [
        raw,
        Path("src") / raw,
        Path("data") / raw.name,
        Path("src/data") / raw.name,
        Path(raw.name),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Fallback para variantes de nombre como "archivo (1).pdf".
    for folder in [Path("."), Path("data"), Path("src/data")]:
        if not folder.exists():
            continue
        matched = sorted(folder.glob(f"{raw.stem}*{raw.suffix}"))
        if matched:
            return matched[0]

    raise FileNotFoundError(f"No se encontro el archivo de entrada: {raw_path}")


def _chunks_from_reviews(path: str, source: str) -> list[ChunkRecord]:
    resolved_path = _resolve_input_path(path)
    logger.info("Leyendo archivo Excel: %s", resolved_path)
    rows = load_reviews(resolved_path)
    logger.info("Filas leidas de Excel: %s", len(rows))
    records: list[ChunkRecord] = []
    for row in rows:
        text = f"Usuario {row['user_id']}. Sede {row['branch_id']}. Comentario: {row['comment']}"
        chunks = chunk_text(text, chunk_size=400, overlap=60)
        for idx, chunk in enumerate(chunks, start=1):
            records.append(
                ChunkRecord(
                    source=source,
                    text=chunk,
                    metadata={
                        "branch_id": row["branch_id"],
                        "user_id": row["user_id"],
                        "chunk_index": idx,
                    },
                )
            )
    logger.info("Chunks generados para %s: %s", source, len(records))
    return records


def _chunks_from_pdf(source: str, path: str) -> list[ChunkRecord]:
    resolved_path = _resolve_input_path(path)
    logger.info("Leyendo archivo PDF: %s", resolved_path)
    pages = load_pdf_pages(resolved_path)
    logger.info("Paginas utiles leidas de PDF (%s): %s", source, len(pages))
    records: list[ChunkRecord] = []
    for page_item in pages:
        chunks = chunk_text(page_item["text"], chunk_size=800, overlap=120)
        for idx, chunk in enumerate(chunks, start=1):
            records.append(
                ChunkRecord(
                    source=source,
                    text=chunk,
                    metadata={"page": page_item["page"], "chunk_index": idx},
                )
            )
    logger.info("Chunks generados para %s: %s", source, len(records))
    return records


def _upsert_records(collection: str, records: list[ChunkRecord], store: QdrantStore, embedder: Embedder) -> int:
    if not records:
        logger.warning("No hay registros para indexar en la coleccion %s", collection)
        return 0

    logger.info("Iniciando embeddings para coleccion %s. Registros: %s", collection, len(records))
    emb_start = time.perf_counter()
    vectors = embedder.embed([r.text for r in records])
    emb_elapsed = time.perf_counter() - emb_start
    logger.info(
        "Embeddings completados para %s en %.2fs. Dimension vectorial: %s",
        collection,
        emb_elapsed,
        len(vectors[0]),
    )

    store.ensure_collection(name=collection, vector_size=len(vectors[0]))
    logger.info("Coleccion lista en Qdrant: %s", collection)

    points: list[PointStruct] = []
    for record, vector in zip(records, vectors, strict=True):
        point_id = _stable_point_id(record.source, record.text, record.metadata)
        payload = {"source": record.source, "text": record.text, **record.metadata}
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    upsert_start = time.perf_counter()
    store.upsert(collection=collection, points=points)
    upsert_elapsed = time.perf_counter() - upsert_start
    logger.info(
        "Upsert completado en %s. Puntos: %s. Tiempo: %.2fs",
        collection,
        len(points),
        upsert_elapsed,
    )
    return len(points)


def ingest_reviews(store: QdrantStore, embedder: Embedder) -> int:
    config = SOURCE_CONFIG["reviews"]
    records = _chunks_from_reviews(path=config["path"], source="reviews")
    return _upsert_records(collection=config["collection"], records=records, store=store, embedder=embedder)


def ingest_products(store: QdrantStore, embedder: Embedder) -> int:
    config = SOURCE_CONFIG["products"]
    records = _chunks_from_pdf(source="products", path=config["path"])
    return _upsert_records(collection=config["collection"], records=records, store=store, embedder=embedder)


def ingest_breb(store: QdrantStore, embedder: Embedder) -> int:
    config = SOURCE_CONFIG["breb"]
    records = _chunks_from_pdf(source="breb", path=config["path"])
    return _upsert_records(collection=config["collection"], records=records, store=store, embedder=embedder)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline de ingesta para Qdrant")
    parser.add_argument(
        "--source",
        choices=["reviews", "products", "breb", "all"],
        default="all",
        help="Fuente a ingerir (por defecto: all).",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("openai._base_client").setLevel(logging.WARNING)

    run_start = time.perf_counter()
    args = parse_args()
    logger.info("Inicio de pipeline de ingesta. source=%s", args.source)
    qdrant_host = os.getenv("QDRANT_HOST", "localhost").strip() or "localhost"
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    logger.info("Configuracion Qdrant: host=%s port=%s", qdrant_host, qdrant_port)

    store = QdrantStore(host=qdrant_host, port=qdrant_port)
    embedder = Embedder()
    logger.info("Embedder inicializado con modelo=%s", embedder.model)

    if args.source == "reviews":
        count = ingest_reviews(store, embedder)
        logger.info("Finalizado source=reviews. Total=%s", count)
        logger.info("Pipeline finalizado en %.2fs", time.perf_counter() - run_start)
        return

    if args.source == "products":
        count = ingest_products(store, embedder)
        logger.info("Finalizado source=products. Total=%s", count)
        logger.info("Pipeline finalizado en %.2fs", time.perf_counter() - run_start)
        return

    if args.source == "breb":
        count = ingest_breb(store, embedder)
        logger.info("Finalizado source=breb. Total=%s", count)
        logger.info("Pipeline finalizado en %.2fs", time.perf_counter() - run_start)
        return

    counts = {
        "reviews": ingest_reviews(store, embedder),
        "products": ingest_products(store, embedder),
        "breb": ingest_breb(store, embedder),
    }
    logger.info("Ingesta completa")
    for key, value in counts.items():
        logger.info("source=%s collection=%s total_indexado=%s", key, SOURCE_CONFIG[key]["collection"], value)
    logger.info("Pipeline finalizado en %.2fs", time.perf_counter() - run_start)


if __name__ == "__main__":
    main()
