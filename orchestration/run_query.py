import os
from pathlib import Path

from dotenv import load_dotenv

from orchestration.orchestrator import Orchestrator
from storage.qdrant_store import QdrantStore

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
DEFAULT_TOP_K = 4


def main() -> None:
    qdrant_host = os.getenv("QDRANT_HOST", "localhost").strip() or "localhost"
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    store = QdrantStore(host=qdrant_host, port=qdrant_port)
    orchestrator = Orchestrator(store=store)
    question = input("Escribe tu pregunta: ").strip()
    if not question:
        raise ValueError("Debes ingresar una pregunta para continuar.")

    result = orchestrator.answer(question=question, top_k=DEFAULT_TOP_K)

    print("Respuesta:")
    print(result["answer"])
    print("")
    print("Trazabilidad:")
    print(f"- fuentes_priorizadas: {result['route']['prioritized_sources']}")
    print(f"- fuentes_consultadas: {result['sources_used']}")
    print(f"- chunks_enviados_al_modelo: {len(result['chunks'])}")
    for chunk in result["chunks"][:3]:
        print(
            f"- source={chunk['source']} collection={chunk['collection']} "
            f"score={chunk['score']:.4f} text={chunk['text'][:140]}"
        )


if __name__ == "__main__":
    main()
