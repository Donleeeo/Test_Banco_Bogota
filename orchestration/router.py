import re

SOURCE_TO_COLLECTION = {
    "reviews": "bank_reviews_colombia",
    "products": "portafolio_productos_bancarios_v2_1",
    "breb": "documento_tecnico_bre_b_febrero_2026",
}
ALL_SOURCES = ["reviews", "products", "breb"]

SOURCE_KEYWORDS = {
    "reviews": ["sede", "comentario", "review", "experiencia", "satisfaccion", "atencion"],
    "products": ["producto", "portafolio", "cuenta", "tarjeta", "credito", "prestamo", "ahorro"],
    "breb": ["bre-b", "breb", "reglamento", "norma", "compensacion", "banco de la republica"],
}


class QueryRouter:
    def route(self, question: str) -> dict:
        q = question.lower()
        # Cuando viene codigo de sede, casi siempre la respuesta vive en reviews.
        if re.search(r"\b[a-z]{3}-[a-z0-9]+-\d{2}\b", q):
            return {
                "prioritized_sources": ["reviews"],
            }

        matched_counts = {
            source: sum(1 for term in terms if term in q)
            for source, terms in SOURCE_KEYWORDS.items()
        }
        matched_counts = {source: count for source, count in matched_counts.items() if count > 0}

        prioritized_sources = sorted(
            matched_counts.keys(),
            key=lambda source: matched_counts[source],
            reverse=True,
        )

        if not prioritized_sources:
            # Si no detecto una intencion clara, consulto todo para no sesgar de entrada.
            return {
                "prioritized_sources": ALL_SOURCES.copy(),
            }

        return {
            "prioritized_sources": prioritized_sources,
        }
