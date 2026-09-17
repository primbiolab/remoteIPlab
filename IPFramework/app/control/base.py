"""Interfaz común de los controladores.

Todos los controladores de la carpeta control/ deben heredar de
BaseController y cumplir este contrato. control.py (el dispatcher)
interactúa con cualquier controlador únicamente a través de esta interfaz,
por lo que agregar un controlador nuevo no requiere tocar el dispatcher
salvo registrarlo (ver control.py).
"""
from abc import ABC, abstractmethod
import time


class BaseController(ABC):
    """Contrato que todo controlador debe implementar.

    Atributos esperados:
        K: lista de ganancias actuales (usada por control.get_gains()).
        startup_delay: segundos que el bucle espera tras recentrar el carro
            en el arranque.
    """

    name: str = "Base"

    K: list = []

    startup_delay: float = 2.0

    def prepare_start(self, hw):
        """Preparación previa al bucle de control.

        Por omisión recentra el carro, espera `startup_delay` segundos a que
        se estabilice y reinicia el estado de arranque. Cada controlador
        puede sobrescribirlo si necesita otra secuencia de arranque.
        """
        hw.send_center()
        time.sleep(self.startup_delay)
        self.reset_startup()

    @abstractmethod
    def reload_config(self):
        """Recarga ganancias y parámetros desde control/config.py."""
        raise NotImplementedError

    @abstractmethod
    def set_gains(self, gains):
        """Aplica las ganancias recibidas desde el frontend."""
        raise NotImplementedError

    @abstractmethod
    def reset_startup(self):
        """Reinicia el estado de arranque del controlador."""
        raise NotImplementedError

    @abstractmethod
    def compute_control(self, state: dict, pos_limit_pulses: float, calibrated: bool = True) -> float:
        """Calcula y devuelve el voltaje a aplicar según el estado medido."""
        raise NotImplementedError