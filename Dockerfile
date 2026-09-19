FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias de sistema mínimas (serial + opencv headless necesita libglib).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 \
  && rm -rf /var/lib/apt/lists/*

COPY IPFramework/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY IPFramework ./IPFramework
COPY frontend ./frontend

ENV APP_MODE=remote \
    SERIAL_PORT=/dev/ttyACM0 \
    SERIAL_BAUD=115200 \
    AUTO_CONNECT=true \
    CAMERA_ENABLED=true \
    CAMERA_INDEX=0

EXPOSE 8080

CMD ["uvicorn", "IPFramework.app.web.main:app", "--host", "0.0.0.0", "--port", "8080"]
