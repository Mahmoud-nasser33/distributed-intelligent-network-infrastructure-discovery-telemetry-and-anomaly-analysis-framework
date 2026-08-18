import logging
import os
from pathlib import Path


def setup_logging(app):
    log_level = getattr(logging, app.config.get("DINAS_LOG_LEVEL", "INFO").upper(), logging.INFO)
    log_dir = Path(app.config.get("DINAS_LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_dir / "dinas.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    app.logger.setLevel(log_level)
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    app.logger.info("DINAS logging initialized at level %s", log_level)
