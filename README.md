# PRIMBIO - Inverted Pendulum Control System

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Status](https://img.shields.io/badge/status-Active-success)

Sistema integrado de control en tiempo real para un péndulo invertido sobre carro, desarrollado en el grupo de investigación **PRIMBIO** de la Universidad Nacional de Colombia.

---

## Descripción

PRIMBIO es una plataforma completa para el control de un péndulo invertido que combina:

- **Backend Python** (FastAPI + WebSocket) para comunicación serial con Arduino
- **Frontend Web** (HTML/CSS/JS) con visualización en tiempo real
- **Firmware Arduino** para lectura de encoders y control del motor

El sistema permite controlar el péndulo mediante el controlador **LQR** (Linear Quadratic Regulator) con capacidad de **Swing-up** para balancear el péndulo desde una posición colgante.

---

## Características

| Característica | Descripción |
|----------------|-------------|
| **Control LQR** | Regulador cuadrático lineal con ganancias ajustables en tiempo real |
| **Swing-up** | Algoritmo para balancear el péndulo desde posición colgante |
| **Visualización en tiempo real** | Canvas animado del péndulo y gráficas de telemetría |
| **Calibración de riel** | Configuración de límites izquierdo/derecho y centro automático |
| **Control manual** | Movimiento manual del carro con voltaje configurable |
| **Cámara USB** | Integración de cámara para monitoreo visual |
| **Exportación CSV** | Descarga de datos de telemetría para análisis offline |
| **WebSocket** | Comunicación bidireccional de baja latencia |

---

## Estructura del Proyecto

```
PRIMBIO/
├── frontend/                    # Interfaz web
│   ├── index.html              # Página principal
│   ├── styles.css              # Estilos (tema oscuro Catppuccin)
│   ├── app.js                  # Lógica principal de la aplicación
│   ├── pendulum-sim.js         # Visualización Canvas del péndulo
│   ├── charts.js               # Gráficas de telemetría en tiempo real
│   └── src/icon.png            # Ícono de la aplicación
│
├── IPFramework/                 # Backend Python
│   ├── app/
│   │   ├── settings.py         # Rutas del servidor y constantes de hardware
│   │   ├── core/               # Núcleo de ejecución
│   │   │   ├── states.py       # Estado global, broadcast WS y chequeos
│   │   │   └── loops.py        # Bucle de monitoreo y de control genérico
│   │   ├── hardware/
│   │   │   └── serial.py       # Comunicación serial con el Arduino
│   │   ├── web/
│   │   │   ├── main.py         # Aplicación FastAPI
│   │   │   └── routes.py       # Endpoints REST y WebSocket
│   │   └── control/            # Controladores
│   │       ├── __init__.py     # Dispatcher: selección de controlador
│   │       ├── base.py         # Interfaz BaseController
│   │       ├── config.py       # Configuración de los controladores
│   │       ├── lqr.py          # Controlador LQR + Swing-up
│   │       └── AGREGAR_CONTROLADOR.md
│   ├── ino/
│   │   └── inverted_pendulum_arduino.ino  # Firmware Arduino
│   ├── server.py               # Punto de entrada del servidor
│   └── requirements.txt        # Dependencias Python
│
├── LICENSE                     # GPL-3.0
└── README.md
```

---

## Requisitos

### Hardware
- Arduino (Mega/Uno) con flashed `inverted_pendulum_arduino.ino`
- Motor DC con driver (L298N o similar)
- 2 encoders: uno para posición del carro, otro para ángulo del péndulo
- Riel y carro mecánico
- Conexión USB para comunicación serial

### Software
- Python 3.8+
- Navegador web moderno (Chrome/Firefox)

---

## Instalación

### 1. Clonar el repositorio

```bash
https://github.com/primbiolab/remoteIPlab.git
cd remoteIPlab
```

### 2. Configurar entorno Python

```bash
cd IPFramework
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 3. Flashear Arduino

Abrir `IPFramework/ino/inverted_pendulum_arduino.ino` en Arduino IDE y subir al microcontrolador.

### 4. Ejecutar el servidor

```bash
python server.py
```

### 5. Abrir la interfaz

Acceder a [http://localhost:8080](http://localhost:8080) en el navegador.

---

## Uso

### Conexión Serial

1. Conectar el Arduino por USB
2. Seleccionar el puerto serie (por defecto `/dev/ttyACM0`)
3. Hacer clic en **Conectar**

### Monitoreo

- Clic en **Monitorear** para ver datos en tiempo real sin activar el motor
- Se muestran: posición, ángulo, velocidades y señal de control

### Control

1. Seleccionar el controlador: **LQR + Swing-up**
2. Clic en **Ejecutar** para activar el control
3. Ajustar ganancias (Kθ, Kω, Kp, Kd) en tiempo real

### Calibración del Riel

1. Mover el carro al extremo izquierdo → clic **Extremo Izquierdo**
2. Mover al extremo derecho → clic **Extremo Derecho**
3. Clic **Calcular Centro**
4. Clic **Mover a Centro** para verificar
5. Clic **Aplicar Calibración**

---

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del sistema |
| `GET` | `/ports` | Puertos serie disponibles |
| `POST` | `/connect` | Conectar serial |
| `POST` | `/disconnect` | Desconectar serial |
| `POST` | `/start` | Iniciar control |
| `POST` | `/stop` | Detener control |
| `POST` | `/monitor/start` | Iniciar monitoreo |
| `POST` | `/monitor/stop` | Detener monitoreo |
| `POST` | `/controller` | Cambiar controlador |
| `POST` | `/gains` | Actualizar ganancias LQR |
| `POST` | `/calibrate/*` | Operaciones de calibración |
| `POST` | `/move/start` | Movimiento manual |
| `POST` | `/move/stop` | Detener movimiento |
| `GET` | `/data/export` | Exportar CSV |
| `WS` | `/ws` | WebSocket de telemetría |

---

## Protocolo Serial Arduino

| Comando | Respuesta | Descripción |
|---------|-----------|-------------|
| `R` | `pos,angle,speed,angSpeed` | Leer datos |
| `Z` | `Z_OK` | Reset completo |
| `C` | datos | Modo calibración |
| `E` | `E_OK,pulses` | Set límite izquierdo |
| `D` | `D_OK,pulses` | Set límite derecho |
| `O` | `O_OK,center,left,right` | Calcular centro |
| `H` | `H_OK` | Mover a centro |
| `1<pos>` | - | Control posición |
| `0<voltage>` | - | Control voltaje |

---

## Licencia

Este proyecto está licenciado bajo la [GNU General Public License v3.0](LICENSE).

---

## Créditos

Desarrollado en el **Hotbed PRIMBIO** — Universidad Nacional de Colombia, Sede de La Paz.
