"""Configuración de los controladores.

control.py (el dispatcher en control/__init__.py) le entrega a este archivo
las configuraciones provenientes del frontend (ganancias, parámetros).
Desde aquí se persisten y el controlador seleccionado las consume.
Por ahora solo existe LQR, por lo que este archivo contiene sus ganancias.
"""
import math

LQR_GAINS = [1600.0, 140.0, -13.0, -7.5]

LQR_PARAMS = {
    "k_swingup": 1.5,
    "theta_threshold_deg": 12.0,
    "angle_setpoint": math.pi,
    "startup_kick_voltage": 2.2,
    "startup_kick_max_steps": 12,
    "startup_window_steps": 200,
    "startup_w_threshold": 0.08,
}