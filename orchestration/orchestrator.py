from ingestion.embedder import Embedder
from orchestration.domain_agent import DomainRetrievalAgent
from orchestration.response_generator import ResponseGenerator
from orchestration.router import ALL_SOURCES, QueryRouter
from storage.qdrant_store import QdrantStore

MIN_EVIDENCE_SCORE = 0.30


class Orchestrator:
    def __init__(self, store: QdrantStore) -> None:
        self.store = store
        self.embedder = Embedder()
        self.router = QueryRouter()
        self.response_generator = ResponseGenerator()
        self.domain_agents = {
            source: DomainRetrievalAgent(source=source, store=store) for source in ALL_SOURCES
        }

    def _ask_agents(
        self,
        q_vector: list[float],
        question: str,
        sources: list[str],
        top_k: int,
    ) -> list[dict]:
        chunks: list[dict] = []
        for source in sources:
            source_chunks = self.domain_agents[source].retrieve(
                q_vector=q_vector,
                question=question,
                top_k=top_k,
            )
            chunks.extend(source_chunks)

        chunks.sort(key=lambda x: (x["adjusted_score"], x["score"]), reverse=True)
        return chunks

    def answer(self, question: str, top_k: int = 4) -> dict:
        route = self.router.route(question)
        prioritized_sources = route["prioritized_sources"]
        q_vector = self.embedder.embed([question])[0]

        phase1_chunks = self._ask_agents(
            q_vector=q_vector,
            question=question,
            sources=prioritized_sources,
            top_k=top_k,
        )
        expanded_sources: list[str] = []
        best_score = phase1_chunks[0]["score"] if phase1_chunks else 0.0
        enough_count = len(phase1_chunks) >= max(2, top_k)
        enough_score = best_score >= MIN_EVIDENCE_SCORE
        fallback_needed = not (enough_count and enough_score)
        fallback_triggered = False
        combined_chunks = phase1_chunks
        sources_used = prioritized_sources
        if fallback_needed:
            expanded_sources = [source for source in ALL_SOURCES if source not in prioritized_sources]
            if expanded_sources:
                phase2_chunks = self._ask_agents(
                    q_vector=q_vector,
                    question=question,
                    sources=expanded_sources,
                    top_k=top_k,
                )
                combined_chunks = phase1_chunks + phase2_chunks
                combined_chunks.sort(key=lambda x: (x["adjusted_score"], x["score"]), reverse=True)
                sources_used = prioritized_sources + expanded_sources
                fallback_triggered = True

        # Salida final compacta: top_k global para reducir ruido y costo.
        selected = combined_chunks[: max(top_k, 1)]
        answer = self.response_generator.generate(question=question, chunks=selected)

        return {
            "question": question,
            "sources_used": sources_used,
            "chunks": selected,
            "answer": answer,
            "route": route,
            "fallback_triggered": fallback_triggered,
        }
