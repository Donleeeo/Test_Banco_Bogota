import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


class Embedder:
    def __init__(self) -> None:
        # Leo modelo y llave desde .env para evitar valores quemados en codigo.
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large").strip()
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY no esta configurada en .env")
        self.client = OpenAI(api_key=openai_api_key)
        self.model = embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Este metodo se usa para documentos y tambien para preguntas de consulta.
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]
