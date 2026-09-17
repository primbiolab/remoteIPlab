"""Controlador LQR (Clásico + Swing-up).

Toda la lógica de control relacionada con LQR vive aquí en un único archivo.
Recibe el estado medido por serial.py y devuelve el voltaje a aplicar.
La selección del controlador la realiza control.py.
"""
import math

from .base import BaseController
from .config import G, MP, LP, JP
from . import config as ctrl_config


class LQRController(BaseController):
    name = "LQR + Swing-up"

    def __init__(self):
        # Constantes físicas compartidas desde config.py
        self.mplp = MP * LP
        self.INERTIA_EQ = JP + self.mplp * LP
        self.MGL = self.mplp * G
        self.desired_energy = 2 * self.MGL

        self.startup_kick_steps = 0
        self.reload_config()

    def reload_config(self):
        """Recarga ganancias y parámetros desde control/config.py."""
        self.K = list(ctrl_config.LQR_GAINS)
        self.k_swingup = ctrl_config.LQR_PARAMS["k_swingup"]
        self.theta_threshold = math.radians(ctrl_config.LQR_PARAMS["theta_threshold_deg"])
        self.angle_setpoint = ctrl_config.LQR_PARAMS["angle_setpoint"]
        self.startup_kick_voltage = ctrl_config.LQR_PARAMS["startup_kick_voltage"]
        self.startup_kick_max_steps = ctrl_config.LQR_PARAMS["startup_kick_max_steps"]
        self.startup_window_steps = ctrl_config.LQR_PARAMS["startup_window_steps"]
        self.startup_w_threshold = ctrl_config.LQR_PARAMS["startup_w_threshold"]

    def set_gains(self, gains):
        if len(gains) != 4:
            raise ValueError("Se necesitan exactamente 4 ganancias")
        self.K = [float(g) for g in gains]
        ctrl_config.LQR_GAINS[:] = self.K

    def reset_startup(self):
        self.startup_kick_steps = 0
        self.startup_window_steps = ctrl_config.LQR_PARAMS["startup_window_steps"]

    def avoidStall(self, u: float) -> float:
        MAX_STALL_U = 90.0
        if abs(u) < MAX_STALL_U:
            return (2.0 + MAX_STALL_U) if u > 0 else (-2.0 - MAX_STALL_U)
        return u

    def compute_control(self, state: dict, pos_limit_pulses: float, calibrated: bool = True) -> float:
        theta = state["angle_rad"]
        w = state["w_rad_s"]
        x = state["pos_cm"]
        v = state["vel_cm_s"]
        raw_pulses = state["raw_pulses"]

        if self.startup_window_steps > 0:
            self.startup_window_steps -= 1
            near_bottom = (theta > (2 * math.pi - 0.35) or theta < 0.35)
            near_rest = abs(w) < self.startup_w_threshold
            if near_bottom and near_rest and self.startup_kick_steps < self.startup_kick_max_steps:
                self.startup_kick_steps += 1
                kick_dir = -1.0 if raw_pulses > 0 else 1.0
                return kick_dir * self.startup_kick_voltage

        if calibrated and abs(raw_pulses) > pos_limit_pulses:
            return 12.0 if raw_pulses <= 0 else -12.0

        if abs(self.angle_setpoint - theta) < self.theta_threshold:
            u_lqr = (
                self.K[0] * (self.angle_setpoint - theta)
                - self.K[1] * w
                + self.K[2] * (0 - x)
                - self.K[3] * v
            )
            u_pwm = self.avoidStall(u_lqr)
            u_pwm = max(min(u_pwm, 255.0), -255.0)
            return u_pwm * (12.0 / 255.0)

        current_energy = (
            0.5 * self.INERTIA_EQ * (w ** 2)
            + self.MGL * (1 - math.cos(theta))
        )
        if (theta > (2 * math.pi - 0.28) or theta < 0.28) and current_energy < 0.85:
            accel = -300 * self.k_swingup * abs(current_energy - self.desired_energy) * w
            u_pwm = self.avoidStall(accel)
            u_pwm = max(min(u_pwm, 255.0), -255.0)
            return u_pwm * (12.0 / 255.0)

        return 0.0