# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import shipments, bookings, match
import uvicorn

app = FastAPI(title="Shipment Matching API")

# Allow frontend local dev (adjust origins when deploying)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend origin(s) in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shipments.router, prefix="/shipments", tags=["shipments"])
app.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
app.include_router(match.router, prefix="/match", tags=["match"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Shipment Matching API"}

# --- RUN APP ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Railway sets PORT automatically
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
