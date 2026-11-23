#!/usr/bin/env bash
# =============================================================================
# MedShare-Lab: Healthcare Web Portal Runner (Topic 18 — NT2205.11.CH)
# Supports both HTTP (Port 8000) and HTTPS / TLS 1.3 (Port 8443).
# =============================================================================

set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-http}"
PORT="${2:-8000}"

echo "================================================================="
echo "  MedShare-Lab Healthcare Web Portal (Topic 18)"
echo "  Mode: $MODE | Root: $ROOT_DIR"
echo "================================================================="

# Ensure certificates exist for HTTPS
if [ "$MODE" = "https" ] || [ "$MODE" = "tls" ]; then
    PORT="${PORT:-8443}"
    mkdir -p infra/certs
    if [ ! -f infra/certs/server.crt ] || [ ! -f infra/certs/server.key ]; then
        echo "Generating TLS 1.3 self-signed certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout infra/certs/server.key -out infra/certs/server.crt \
            -subj "/CN=localhost/O=MedShare-Lab/C=VN" \
            -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
    fi

    echo "Starting Uvicorn with TLS 1.3 on https://127.0.0.1:$PORT ..."
    PYTHONPATH=src:. .venv/bin/python -m uvicorn medshare.gateway.api:app \
        --host 0.0.0.0 \
        --port "$PORT" \
        --ssl-keyfile infra/certs/server.key \
        --ssl-certfile infra/certs/server.crt \
        --ssl-version 17
else
    echo "Starting Uvicorn on http://127.0.0.1:$PORT ..."
    PYTHONPATH=src:. .venv/bin/python -m uvicorn medshare.gateway.api:app \
        --host 0.0.0.0 \
        --port "$PORT"
fi
