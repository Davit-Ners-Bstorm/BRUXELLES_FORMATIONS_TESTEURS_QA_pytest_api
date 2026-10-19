TIMEOUT = 5
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_json(relative_path):
    with open(PROJECT_ROOT / relative_path, encoding="utf-8") as f:
        return json.load(f)

def event_Array_Schema() : 
    eventOut = load_json("schemas/eventOut.json")
    return {
        "type" : "array",
        "items" : eventOut
    }