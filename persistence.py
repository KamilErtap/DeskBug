"""Atomic, backward-compatible local persistence and rotating diagnostics."""
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

log = logging.getLogger("deskbug")

def data_directory():
    return Path(os.getenv("LOCALAPPDATA") or Path.home()) / "DeskBug"

def read_json(path):
    try:
        value = path.read_text(encoding="utf-8")
        data = json.loads(value)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data
    except FileNotFoundError:
        return {}
    except (OSError, ValueError, TypeError):
        log.warning("Unable to read save: %s", path, exc_info=True)
        return {}

def write_json(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
        return True
    except OSError:
        log.exception("Unable to save: %s", path)
        return False

def configure_logging():
    close_logging()
    log.setLevel(logging.INFO)
    try:
        folder = data_directory()
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / "deskbug.log", maxBytes=524288, backupCount=2, encoding="utf-8")
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    log.addHandler(handler)


def close_logging():
    for handler in list(log.handlers):
        handler.close()
        log.removeHandler(handler)
