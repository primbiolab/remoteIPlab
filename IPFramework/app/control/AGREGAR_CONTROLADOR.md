# Cómo agregar un controlador nuevo

Esta guía explica paso a paso cómo integrar un controlador nuevo al sistema,
cómo recibir la salida del Arduino y qué valores debe devolver el controlador
para mover el motor.

## Arquitectura (en resumen)

```
Arduino ──R\n──▶ hardware/serial.py ──state (dict)──▶ control/<nombre>.py
          ◀─0VV.VV\n── send_voltage() ◀─────────────── (compute_control)
```

- `hardware/serial.py` es el ÚNICO archivo que habla con el Arduino (lectura
  de estado, envío de voltaje, calibración). No contiene lógica de control.
- Cada controlador vive en su propio archivo dentro de `control/` y hereda de
  `BaseController` (ver `control/base.py`).
- `control/__init__.py` (el dispatcher) resuelve qué controlador está activo y
  delega a él todos los cálculos. El bucle genérico de control en
  `core/loops.py` (`_control_loop`) funciona con cualquier controlador sin
  modificaciones.
- El frontend lista los controladores automáticamente leyendo `/health`
  (campos `controllers`, `gains` y `gain_labels`), generados por
  `control.get_available()`, `control.get_gains()` y
  `control.get_gain_labels()`.

Para agregar un controlador nuevo NO hace falta tocar `hardware/serial.py`,
`core/loops.py`, `web/routes.py` ni el frontend.

---

## 1. Cómo se recibe la salida del Arduino

La lectura de estado ocurre en `hardware/serial.py` (`read_state`). El
protocolo es:

1. Python envía la línea `R\n` por el puerto serial.
2. El Arduino responde UNA línea con 4 valores separados por coma:

```
<motorPosition>,<angle>,<motorSpeed>,<angularSpeed>
```

| Campo Arduino       | Unidad      | Descripción                                   |
|---------------------|-------------|-----------------------------------------------|
| `motorPosition`     | pulsos      | Posición del carro (encoder del motor).       |
| `angle`             | grados      | Ángulo del péndulo, rango [-180, 180). 0 = vertical hacia arriba, positivo en sentido horario. |
| `motorSpeed`        | pulsos/s    | Velocidad del carro (suavizada).              |
| `angularSpeed`      | grados/s    | Velocidad angular del péndulo (suavizada).    |

3. Python convierte esa línea y la deja en el `state` que recibe el
   controlador en `compute_control`:

| Clave del `state` | Unidad | Significado |
|-------------------|--------|-------------|
| `raw_pulses`      | pulsos | Posición cruda del encoder del motor. |
| `raw_angle_deg`   | grados | Ángulo crudo que envía el Arduino. |
| `angle_rad`       | rad    | Ángulo convertido a radianes en [0, 2π). Este es el que usa la ley de control (en LQR, `π` = péndulo vertical arriba). |
| `w_rad_s`         | rad/s  | Velocidad angular. |
| `pos_cm`          | cm     | Posición del carro convertida a centímetros. |
| `vel_cm_s`        | cm/s   | Velocidad del carro en centímetros por segundo. |

> Ejemplo real (voltaje nulo):
> ```
> Arduino → 43,179.4,120.5,3.2
> state   → {"raw_pulses": 43, "raw_angle_deg": 179.4, "angle_rad": 3.131,
>            "w_rad_s": -0.0558, "pos_cm": 0.135, "vel_cm_s": 0.377}
> ```

`SerialController` también expone, aparte del `state`, cosas útiles para el
control: `pos_limit_pulses` (límite del carril en pulsos), `is_calibrated()`
y `is_out_of_limits()`.

---

## 2. Qué debe devolver el controlador (salida hacia el Arduino)

`compute_control(state, pos_limit_pulses, calibrated)` debe devolver UN número:
el VOLTAJE a aplicar al motor, en voltios.

El bucle lo pasa a `ctrl.send_voltage(u)` (`hardware/serial.py`), que envía al Arduino
una línea con el formato:

```
0<voltage>:.2f
```

Ejemplos con `send_voltage`:

| Valor devuelto | Línea enviada        |
|----------------|----------------------|
| 5.0            | `05.00\n`            |
| -3.5           | `0-3.50\n`           |
| 12.0           | `012.00\n`           |

El Arduino interpreta: primer carácter `0` = modo voltaje, y el resto es el
voltaje en volts; luego lo mapea `map(value, -12, 12, -255, 255)` a PWM.

Reglas obligatorias:

- **Devuelve voltios, NO PWM.** El rango útil es [-12, 12]. Recorta
  (`clamp`) tu salida a ese rango para no saturar el motor.
- **El signo decide el sentido del motor.** Un valor positivo mueve en un
  sentido y negativo en el otro. Si tu ley de control mueve en el sentido
  equivocado, invierte el signo (o los signos de tus ganancias).
- **No devuelvas exactamente 0 si quieres que el motor venza la fricción.**
  LQR lo resuelve con `avoidStall()`, que mantiene un voltaje mínimo en lugar
  de 0 cuando la ley de control pide un valor muy pequeño.

---

## 3. Paso a paso: integrar un controlador nuevo

### Paso 1 — Crear el archivo del controlador

Crea `control/<nombre>.py` con una clase que herede de `BaseController`
(ver `control/base.py`) y que implemente su contrato:

| Método (abstracto)      | Descripción |
|--------------------------|-------------|
| `reload_config()`        | Carga ganancias y parámetros desde `control/config.py`. Se llama al seleccionar el controlador. |
| `set_gains(gains)`       | Aplica las ganancias enviadas desde el frontend (lista). |
| `reset_startup()`        | Reinicia el estado interno de arranque del controlador. El bucle lo llama al iniciar y tras recuperarse de una salida de límites. |
| `compute_control(state, pos_limit_pulses, calibrated)` | Calcula y devuelve el voltaje a aplicar, usando el `state` de la sección 1. |

Atributos utilizados por el sistema:

- `name: str` → nombre que se muestra en el frontend.
- `K: list` → ganancias actuales (la usa `control.get_gains()`).
- `gain_labels: list` → etiquetas de cada ganancia, en el mismo orden que `K`.
  Define cuántos campos genera el panel de ganancias. Si está vacía, el
  controlador no expone ganancias configurables.
- `startup_delay: float = 2.0` → segundos que el bucle espera tras recentrar
  el carro en el arranque.
- `prepare_start(hw)` (opcional sobrescribir) → secuencia previa al bucle.
  Por omisión: `hw.send_center()`, espera `startup_delay` y llama
  `reset_startup()`. Sobrescríbelo solo si necesitas otro arranque.

### Paso 2 — Configuración en `control/config.py`

Añade un bloque de configuración propio con el prefijo de tu controlador,
p. ej. para un PID:

```python
# ── PID ─────────────────────────────────────────────────────────
PID_GAINS = [10.0, 1.0, 0.1]

PID_PARAMS = {
    "integral_limit": 50.0,
}
```

Tu clase lo leerá desde `reload_config()` (igual que hace `lqr.py`).

### Paso 3 — Registrar el controlador en `control/__init__.py`

En `control/__init__.py` (el dispatcher) registras la clase y sus nombres:

```python
from app.control import lqr, base, pid  # ← importa tu módulo

_REGISTRY = {
    "lqr": lqr.LQRController,
    "pid": pid.PIDController,            # ← añade tu controlador
}

_LABELS = {
    "lqr": lqr.LQRController.name,
    "pid": pid.PIDController.name,       # ← nombre mostrado en el frontend
}

_ALIASES = {
    "lqr": ("lqr", "lqr clasico", "lqr + swing-up"),
    "pid": ("pid", "pid clasico"),       # ← nombres que puede enviar el frontend
}
```

Con esto el controlador:
- Aparece automáticamente en el `<select>` del frontend (vía `/health`).
- Es seleccionable por su clave (`pid`) o por cualquiera de sus aliases.
- Sus `gain_labels` generan dinámicamente los campos del panel de ganancias y
  su `K` se muestra/edita en esos campos.

### Paso 4 — Verificar

1. Arranca el servidor: `python server.py` (desde `IPFramework/`).
2. Abre el frontend y comprueba que tu controlador aparece en el selector.
3. Conéctate al Arduino, selecciona el controlador y ejecútalo.

El bucle genérico (`_control_loop`) ya se encarga de: recentrar el carro,
leer estado, recuperarse cuando el carro sale de límites, emitir la telemetría
(posición, velocidad, ángulo, velocidad angular) y registrar datos para
exportar CSV. No tienes que programar nada de eso.

---

## 4. Ejemplo mínimo

```python
"""Controlador PID de ejemplo."""
from .base import BaseController
from . import config as ctrl_config


class PIDController(BaseController):
    name = "PID"
    gain_labels = ["Kp", "Ki", "Kd"]

    def __init__(self):
        self.reload_config()
        self.reset_startup()

    def reload_config(self):
        self.K = list(ctrl_config.PID_GAINS)
        self.integral_limit = ctrl_config.PID_PARAMS["integral_limit"]
        self._integral = 0.0

    def set_gains(self, gains):
        if len(gains) != len(self.gain_labels):
            raise ValueError(f"Se necesitan exactamente {len(self.gain_labels)} ganancias")
        self.K = [float(g) for g in gains]
        ctrl_config.PID_GAINS[:] = self.K

    def reset_startup(self):
        self._integral = 0.0

    def compute_control(self, state, pos_limit_pulses, calibrated=True):
        kp, ki, kd = self.K
        error = state["pos_cm"]              # qué error usar depende de tu ley
        de = state["vel_cm_s"]
        self._integral = max(
            -self.integral_limit,
            min(self.integral_limit, self._integral + error),
        )
        u = kp * error + ki * self._integral + kd * de
        u = max(-12.0, min(12.0, u))         # clamp a ±12 V (obligatorio)
        return u
```

---

## 5. Notas importantes

- **No toques `hardware/serial.py`, `core/loops.py` ni `web/routes.py`** para agregar un
  controlador. Todo lo específico de tu controlador vive en su archivo de
  `control/` y su registro en `control/__init__.py`.
- **Ganancias del frontend:** el panel se genera dinámicamente desde
  `gain_labels`, en el mismo orden que `K`. `/gains` valida que la lista
  recibida tenga exactamente `len(gain_labels)` valores. Si un controlador no
  debe exponer ganancias, deja `gain_labels = []`.
- **Estado interno:** si tu controlador acumula memoria (integral, filtros,
  contadores), reséñala en `reset_startup()`. Se llama al iniciar y tras cada
  recuperación de límites.
- **Salidas de límites y calibración** las maneja el bucle genérico con
  `is_out_of_limits()` y `send_center()`; tu controlador solo tiene que
  comportarse de forma segura cuando `calibrated=False`.