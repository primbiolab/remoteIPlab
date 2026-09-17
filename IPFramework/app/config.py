"""Configuración general de la aplicación (nivel servidor + hardware).

Contiene las rutas del servidor y las constantes físicas del hardware que
usa serial.py para convertir pulsos. La configuración de los controladores
vive por separado en control/config.py.
"""
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = SCRIPT_DIR.parent / "frontend"

MOTOR_PPR = 2400
SHAFT_R = 1.2