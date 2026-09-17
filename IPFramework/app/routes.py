"""Comunicación con el frontend (API REST + WebSocket).

Único archivo responsable de la comunicación con el frontend:
esquemas de las peticiones, endpoints REST y el WebSocket.
"""
import json
import csv
import io
import threading
from typing import Optional, List

from pydantic import BaseModel

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse

from .states import state, ws_broadcast, check_serial, check_idle
from . import control as control_dispatcher
from .loops import (
    _monitor_loop, _control_loop,
    _stop_all_threads, _clean_stop_and_close,
)

router = APIRouter()


# ── Esquemas de las peticiones del frontend ──────────────────────

class ConnectRequest(BaseModel):
    port: str
    baudrate: int = 115200


class GainsRequest(BaseModel):
    gains: List[float]


class ControllerRequest(BaseModel):
    controller: str = "LQR"
    gains: Optional[List[float]] = None


class MoveRequest(BaseModel):
    direction: str
    voltage: float = 5.0


# ── Health ──────────────────────────────────────────────────────

@router.get("/health")
async def health():
    ctrl = state.controller
    return {
        "status": "ok",
        "connected": ctrl.is_connected(),
        "running": state.is_running,
        "monitoring": state.is_monitoring,
        "controller": control_dispatcher.get_current_type(),
        "controllers": control_dispatcher.get_available(),
        "gains": control_dispatcher.get_gains(),
        "calibration": {
            "calibrated": ctrl.is_calibrated() if ctrl else False,
            "left_pulses": ctrl.rail_left_pulses if ctrl else 0,
            "right_pulses": ctrl.rail_right_pulses if ctrl else 0,
            "center_pulses": ctrl.rail_center_pulses if ctrl else 0,
            "limit_pulses": ctrl.pos_limit_pulses if ctrl else 5000,
        },
    }

# ── Serial ports ────────────────────────────────────────────────

@router.get("/ports")
async def list_ports():
    import serial.tools.list_ports
    ports = []
    for p in serial.tools.list_ports.comports():
        ports.append({"device": p.device, "description": p.description, "hwid": p.hwid})
    return {"ports": ports}

@router.post("/connect")
async def connect_serial(req: ConnectRequest):
    try:
        if state.controller.is_connected():
            state.controller.close()
        state.controller.port = req.port
        state.controller.baudrate = req.baudrate
        state.controller.connect()
        return {"status": "connected", "port": req.port}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/disconnect")
async def disconnect_serial():
    _clean_stop_and_close()
    return {"status": "disconnected"}

# ── Monitor ─────────────────────────────────────────────────────

@router.post("/monitor/start")
async def start_monitor():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    err = check_idle()
    if err:
        return JSONResponse(status_code=400, content=err)

    _stop_all_threads()
    state.is_monitoring = True
    state.monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    state.monitor_thread.start()
    return {"status": "monitoring"}

@router.post("/monitor/stop")
async def stop_monitor():
    _stop_all_threads()
    return {"status": "stopped"}

# ── Control ─────────────────────────────────────────────────────

@router.post("/start")
async def start_control():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    err = check_idle()
    if err:
        return JSONResponse(status_code=400, content=err)

    _stop_all_threads()
    for k in state.data_log:
        state.data_log[k] = []

    state.is_running = True
    state.control_thread = threading.Thread(target=_control_loop, daemon=True)
    state.control_thread.start()
    return {"status": "running", "controller": control_dispatcher.get_current_type()}

@router.post("/stop")
async def stop_control():
    _stop_all_threads()
    state.is_monitoring = True
    state.monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    state.monitor_thread.start()
    return {"status": "stopped", "monitor": True}

@router.post("/controller")
async def set_controller(req: ControllerRequest):
    gains = None
    if req.gains is not None and len(req.gains) == 4:
        gains = req.gains
    control_dispatcher.set_controller(req.controller, gains)
    return {"status": "ok", "controller": req.controller}

@router.post("/gains")
async def set_gains(req: GainsRequest):
    if len(req.gains) != 4:
        return JSONResponse(status_code=400, content={"error": "Se necesitan exactamente 4 ganancias"})
    control_dispatcher.set_gains(req.gains)
    return {"status": "ok", "gains": req.gains}

# ── Calibration ─────────────────────────────────────────────────

@router.post("/calibrate/left")
async def calibrate_left():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    _stop_all_threads()
    pulses = state.controller.set_left_limit()
    cm = state.controller.pulses_to_cm(pulses)
    if pulses == 0:
        return JSONResponse(status_code=500, content={"error": "No se recibió respuesta del Arduino"})
    return {"status": "ok", "pulses": pulses, "cm": cm}

@router.post("/calibrate/right")
async def calibrate_right():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    _stop_all_threads()
    pulses = state.controller.set_right_limit()
    cm = state.controller.pulses_to_cm(pulses)
    if pulses == 0:
        return JSONResponse(status_code=500, content={"error": "No se recibió respuesta del Arduino"})
    return {"status": "ok", "pulses": pulses, "cm": cm}

@router.post("/calibrate/compute_center")
async def calibrate_compute_center():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    _stop_all_threads()
    result = state.controller.compute_center()
    if result["center"] == 0 and result["left"] == 0 and result["right"] == 0:
        return JSONResponse(status_code=400, content={"error": "Primero fija ambos extremos"})
    state.calibration_pulses = abs(result["left"]) if abs(result["left"]) > abs(result["right"]) else abs(result["right"])
    state.calibration_cm = state.controller.pulses_to_cm(state.calibration_pulses)
    return {
        "status": "ok",
        "left_pulses": result["left"],
        "right_pulses": result["right"],
        "center_pulses": result["center"],
        "limit_pulses": state.calibration_pulses,
        "limit_cm": state.calibration_cm,
    }

@router.post("/calibrate/move_to_center")
async def calibrate_move_to_center():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    _stop_all_threads()
    if state.controller.rail_center_pulses == 0 and state.controller.rail_left_pulses != 0:
        state.controller.compute_center()
    ok = state.controller.move_to_center()
    state.controller.send_stop_motor()
    if ok:
        return {"status": "ok", "message": "Carro en centro"}
    return JSONResponse(status_code=500, content={"error": "No se pudo llegar al centro en el tiempo limite"})

@router.post("/calibrate/apply")
async def calibrate_apply():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    _stop_all_threads()
    limit_pulses = state.calibration_pulses
    limit_cm = state.calibration_cm
    try:
        state.controller.apply_calibration()
    except RuntimeError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    print(f"[Calibration] Calibración aplicada: límite {limit_pulses} pulsos ({limit_cm:.2f} cm)")
    return {"status": "ok", "limit_pulses": limit_pulses, "limit_cm": limit_cm}

@router.post("/calibrate/reset")
async def calibrate_reset():
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    _stop_all_threads()
    state.controller.reset_encoder()
    state.controller.pos_limit_pulses = 5000
    state.controller.rail_left_pulses = 0
    state.controller.rail_right_pulses = 0
    state.controller.rail_center_pulses = 0
    state.calibration_pulses = 5000
    state.calibration_cm = state.controller.pulses_to_cm(5000)
    print("[Calibration] Calibración reseteada")
    return {"status": "ok", "limit_pulses": 5000}

# ── Manual movement ─────────────────────────────────────────────

@router.post("/move/start")
async def move_start(req: MoveRequest):
    err = check_serial()
    if err:
        return JSONResponse(status_code=400, content=err)
    voltage = abs(req.voltage)
    if req.direction == "right":
        voltage = -voltage
    state.controller.send_voltage(voltage)
    return {"status": "moving", "direction": req.direction, "voltage": voltage}

@router.post("/move/stop")
async def move_stop():
    state.controller.send_voltage(0)
    return {"status": "stopped"}

# ── Data export ─────────────────────────────────────────────────

@router.get("/data/export")
async def export_data():
    if not state.data_log["time"]:
        return JSONResponse(status_code=404, content={"error": "No hay datos"})

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["time", "pos", "angle", "vel_pos", "vel_angle", "action"])
    for i in range(len(state.data_log["time"])):
        writer.writerow([
            state.data_log["time"][i],
            state.data_log["pos"][i],
            state.data_log["angle"][i],
            state.data_log["vel_pos"][i],
            state.data_log["vel_angle"][i],
            state.data_log["action"][i],
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pendulum_data.csv"},
    )

# ── WebSocket ───────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    state.ws_clients.append(ws)
    print(f"[WS] Cliente conectado. Total: {len(state.ws_clients)}")
    try:
        while True:
            data = await ws.receive_text()
            try:
                cmd = json.loads(data)
                action = cmd.get("action")

                if action == "set_controller":
                    gains = cmd.get("gains")
                    if gains is not None and len(gains) != 4:
                        gains = None
                    control_dispatcher.set_controller(cmd.get("controller", "LQR"), gains)
                elif action == "set_gains":
                    gains = cmd.get("gains", [])
                    if len(gains) == 4:
                        control_dispatcher.set_gains(gains)

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if ws in state.ws_clients:
            state.ws_clients.remove(ws)
        print(f"[WS] Cliente desconectado. Total: {len(state.ws_clients)}")