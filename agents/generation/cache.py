import os
import json
import hashlib

CACHE_DIR = "cache/generated_files"


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _path_to_cache_key(path: str) -> str:
    return hashlib.md5(path.encode()).hexdigest()


def _cache_file_path(path: str) -> str:
    key = _path_to_cache_key(path)
    return os.path.join(CACHE_DIR, f"{key}.json")


def set_file(path: str, data: dict):
    """
    Store generated fake artifact in cache.

    Expected data format:
    {
        "content": "...",
        "schema": [...],
        "metadata": {...}
    }
    """
    _ensure_cache_dir()
    cache_path = _cache_file_path(path)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_file(path: str):
    """
    Retrieve cached fake artifact for a given path.

    Returns:
        dict or None
    """
    cache_path = _cache_file_path(path)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clear_cache():
    """
    Optional helper to wipe all cached generated files.
    """
    if not os.path.exists(CACHE_DIR):
        return

    for file_name in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)