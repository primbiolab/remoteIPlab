#!/usr/bin/env python3
"""
PRIMBIO — Servidor web para el Péndulo Invertido.
Ejecutar:  python server.py
Abrir:     http://localhost:8080
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import uvicorn
from app.web.main import app

if __name__ == "__main__":
    print("=" * 60)
    print("  PRIMBIO — Péndulo Invertido — Servidor Web")
    print(f"  Abrir: http://localhost:8080")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
