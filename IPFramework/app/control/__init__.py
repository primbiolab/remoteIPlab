"""Selección del controlador (dispatcher).

Paquete de controladores. Este __init__.py garantiza que la selección del
"Controlador" hecha en el frontend se aplique de verdad: resuelve el nombre
elegido a un controlador registrado y delega el cálculo de la ley de control
al módulo correspondiente de este mismo paquete.

Cómo agregar un controlador nuevo:
    1. Crear control/<nombre>.py con una clase que herede de BaseController
       (ver control/base.py) e implemente su contrato.
    2. Registrar la clase en _REGISTRY y sus nombres/alias de frontend en
       _ALIASES (este archivo). El dispatcher no requiere más cambios.
    3. Añadir el bloque de configuración del controlador en
       control/config.py.
"""
from . import lqr, base 

# Registro de controladores disponibles: clave interna -> clase concreta.
_REGISTRY = {
    "lqr": lqr.LQRController,
}

# Nombre mostrado en el frontend por cada clave del registro.
_LABELS = {
    "lqr": lqr.LQRController.name,
}

# Aliases (nombres que envía el frontend) que resuelven a cada clave.
_ALIASES = {
    "lqr": ("lqr", "lqr clasico", "lqr + swing-up"),
}

_current_key = next(iter(_REGISTRY))
_current_name = _LABELS[_current_key]
_instances = {}


def _resolve_key(name: str) -> str:
    """Resuelve el nombre elegido en el frontend a una clave del registro.

    Si el nombre no coincide con ningún alias conocido, se usa el primer
    controlador registrado como predeterminado.
    """
    nl = (name or "").strip().lower()
    if nl in _REGISTRY:
        return nl
    for key, aliases in _ALIASES.items():
        if nl in aliases:
            return key
    return next(iter(_REGISTRY))


def get_current_type() -> str:
    return _current_name


def _get_instance(key: str) -> base.BaseController:
    """Devuelve (y cachea) la instancia del controlador registrado en `key`."""
    inst = _instances.get(key)
    if inst is None:
        inst = _instances.setdefault(key, _REGISTRY[key]())
    return inst


def _validate_gains(ctrl: base.BaseController, gains):
    expected = len(ctrl.gain_labels)
    if expected == 0:
        raise ValueError("El controlador no tiene ganancias configurables")
    if not isinstance(gains, (list, tuple)) or len(gains) != expected:
        raise ValueError(f"Se esperan exactamente {expected} ganancias")


def set_controller(name: str, gains=None):
    """Aplica la selección del controlador y, si vienen, las ganancias."""
    global _current_key, _current_name
    key = _resolve_key(name or _current_name)
    ctrl = _get_instance(key)
    if gains is not None:
        _validate_gains(ctrl, gains)

    _current_key = key
    _current_name = _LABELS[key]
    ctrl.reload_config()
    if gains is not None:
        ctrl.set_gains(gains)
    return ctrl


def get_controller() -> base.BaseController:
    """Devuelve la instancia activa del controlador seleccionado."""
    return _get_instance(_current_key)


def get_available() -> list:
    """Devuelve la lista de controladores registrados.

    Formato: [{"key": ..., "label": ...}, ...]. Útil para que el frontend
    muestre dinámicamente los controladores disponibles.
    """
    return [{"key": key, "label": _LABELS[key]} for key in _REGISTRY]


def set_gains(gains):
    """Aplica ganancias al controlador activo validando su cantidad."""
    ctrl = get_controller()
    _validate_gains(ctrl, gains)
    ctrl.set_gains(gains)


def get_gains() -> list:
    """Devuelve las ganancias actualmente configuradas para el controlador."""
    return list(get_controller().K)


def get_gain_labels() -> list:
    """Devuelve las etiquetas de las ganancias del controlador activo.

    Lista vacía si el controlador no expone ganancias configurables.
    """
    return list(get_controller().gain_labels)


def compute_control(state: dict, pos_limit_pulses: float, calibrated: bool = True) -> float:
    return get_controller().compute_control(state, pos_limit_pulses, calibrated)


def reset_startup():
    get_controller().reset_startup()


def prepare_start(hw):
    """Preparación de arranque del controlador activo (ver BaseController).

    Se delega al controlador para que la secuencia previa al bucle
    (recentrar carro, espera, reset de arranque) no esté acoplada al bucle.
    """
    get_controller().prepare_start(hw)