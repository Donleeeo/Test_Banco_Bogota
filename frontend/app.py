import os

import streamlit as st

from orchestration.orchestrator import Orchestrator
from storage.qdrant_store import QdrantStore

DEFAULT_TOP_K = 4


@st.cache_resource(show_spinner=False)
def build_orchestrator() -> Orchestrator:
    qdrant_host = os.getenv("QDRANT_HOST", "localhost").strip() or "localhost"
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    store = QdrantStore(host=qdrant_host, port=qdrant_port)
    return Orchestrator(store=store)


def main() -> None:
    st.set_page_config(page_title="Orquestador RAG", layout="wide")
    st.title("Orquestador - Demo")
    st.caption("Canal unico para consultar reviews, products y breb.")

    with st.sidebar:
        st.subheader("Configuracion")
        top_k = st.number_input("Top K", min_value=1, max_value=10, value=DEFAULT_TOP_K, step=1)
        st.markdown("Colecciones: `reviews`, `products`, `breb`")

    question = st.text_input("Pregunta", placeholder="Ej: beneficios de Cuenta Corriente Empresarial")
    run = st.button("Consultar", type="primary", use_container_width=True)

    if run:
        if not question.strip():
            st.warning("Debes escribir una pregunta.")
            st.stop()

        try:
            orchestrator = build_orchestrator()
            with st.spinner("Consultando fuentes..."):
                result = orchestrator.answer(question=question.strip(), top_k=int(top_k))
        except Exception as exc:
            st.error(f"Error al ejecutar la consulta: {exc}")
            st.stop()

        st.subheader("Respuesta")
        st.write(result["answer"])

        st.subheader("Trazabilidad")
        st.write(f"Fuentes priorizadas: {result['route']['prioritized_sources']}")
        st.write(f"Fuentes consultadas: {result['sources_used']}")
        st.write(f"Chunks enviados al modelo: {len(result['chunks'])}")

        st.subheader("Top Chunks")
        for idx, chunk in enumerate(result["chunks"][:3], start=1):
            st.markdown(
                f"**{idx}.** source=`{chunk['source']}` | score=`{chunk['score']:.4f}`\n\n"
                f"{chunk['text'][:300]}"
            )


if __name__ == "__main__":
    main()
