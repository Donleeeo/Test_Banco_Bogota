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
  frontend/
    app.py
  orchestration/
    router.py
    domain_agent.py
    orchestrator.py
    response_generator.py
    run_query.py
  presentation/
    main.py
  storage/
    qdrant_store.py
  .env
  requirements.txt
```

## Variables De Entorno

En `src/.env`:

- `OPENAI_API_KEY=...`
- `EMBEDDING_MODEL=text-embedding-3-small`
- `RESPONSE_MODEL=gpt-4o-mini`
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

Nota: si cambiaste la construccion de texto de reviews (por ejemplo incluir `Usuario <id>`), vuelve a correr:

```powershell
..\.venv\Scripts\python.exe -m ingestion.run_ingestion --source reviews
```

## Colecciones En Qdrant

- `bank_reviews_colombia`
- `portafolio_productos_bancarios_v2_1`
- `documento_tecnico_bre_b_febrero_2026`

## Orquestacion Minima

Consulta desde terminal:

```powershell
cd src
& ..\.venv\Scripts\python.exe -m orchestration.run_query
```

El script te pide la pregunta por consola.

El orquestador:

1. Recibe la pregunta.
2. Decide fuente(s) (`reviews`, `products`, `breb`).
3. Hace embedding de la pregunta.
4. Ejecuta `search top-k` por coleccion en Qdrant.
5. Genera respuesta final unificada con contexto recuperado.

## Capa De Presentacion (Entry Point Unico)

Desde `src`, puedes ejecutar todo desde un solo archivo:

```powershell
& ..\.venv\Scripts\python.exe presentation/main.py --load_knowledge
& ..\.venv\Scripts\python.exe presentation/main.py --query
```

Opcional para UI (cuando exista `frontend/app.py`):

```powershell
& ..\.venv\Scripts\python.exe presentation/main.py --ui
```

Comando directo de Streamlit:

```powershell
& ..\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```
