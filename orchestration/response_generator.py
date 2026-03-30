import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


class ResponseGenerator:
    def __init__(self) -> None:
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("RESPONSE_MODEL", "gpt-4o-mini").strip()
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY no esta configurada en .env")
        self.client = OpenAI(api_key=openai_api_key)

    def generate(self, question: str, chunks: list[dict]) -> str:
        if not chunks:
            return "No encontre informacion relevante en las colecciones consultadas."

        # Paso el contexto con score para que el modelo priorice lo mas fuerte.
        context_lines = []
        for i, chunk in enumerate(chunks, start=1):
            context_lines.append(
                f"[{i}] source={chunk['source']} score={chunk['score']:.4f} text={chunk['text']}"
            )
        context = "\n".join(context_lines)

        messages = [
            {
                "role": "system",
                "content": (
                    "Responde en espanol claro, natural y facil de entender para una persona no tecnica. "
                    "Usa frases cortas y evita jerga tecnica, siglas innecesarias o tono academico. "
                    "Empieza con la respuesta directa, sin introducciones como "
                    "'segun el contexto', 'con base en la informacion' o frases similares. "
                    "Responde solo con informacion del contexto entregado. "
                    "Si falta informacion, dilo de forma simple. "
                    "Si la pregunta pide una cifra, copia el valor literal del contexto. "
                    "No mezcles informacion de productos distintos; si preguntan por un producto especifico, "
                    "usa solo fragmentos de ese producto. "
                    "Cierra con una linea: 'Fuentes:' y lista solo los dominios usados "
                    "(reviews, products, breb), separados por coma."
                ),
            },
            {
                "role": "user",
                "content": f"Pregunta:\n{question}\n\nContexto recuperado:\n{context}",
            },
        ]

        request_kwargs = {
            "model": self.model,
            "messages": messages,
        }
        # Con modelos GPT-5 dejo la temperatura por defecto para evitar errores de compatibilidad.
        if not self.model.startswith("gpt-5"):
            request_kwargs["temperature"] = 0.2

        response = self.client.chat.completions.create(**request_kwargs)
        return response.choices[0].message.content or ""
