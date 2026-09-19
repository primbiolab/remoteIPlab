#!/usr/bin/env bash
# Actualización manual del PC del laboratorio: git pull + rebuild.
# Para auto-actualizar en cada push, ver deploy/README.md (opciones A/B/C).
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --ff-only
docker compose up -d --build
docker compose ps
