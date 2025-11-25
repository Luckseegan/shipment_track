#!/bin/bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
uvicorn app.main:app --reload --port 8000
