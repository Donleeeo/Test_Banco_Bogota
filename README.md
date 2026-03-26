# Ingestion Simple Para La Prueba Tecnica

Este repositorio quedo enfocado solo en la fase de ingestion:

1. Leer archivos PDF y Excel.
2. Normalizar texto.
3. Hacer chunking.
4. Generar embeddings con `text-embedding-3-small`.
5. Guardar en Qdrant (una coleccion por archivo).

## Estructura Actual

```text
src/
  data/
    documento-tecnico-bre-b-febrero-2026.pdf
    portafolio_productos_bancarios_v2-1.pdf
    bank_reviews_colombia.xlsx
  ingestion/
    pdf_loader.py
    excel_loader.py
    chunker.py
    embedder.py
    run_ingestion.py
  storage/
    qdrant_store.py
  .env
  requirements.txt
```

## Variables De Entorno

En `src/.env`:

- `OPENAI_API_KEY=...`
- `EMBEDDING_MODEL=text-embedding-3-small`
- `QDRANT_HOST=localhost`
- `QDRANT_PORT=6333`

Las rutas de los 3 archivos se manejan directo en `ingestion/run_ingestion.py`.

## Ejecutar Ingestion

Desde la raiz del proyecto:

```powershell
cd src
..\.venv\Scripts\python.exe -m ingestion.run_ingestion --source all
```

Opcional por fuente:

```powershell
..\.venv\Scripts\python.exe -m ingestion.run_ingestion --source reviews
..\.venv\Scripts\python.exe -m ingestion.run_ingestion --source products
..\.venv\Scripts\python.exe -m ingestion.run_ingestion --source breb
```

## Colecciones En Qdrant

- `bank_reviews_colombia`
- `portafolio_productos_bancarios_v2_1`
- `documento_tecnico_bre_b_febrero_2026`
