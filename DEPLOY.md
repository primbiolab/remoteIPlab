# Despliegue — iplab.primbiolab.org

Arquitectura:

```
Navegador ──HTTPS/WSS──▶ Cloudflare (iplab.primbiolab.org)
                           │ (túnel cloudflared, sin puertos abiertos)
                           ▼
                    PC laboratorio (Docker)
                    ├─ app: FastAPI:8080 (backend + frontend, APP_MODE=remote)
                    │    ├─ serial fijo /dev/ttyACM0 (autoconectado)
                    │    └─ cámara fija /dev/video0 → /camera/stream (MJPEG)
                    └─ cloudflared (token)
```

El repo en GitHub queda en **modo local** por defecto (cada quien conecta
su péndulo). Solo el PC del laboratorio usa `APP_MODE=remote` vía `.env`,
así que el código es el mismo para ambos casos.

## 1. Crear el túnel en Cloudflare (una vez)

1. Cloudflare Zero Trust → Networks → Tunnels → Create → Cloudflared.
2. Nombre: `iplab`, instala el token que te da (va en `.env` como `TUNNEL_TOKEN`).
3. Public hostname:
   - Domain: `iplab.primbiolab.org`
   - Service: `http://app:8080` (nombre del servicio en docker-compose)
4. (Sin Docker: Service `http://localhost:8080`.)

## 2. PC del laboratorio (una vez)

```bash
# Docker + permisos hardware
sudo usermod -aG dialout,video $USER   # re-login después
# clonar
git clone https://github.com/primbiolab/remoteIPlab.git
cd remoteIPlab
cp .env.example .env
nano .env   # APP_MODE=remote, SERIAL_PORT, CAMERA_INDEX, TUNNEL_TOKEN

docker compose up -d --build
curl -s http://localhost:8080/api/config   # debe decir "remote"
```

Verifica `https://iplab.primbiolab.org/api/config` → `mode: remote`.

## 3. Push a GitHub = se refleja en la página (elige UNA opción)

**Opción A — Watchtower + GHCR (recomendada).**
Cada push a `main` publica `ghcr.io/primbiolab/remoteiplab:latest`
(workflow `docker-publish.yml`). En el lab:

```bash
# usar la imagen publicada en vez de build local:
# en docker-compose.yml comenta `build:` y descomenta `image: ghcr.io/...`
docker compose --profile auto-update up -d
```

Desde entonces, cada push actualiza el lab solo en ~1 min.

**Opción B — cron con git pull (simple, sin registry).**

```bash
crontab -e
# cada 2 min:
*/2 * * * * /home/lab/remoteIPlab/scripts/lab-update.sh >> /tmp/iplab-update.log 2>&1
```

**Opción C — manual:** `scripts/lab-update.sh`.

## 4. Modo local (quien clona el repo)

```bash
cd IPFramework
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python server.py   # APP_MODE no definido → local
# abrir http://localhost:8080, elegir puerto y cámara propia
```

En modo local el frontend usa tu webcam (`getUserMedia`).
En modo remoto usa el stream del laboratorio (`/camera/stream`) y el
panel serial aparece bloqueado como "Laboratorio (fijo)".

## 5. Solución de problemas

| Síntoma | Causa probable |
|---|---|
| Página carga pero dice Desconectado | `AUTO_CONNECT=false` o Arduino en otro `/dev/tty*`. Revisa `SERIAL_PORT` y `docker logs iplab-app`. |
| Cámara 503 | `CAMERA_INDEX` incorrecto. Lista con `ls /dev/video*`; prueba `CAMERA_INDEX=1` o `CAMERA_ENABLED=false` para descartar. |
| WS falla tras Cloudflare | El frontend ya usa `wss://host/ws` mismo-origen; no fijes `:8080`. Verifica que el túnel apunte a `http://app:8080`. |
| Watchtower no actualiza | La imagen debe ser pública o hacer `docker login ghcr.io` en el lab. |
