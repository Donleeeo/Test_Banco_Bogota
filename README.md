# Prueba Tecnica - RAG Multi Fuente

Proyecto simple para consultar 3 fuentes desde un canal unico:

1. BRE-B (PDF)
2. Reviews de sedes (XLSX)
3. Portafolio de productos (PDF)

## Flujo

1. Ingesta: leer, normalizar, chunking, embedding (`text-embedding-3-large`) y guardado en Qdrant.
2. Orquestacion: recibir pregunta, elegir fuente(s), recuperar contexto y responder.
3. Presentacion: CLI unificada y UI en Streamlit.

## Estructura

```text
src/
  data/
  ingestion/
  orchestration/
  storage/
  frontend/
  presentation/
  .env
  requirements.txt
```

## Variables de entorno

Crear `src/.env`:

```env
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-large
RESPONSE_MODEL=gpt-5-mini
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Comandos (PowerShell)

Parado en la carpeta raiz del proyecto:

```powershell
cd src
```

Entry point unico:

Ingesta:

```powershell
& ..\.venv\Scripts\python.exe presentation/main.py --load_knowledge
& ..\.venv\Scripts\python.exe presentation/main.py --load_knowledge --source reviews
& ..\.venv\Scripts\python.exe presentation/main.py --load_knowledge --source products
& ..\.venv\Scripts\python.exe presentation/main.py --load_knowledge --source breb
```

Query:

```powershell
& ..\.venv\Scripts\python.exe presentation/main.py --query
```

Interfaz:

```powershell
& ..\.venv\Scripts\python.exe presentation/main.py --ui
```

## Colecciones Qdrant 

- `bank_reviews_colombia`
- `portafolio_productos_bancarios_v2_1`
- `documento_tecnico_bre_b_febrero_2026`
