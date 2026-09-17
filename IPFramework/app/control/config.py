"""Configuración de los controladores.

control.py (el dispatcher) le entrega a este archivo las configuraciones
provenientes del frontend (ganancias, parámetros). Desde aquí se persisten
y el controlador seleccionado las consume.

Cómo agregar config para un controlador nuevo:
    Añadir un bloque con el prefijo <CONTROLADOR>_ (p. ej. PID_GAINS) y que
    su clase en control/<nombre>.py lo lea desde aquí, igual que hace lqr.py
    con LQR_GAINS / LQR_PARAMS.
"""
import math

# ── LQR (LQR + Swing-up) ─────────────────────────────────────────

LQR_GAINS = [2110.0, 470, 50, 26.5]

LQR_PARAMS = {
    "k_swingup": 1.5,
    "theta_threshold_deg": 12.0,
    "angle_setpoint": math.pi,
    "startup_kick_voltage": 2.2,
    "startup_kick_max_steps": 12,
    "startup_window_steps": 200,
    "startup_w_threshold": 0.08,
}

# Constantes físicas del péndulo usadas por la ley de control LQR.
G = 9.81
MP = 0.097
LP = 0.2
JP = 0.00517333