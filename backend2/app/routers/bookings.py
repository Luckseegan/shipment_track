from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.matcher import upsert_booking_rows
from app.utils.csv_helpers import read_uploaded_file
import pandas as pd

router = APIRouter()

@router.post("/upload")
async def upload_bookings(file: UploadFile = File(...)):
    content = await file.read()
    df = read_uploaded_file(content, file.filename)
    if df is None:
        raise HTTPException(status_code=400, detail="Could not read bookings file.")

    df.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in df.columns]
    df = df.replace({pd.NA: None})

    # Try to normalize known columns: vessel, port, booking_eta, forecast_eta
    # Caller may have different column names; matcher.upsert_booking_rows will look for common names.
    inserted, updated = upsert_booking_rows(df)
    return {"status": "ok", "inserted": inserted, "updated": updated}
