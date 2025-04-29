import json
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path("memory/memory.json")
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {
        "observations": [],
        "decisions": [],
        "reflections": []
    }

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def log_observation(data):
    memory = load_memory()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    memory["observations"].append(entry)
    save_memory(memory)

def log_decision(data):
    memory = load_memory()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    memory["decisions"].append(entry)
    save_memory(memory)

def log_reflection(data):
    memory = load_memory()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    memory["reflections"].append(entry)
    save_memory(memory)