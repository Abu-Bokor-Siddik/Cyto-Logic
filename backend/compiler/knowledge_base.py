import json
import os
import logging

_KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "parts.json")

_DATA = None

def _load():
    global _DATA
    if _DATA is not None:
        return _DATA
    if not os.path.isfile(_KB_PATH):
        logging.error("Knowledge Base file missing: %s", _KB_PATH)
        raise FileNotFoundError(
            f"Knowledge Base file not found: {_KB_PATH}. "
            "Ensure backend/data/parts.json exists."
        )
    try:
        with open(_KB_PATH, "r") as f:
            _DATA = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logging.error("Failed to load Knowledge Base: %s", exc)
        raise RuntimeError(
            f"Knowledge Base file is corrupted or unreadable: {_KB_PATH}. {exc}"
        ) from exc
    return _DATA


def reload():
    global _DATA
    _DATA = None
    return _load()


def get_parts():
    return _load().get("parts", {})


def get_gates():
    return _load().get("gates", {})


def get_biomolecules():
    return _load().get("biomolecules", {})


def get_reporters():
    return _load().get("reporters", {})


def get_additional_parts():
    return _load().get("additional_parts", {})


def get_regulatory_map():
    return _load().get("regulatory_map", {})


def get_part(part_id):
    return get_parts().get(part_id)


def get_gate(name):
    return get_gates().get(name, [])


def get_biomolecule(name):
    return get_biomolecules().get(name)


def get_reporter(name):
    return get_reporters().get(name)


def get_raw():
    return _load()