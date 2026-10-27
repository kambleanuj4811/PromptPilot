"""Environment check for PromptPilot (standard library only).

Run from the project root:  python scripts/check_env.py
Never prints the API key. With a key set and google-genai installed, it also
lists the Gemini models your key can see, so you can pick a valid GEMINI_MODEL.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ok = True


def report(label, passed, detail=""):
    global ok
    ok = ok and passed
    print(f"[{'OK' if passed else 'MISSING'}] {label} {detail}".rstrip())


def load_env_file():
    env = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


print(f"Python {sys.version.split()[0]}")
report("Python >= 3.10", sys.version_info >= (3, 10))

node = shutil.which("node")
if node:
    ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    major = int(ver.lstrip("v").split(".")[0])
    report("Node.js >= 18", major >= 18, f"({ver})")
else:
    report("Node.js >= 18", False, "(not found; install the LTS from nodejs.org)")

for mod, pkg in [("fastapi", "fastapi"), ("uvicorn", "uvicorn"), ("sqlalchemy", "sqlalchemy"),
                 ("google.genai", "google-genai"), ("fitz", "pymupdf"), ("chromadb", "chromadb"),
                 ("sentence_transformers", "sentence-transformers"), ("pytest", "pytest")]:
    report(f"Python package {pkg}", has_module(mod))

env = load_env_file()
report(".env file present", (ROOT / ".env").exists(), "(copy .env.example to .env)")
key = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
report("GEMINI_API_KEY set", bool(key), "(value hidden)")
print(f"GEMINI_MODEL = {env.get('GEMINI_MODEL') or os.environ.get('GEMINI_MODEL') or '(unset)'}")

if key and has_module("google.genai"):
    try:
        from google import genai

        client = genai.Client(api_key=key)
        names = [m.name for m in client.models.list()]
        print(f"Key accepted. {len(names)} models visible; first 15:")
        for n in names[:15]:
            print("  ", n)
    except Exception as exc:  # report the error type only, never the key
        report("Gemini API reachable", False, f"({type(exc).__name__})")

print("\nResult:", "ready" if ok else "action needed (see MISSING items)")