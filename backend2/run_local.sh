#!/bin/bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
uvicorn app.main:app --host 0.0.0.0 --port $PORT
