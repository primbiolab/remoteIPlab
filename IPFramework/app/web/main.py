import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from ..settings import FRONTEND_DIR, IS_REMOTE, AUTO_CONNECT, SERIAL_PORT, SERIAL_BAUD, CAMERA_ENABLED
from ..core.states import state
from .routes import router
from ..core.loops import _clean_stop_and_close


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.loop = asyncio.get_event_loop()
    # Modo remoto: autoconectar serial fijo y encender cámara del lab.
    if IS_REMOTE and AUTO_CONNECT:
        try:
            if not state.controller.is_connected():
                state.controller.port = SERIAL_PORT
                state.controller.baudrate = SERIAL_BAUD
                state.controller.connect()
                print(f"[remote] Serial autoconectado: {SERIAL_PORT} @ {SERIAL_BAUD}")
        except Exception as e:
            print(f"[remote] No se pudo autoconectar el serial ({SERIAL_PORT}): {e}")
    if IS_REMOTE and CAMERA_ENABLED:
        try:
            from ..hardware.camera import lab_camera
            lab_camera.start()
        except Exception as e:
            print(f"[remote] Cámara no disponible: {e}")
    yield
    try:
        from ..hardware.camera import lab_camera as _cam
        _cam.stop()
    except Exception:
        pass
    _clean_stop_and_close()


app = FastAPI(
    title="PRIMBIO — Péndulo Invertido",
    description="Servidor de control para péndulo invertido con Arduino",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# ── Frontend ────────────────────────────────────────────────────
# Estas rutas DEBEN ir al final para no interceptar los endpoints REST/WS.

@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>PRIMBIO — Frontend no encontrado</h1>")


@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    full_path = FRONTEND_DIR / file_path
    if full_path.exists() and full_path.is_file():
        return FileResponse(str(full_path))
    return HTMLResponse("<h1>Not Found</h1>", status_code=404)
