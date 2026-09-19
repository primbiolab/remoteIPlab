"""Cámara del laboratorio para modo remoto.

Sirve la cámara fija del PC del laboratorio como stream MJPEG
(GET /camera/stream) para que los visitantes de
iplab.primbiolab.org vean el péndulo real sin usar su webcam local.

En modo local (APP_MODE=local) este módulo queda desactivado y el frontend
sigue usando getUserMedia (cámara del propio usuario).
"""
import threading
import time

from ..settings import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS


class LabCamera:
    def __init__(self):
        self._lock = threading.Lock()
        self._cap = None
        self._last_jpeg: bytes | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def _parse_source(self):
        src = (CAMERA_INDEX or "0").strip()
        # Permite índice numérico (/dev/video0 -> 0) o URL (RTSP/HTTP).
        if src.isdigit() or (src.startswith("-") and src[1:].isdigit()):
            return int(src)
        return src

    def start(self) -> bool:
        try:
            import cv2  # import tardío: opcional en modo local
        except ImportError:
            print("[LabCamera] opencv no instalado; cámara remota desactivada.")
            return False
        if self._running:
            return True
        src = self._parse_source()
        cap = cv2.VideoCapture(src)
        if CAMERA_WIDTH:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        if CAMERA_HEIGHT:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        if CAMERA_FPS:
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        if not cap.isOpened():
            print(f"[LabCamera] No se pudo abrir la cámara: {src!r}")
            cap.release()
            return False
        self._cap = cap
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        print(f"[LabCamera] Cámara abierta: {src!r}")
        return True

    def _capture_loop(self):
        import cv2

        interval = 1.0 / max(CAMERA_FPS, 1)
        while self._running and self._cap is not None:
            ok, frame = self._cap.read()
            if ok:
                ok_enc, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok_enc:
                    with self._lock:
                        self._last_jpeg = bytes(buf)
            else:
                time.sleep(0.2)
            time.sleep(interval)

    def stop(self):
        self._running = False
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def is_running(self) -> bool:
        return self._running and self._cap is not None

    def get_jpeg(self) -> bytes | None:
        with self._lock:
            return self._last_jpeg


lab_camera = LabCamera()


def mjpeg_generator(poll_interval: float = 0.07):
    """Generador multipart/x-mixed-replace para StreamingResponse."""
    while True:
        frame = lab_camera.get_jpeg()
        if frame is None:
            time.sleep(poll_interval)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
            + frame + b"\r\n"
        )
        time.sleep(poll_interval)
