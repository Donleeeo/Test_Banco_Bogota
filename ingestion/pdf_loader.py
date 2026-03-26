from pathlib import Path

from pypdf import PdfReader


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def load_pdf_pages(path: str | Path) -> list[dict]:
    reader = PdfReader(str(path))
    pages: list[dict] = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = _normalize_text((page.extract_text() or "").strip())
        if not text:
            continue
        pages.append({"page": page_num, "text": text})
    return pages


def load_pdf_text(path: str | Path) -> str:
    return "\n".join(item["text"] for item in load_pdf_pages(path))
