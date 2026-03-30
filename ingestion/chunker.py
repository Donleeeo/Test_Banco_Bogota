def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    # Normalizo espacios para que los cortes sean consistentes.
    if not text:
        return []
    text = " ".join(text.split())
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        # Dejo solape para no perder contexto entre chunks consecutivos.
        start = max(0, end - overlap)
    return chunks
