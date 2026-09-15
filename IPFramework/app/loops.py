import math
import time
import threading

from .states import state, ws_broadcast
from . import control

# ── Monitor loop ────────────────────────────────────────────────

def _monitor_loop():
    state.run_start_time = time.time()
    ctrl = state.controller
    recovering = False
    recovery_start = 0

    while not state.stop_event.is_set():
        if ctrl.read_state_monitor():
            if ctrl.is_out_of_limits() and not recovering:
                recovering = True
                recovery_start = time.time()
                ctrl.send_stop_motor()
                ws_broadcast({
                    "pos": ctrl.state["pos_cm"],
                    "vel": ctrl.state["vel_cm_s"],
                    "angle": ctrl.state["raw_angle_deg"],
                    "ang_vel": ctrl.state["w_rad_s"],
                    "action": 0.0,
                    "raw_pulses": ctrl.state["raw_pulses"],
                    "raw_angle_deg": ctrl.state["raw_angle_deg"],
                    "pos_limit_pulses": ctrl.pos_limit_pulses,
                    "monitor": True,
                    "event": "out_of_limits",
                    "message": "Fuera de limites. Regresando al centro...",
                })
                time.sleep(0.5)
                ctrl.send_center()

            if recovering:
                elapsed = time.time() - recovery_start
                if elapsed > 4.0:
                    ctrl.send_stop_motor()
                    recovering = False

            ws_broadcast({
                "pos": ctrl.state["pos_cm"],
                "vel": ctrl.state["vel_cm_s"],
                "angle": ctrl.state["raw_angle_deg"],
                "ang_vel": ctrl.state["w_rad_s"],
                "action": 0.0,
                "raw_pulses": ctrl.state["raw_pulses"],
                "raw_angle_deg": ctrl.state["raw_angle_deg"],
                "pos_limit_pulses": ctrl.pos_limit_pulses,
                "monitor": True,
            })
        time.sleep(0.01)

# ── LQR + Swing-up control loop ─────────────────────────────────

def _control_loop_lqr():
    ctrl = state.controller
    ctrl.send_center()
    time.sleep(2)
    control.reset_startup()
    state.run_start_time = time.time()
    recovering = False
    recovery_start = 0

    while not state.stop_event.is_set():
        if ctrl.read_state():
            if ctrl.is_out_of_limits() and not recovering:
                recovering = True
                recovery_start = time.time()
                ctrl.send_stop_motor()
                ws_broadcast({
                    "pos": ctrl.state["pos_cm"],
                    "vel": ctrl.state["vel_cm_s"],
                    "angle": ctrl.state["raw_angle_deg"],
                    "ang_vel": ctrl.state["w_rad_s"],
                    "action": 0.0,
                    "raw_pulses": ctrl.state["raw_pulses"],
                    "raw_angle_deg": ctrl.state["raw_angle_deg"],
                    "pos_limit_pulses": ctrl.pos_limit_pulses,
                    "monitor": False,
                    "event": "out_of_limits",
                    "message": "Fuera de limites. Regresando al centro...",
                })
                time.sleep(0.5)
                ctrl.send_center()

            if recovering:
                elapsed = time.time() - recovery_start
                if elapsed > 4.0:
                    ctrl.send_stop_motor()
                    control.reset_startup()
                    state.run_start_time = time.time()
                    recovering = False

            if not recovering:
                u = control.compute_control(ctrl.state, ctrl.pos_limit_pulses, ctrl.is_calibrated())
                ctrl.send_voltage(u)

            t = time.time() - state.run_start_time
            telemetry = {
                "pos": ctrl.state["pos_cm"],
                "vel": ctrl.state["vel_cm_s"],
                "angle": ctrl.state["raw_angle_deg"],
                "ang_vel": ctrl.state["w_rad_s"],
                "action": ctrl.current_voltage if not recovering else 0.0,
                "raw_pulses": ctrl.state["raw_pulses"],
                "raw_angle_deg": ctrl.state["raw_angle_deg"],
                "pos_limit_pulses": ctrl.pos_limit_pulses,
                "monitor": False,
            }
            ws_broadcast(telemetry)

            if not recovering:
                state.data_log["time"].append(t)
                state.data_log["pos"].append(ctrl.state["pos_cm"])
                state.data_log["angle"].append(ctrl.state["raw_angle_deg"])
                state.data_log["vel_pos"].append(ctrl.state["vel_cm_s"])
                state.data_log["vel_angle"].append(ctrl.state["w_rad_s"])
                state.data_log["action"].append(ctrl.current_voltage)

        time.sleep(0.01)

    ctrl.send_stop_motor()

# ── Thread helpers ──────────────────────────────────────────────

def _stop_all_threads():
    state.stop_event.set()

    for attr in ("control_thread", "monitor_thread"):
        t = getattr(state, attr)
        if t and t.is_alive():
            t.join(timeout=3.0)
        setattr(state, attr, None)

    state.is_running = False
    state.is_monitoring = False
    state.stop_event.clear()

    ctrl = state.controller
    if ctrl.is_connected():
        ctrl.send_stop_motor()


def _clean_stop_and_close():
    _stop_all_threads()
    state.controller.close()
