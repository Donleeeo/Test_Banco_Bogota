import argparse
import logging
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    # Esta capa decide que flujo ejecutar desde un unico punto de entrada.
    parser = argparse.ArgumentParser(description="Capa de presentacion para ejecutar ingesta u orquestacion")
    parser.add_argument(
        "--load_knowledge",
        action="store_true",
        help="Ejecuta la ingesta de conocimiento en Qdrant",
    )
    parser.add_argument(
        "--source",
        choices=["reviews", "products", "breb"],
        help="Fuente opcional para la ingesta: reviews, products o breb",
    )
    parser.add_argument(
        "--query",
        action="store_true",
        help="Ejecuta el flujo de consulta orquestada",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Ejecuta la interfaz Streamlit (cuando exista frontend/app.py)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    for noisy_logger in ["httpx", "urllib3", "oauthlib", "qdrant_client"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    args = parse_args()

    if args.load_knowledge:
        # Si no se especifica fuente, cargamos las 3 para mantener un comando simple.
        sources = [args.source] if args.source else ["reviews", "products", "breb"]
        for source in sources:
            logging.info("Starting knowledge load ... source=%s", source)
            subprocess.run(
                [sys.executable, "-m", "ingestion.run_ingestion", "--source", source],
                check=True,
            )
        return

    if args.query:
        # Flujo interactivo de pregunta-respuesta por consola.
        logging.info("Starting orchestrator query flow ...")
        subprocess.run([sys.executable, "-m", "orchestration.run_query"], check=True)
        return

    if args.ui:
        # Front de demostracion en Streamlit.
        logging.info("Starting Streamlit UI ...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/app.py"], check=True)
        return

    logging.info("No command provided. Usa --load_knowledge o --query o --ui")


if __name__ == "__main__":
    main()
