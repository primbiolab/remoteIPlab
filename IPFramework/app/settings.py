"""Configuración general de la aplicación (nivel servidor + hardware).

Contiene las rutas del servidor y las constantes físicas del hardware que
usa hardware/serial.py para convertir pulsos. La configuración de los
controladores vive por separado en control/config.py.

Modos de operación (variable de entorno APP_MODE):
  - "local"  (por defecto): para quien clona el repo. El usuario elige
    puerto serial, baudrate y cámara local desde el frontend.
  - "remote": para el PC del laboratorio expuesto en
    iplab.primbiolab.org. Puerto, baudrate y cámara son fijos y se
    autoconectan al arrancar. El frontend oculta la selección de puerto.
"""
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = SCRIPT_DIR.parent / "frontend"

MOTOR_PPR = 2400
SHAFT_R = 1.2

# ── Modo de operación ─────────────────────────────────────────────
# APP_MODE=local | remote
APP_MODE = os.getenv("APP_MODE", "local").strip().lower()
if APP_MODE not in ("local", "remote"):
    APP_MODE = "local"
IS_REMOTE = APP_MODE == "remote"

# ── Hardware fijo (usado en modo remote, valores por defecto en local) ──
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyACM0").strip()
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "115200").strip() or 115200)
AUTO_CONNECT = os.getenv("AUTO_CONNECT", "true" if IS_REMOTE else "false").strip().lower() in (
    "1", "true", "yes", "on",
)

# ── Cámara del laboratorio (modo remote: stream MJPEG servido por backend) ──
# CAMERA_INDEX: índice OpenCV (/dev/video0 -> 0) o URL RTSP/HTTP si aplica.
# CAMERA_ENABLED=false la desactiva (ej. laboratorio sin cámara).
CAMERA_INDEX = os.getenv("CAMERA_INDEX", "0").strip()
CAMERA_ENABLED = os.getenv("CAMERA_ENABLED", "true" if IS_REMOTE else "false").strip().lower() in (
    "1", "true", "yes", "on",
)
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640").strip() or 640)
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480").strip() or 480)
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "15").strip() or 15)

# Etiqueta mostrada en modo remoto (ej. "Laboratorio PRIMBIO — UNAL")
REMOTE_LABEL = os.getenv("REMOTE_LABEL", "Laboratorio PRIMBIO — Péndulo remoto")