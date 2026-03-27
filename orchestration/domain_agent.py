import re

from orchestration.router import SOURCE_TO_COLLECTION
from storage.qdrant_store import QdrantStore


class DomainRetrievalAgent:
    def __init__(self, source: str, store: QdrantStore) -> None:
        self.source = source
        self.collection = SOURCE_TO_COLLECTION[source]
        self.store = store

    @staticmethod
    def _keywords_from_question(question: str) -> list[str]:
        q = question.lower()
        # Conserva tokens con underscore/hyphen para ids como user_3 o bog-chapinero-01
        raw_tokens = re.findall(r"[a-z0-9_-]+", q)
        user_tokens = re.findall(r"user[_-]?\d+", q)
        terms = []
        for token in raw_tokens + user_tokens:
            if len(token) >= 4 or any(ch.isdigit() for ch in token):
                terms.append(token)
        return list(dict.fromkeys(terms))

    def retrieve(self, q_vector: list[float], question: str, top_k: int) -> list[dict]:
        candidate_limit = max(top_k * 3, top_k)
        results = self.store.search(collection=self.collection, vector=q_vector, limit=candidate_limit)
        keywords = self._keywords_from_question(question)
        chunks: list[dict] = []
        for item in results:
            payload = item.payload or {}
            text = str(payload.get("text", ""))
            text_lower = text.lower()
            lexical_hits = sum(1 for kw in keywords if kw in text_lower)
            # Subimos el peso del match lexical para entidades exactas (user_3, codigos de sede, etc.).
            adjusted_score = float(item.score) + (0.08 * lexical_hits)
            chunks.append(
                {
                    "source": self.source,
                    "collection": self.collection,
                    "score": float(item.score),
                    "adjusted_score": adjusted_score,
                    "text": text,
                }
            )

        chunks.sort(key=lambda x: (x["adjusted_score"], x["score"]), reverse=True)
        return chunks[:top_k]
