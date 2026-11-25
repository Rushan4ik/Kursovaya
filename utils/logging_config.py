import logging


def setup_logging(filename: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(filename, encoding="utf-8"), logging.StreamHandler()],
    )
