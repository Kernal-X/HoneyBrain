import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CACHE_DIR = os.path.join(BASE_DIR, "cache_store")
FILE_CACHE_PATH = os.path.join(CACHE_DIR, "file_cache.json")
SCHEMA_CACHE_PATH = os.path.join(CACHE_DIR, "schema_cache.json")

os.makedirs(CACHE_DIR, exist_ok=True)


def _load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ---------------- FILE CACHE ----------------

def get_file(path):
    file_cache = _load_json(FILE_CACHE_PATH)
    return file_cache.get(path)


def set_file(path, content):
    file_cache = _load_json(FILE_CACHE_PATH)
    file_cache[path] = {
        "content": content
    }
    _save_json(FILE_CACHE_PATH, file_cache)


# ---------------- SCHEMA CACHE ----------------

def get_schema(path):
    schema_cache = _load_json(SCHEMA_CACHE_PATH)
    return schema_cache.get(path)


def set_schema(path, schema):
    schema_cache = _load_json(SCHEMA_CACHE_PATH)
    schema_cache[path] = schema
    _save_json(SCHEMA_CACHE_PATH, schema_cache)