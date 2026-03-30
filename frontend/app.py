import os

import streamlit as st

from orchestration.orchestrator import DEFAULT_TOP_K, Orchestrator
from storage.qdrant_store import QdrantStore


@st.cache_resource(show_spinner=False)
def build_orchestrator() -> Orchestrator:
    # Reuso la misma instancia entre interacciones para que la UI sea fluida.
    qdrant_host = os.getenv("QDRANT_HOST", "localhost").strip() or "localhost"
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    store = QdrantStore(host=qdrant_host, port=qdrant_port)
    return Orchestrator(store=store)


def main() -> None:
    # UI pensada para demo: limpia, directa y sin controles tecnicos de mas.
    st.set_page_config(page_title="Orquestador RAG", layout="wide")

    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; max-width: 980px;}
        .hero {
            background: linear-gradient(135deg, #f2f7ff 0%, #eef9f2 100%);
            border: 1px solid #dbe7f5;
            border-radius: 14px;
            padding: 1.1rem 1.2rem;
            margin-bottom: 1rem;
        }
        .answer-box {
            background: #f8fafc;
            border: 1px solid #dbe3ea;
            border-radius: 12px;
            padding: 1rem 1rem;
        }
        .chunk-box {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hero">
          <h2 style="margin:0;">Orquestador RAG</h2>
          <p style="margin:0.35rem 0 0 0;">
            Haz una pregunta y el sistema consulta las colecciones necesarias:
            <b>Comentarios Banco</b>, <b>Productos</b> y <b>Bre-B</b>.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    question = st.text_input(
        "Pregunta",
        placeholder="Ej: beneficios de Cuenta Corriente Empresarial",
    )
    run = st.button("Consultar", type="primary", use_container_width=True)

    if run:
        if not question.strip():
            st.warning("Debes escribir una pregunta.")
            st.stop()

        try:
            orchestrator = build_orchestrator()
            with st.spinner("Consultando fuentes..."):
                result = orchestrator.answer(question=question.strip(), top_k=DEFAULT_TOP_K)
        except Exception as exc:
            st.error(f"Error al ejecutar la consulta: {exc}")
            st.stop()

        st.subheader("Respuesta")
        st.markdown(
            f"<div class='answer-box'>{result['answer']}</div>",
            unsafe_allow_html=True,
        )

        st.subheader("Top Chunks")
        # Muestro solo los primeros 3 para no saturar la pantalla.
        for idx, chunk in enumerate(result["chunks"][:3], start=1):
            st.markdown(
                f"""
                <div class="chunk-box">
                  <b>{idx}. {chunk['source']}</b> | score={chunk['score']:.4f}<br/>
                  {chunk['text'][:300]}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Ver trazabilidad tecnica"):
            st.write(f"Fuentes priorizadas: {result['route']['prioritized_sources']}")
            st.write(f"Fuentes consultadas: {result['sources_used']}")
            st.write(f"Chunks enviados al modelo: {len(result['chunks'])}")


if __name__ == "__main__":
    main()
