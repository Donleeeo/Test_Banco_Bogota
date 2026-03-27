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
                    "Responde de forma clara y breve usando solo el contexto entregado. "
                    "Si faltan datos, dilo explicitamente. "
                    "Si la pregunta pide una cifra, reporta el valor literal que aparezca en el contexto. "
                    "No mezcles informacion de productos distintos; si el usuario pregunta por un producto especifico, "
                    "responde solo con fragmentos que mencionen explicitamente ese producto. "
                    "Incluye al final una linea 'Fuentes:' con los dominios usados (reviews, products, breb), sin numeracion."
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
        # Algunos modelos (por ejemplo gpt-5-mini) solo aceptan temperatura por defecto.
        if not self.model.startswith("gpt-5"):
            request_kwargs["temperature"] = 0.2

        response = self.client.chat.completions.create(**request_kwargs)
        return response.choices[0].message.content or ""
