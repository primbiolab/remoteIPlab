"""Selección del controlador (dispatcher).

Único archivo responsable de garantizar que la selección del "Controlador"
hecha en el frontend se aplique de verdad: resuelve el nombre elegido a un
controlador registrado y delega el cálculo de la ley de control al archivo
correspondiente de la carpeta control/.

Cómo agregar un controlador nuevo:
    1. Crear control/<nombre>.py con una clase que herede de BaseController
       (ver control/base.py) e implemente su contrato.
    2. Registrar la clase en _REGISTRY y sus nombres/alias de frontend en
       _ALIASES (control.py). El dispatcher no requiere más cambios.
    3. Añadir el bloque de configuración del controlador en
       control/config.py.

Nota de estructura: el dispatcher vive en un módulo control.py que convive
con la carpeta control/ (donde están los controladores). Como un paquete
con __init__.py opacaría al módulo del mismo nombre, la carpeta control/ NO
tiene __init__.py: aquí se expone su ruta mediante __path__, de modo que
app.control.lqr y app.control.config sigan resolviendo a los archivos de la
carpeta control/.
"""
import os

__path__ = [os.path.join(os.path.dirname(__file__), "control")]

from app.control import lqr, base

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


def set_controller(name: str, gains=None):
    """Aplica la selección del controlador y, si vienen, las ganancias."""
    global _current_key, _current_name
    _current_name = name or _LABELS[_current_key]
    _current_key = _resolve_key(_current_name)
    _current_name = _LABELS[_current_key]
    ctrl = get_controller()
    ctrl.reload_config()
    if gains:
        ctrl.set_gains(gains)
    return ctrl


def get_controller() -> base.BaseController:
    """Devuelve la instancia activa del controlador seleccionado."""
    inst = _instances.get(_current_key)
    if inst is None:
        inst = _instances.setdefault(_current_key, _REGISTRY[_current_key]())
    return inst


def get_available() -> list:
    """Devuelve la lista de controladores registrados.

    Formato: [{"key": ..., "label": ...}, ...]. Útil para que el frontend
    muestre dinámicamente los controladores disponibles.
    """
    return [{"key": key, "label": _LABELS[key]} for key in _REGISTRY]


def set_gains(gains):
    get_controller().set_gains(gains)


def get_gains() -> list:
    """Devuelve las ganancias actualmente configuradas para el controlador."""
    return list(get_controller().K)


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