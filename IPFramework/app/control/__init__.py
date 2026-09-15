"""Selección del controlador (rol asignado a control.py).

Garantiza que la selección del "Controlador" hecha en el frontend se
aplique de verdad: elige la implementación según condicionales y delega
el cálculo de la ley de control al archivo correspondiente de la carpeta
control/.

Nota de estructura: este dispatcher vive en control/__init__.py y no en un
archivo control.py independiente porque Python NO permite coexistir un
módulo control.py con un paquete control/ en el mismo directorio (el
paquete opaca por completo al módulo, lo que lo volvería código muerto).
"""
from . import lqr

_AVAILABLE = {
    "lqr": lqr.LQRController,
}

_current_key = "lqr"
_current_name = "LQR"
_instances = {}


def _resolve_key(name: str) -> str:
    """Selección condicional según lo elegido en el frontend.

    Por ahora solo existe lqr.py: tanto "LQR" como "LQR + Swing-up"
    resuelven al mismo archivo. Si se agrega otro controlador, se añade
    aquí un caso nuevo sin tocar la lógica existente.
    """
    nl = (name or "").strip().lower()
    if "swing" in nl or nl in ("lqr", "lqr clasico"):
        return "lqr"
    # Futuros controladores:
    # if nl == "pid":
    #     return "pid"
    # if nl == "fuzzy":
    #     return "fuzzy"
    return "lqr"


def get_current_type() -> str:
    return _current_name


def set_controller(name: str, gains=None):
    """Aplica la selección del controlador y, si vienen, las ganancias."""
    global _current_key, _current_name
    _current_name = name or "LQR"
    _current_key = _resolve_key(_current_name)
    ctrl = get_controller()
    ctrl.reload_config()
    if gains:
        ctrl.set_gains(gains)
    return ctrl


def get_controller():
    inst = _instances.get(_current_key)
    if inst is None:
        inst = _instances.setdefault(_current_key, _AVAILABLE[_current_key]())
    return inst


def set_gains(gains):
    get_controller().set_gains(gains)


def get_gains() -> list:
    """Devuelve las ganancias actualmente configuradas para el controlador."""
    return list(get_controller().K)


def compute_control(state: dict, pos_limit_pulses: float, calibrated: bool = True) -> float:
    return get_controller().compute_control(state, pos_limit_pulses, calibrated)


def reset_startup():
    get_controller().reset_startup()