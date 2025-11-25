from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.supabase_client import supabase
from app.services.matcher import row_to_json_safe
from app.services.matcher import TABLE_SHIPMENTS
from app.utils.csv_helpers import read_uploaded_file
import pandas as pd
from datetime import datetime

router = APIRouter()

@router.post("/upload")
async def upload_shipments(file: UploadFile = File(...), agent: str = Form(...)):
    content = await file.read()
    df = read_uploaded_file(content, file.filename)
    if df is None:
        raise HTTPException(status_code=400, detail="Could not parse uploaded file.")

    # Normalize columns & rows
    df.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in df.columns]
    df = df.replace({pd.NA: None})

    HBL_COL = None
    SHEET_COL = None
    # try common column names
    for cand in ["HBL NO", "HBL_NO", "hbl_no", "HBL"]:
        if cand in df.columns:
            HBL_COL = cand
            break
    for cand in ["Sheet", "SHEET", "sheet", "Sheet Name", "sheet_name"]:
        if cand in df.columns:
            SHEET_COL = cand
            break

    if not HBL_COL or not SHEET_COL:
        raise HTTPException(status_code=400, detail="Missing required columns: HBL and Sheet")

    df = df.drop_duplicates(subset=[HBL_COL])
    insert_rows = []
    for _, row in df.iterrows():
        hbl_no = row.get(HBL_COL)
        sheet_name = row.get(SHEET_COL)
        payload = {
            "hbl_no": hbl_no,
            "sheet_name": sheet_name,
            "agent": agent,
            "raw_json": row_to_json_safe(row),
            "created_at": datetime.utcnow().isoformat()
        }
        insert_rows.append(payload)

    try:
        # upsert by hbl_no, sheet_name, agent
        res = supabase.table(TABLE_SHIPMENTS).upsert(insert_rows, on_conflict="hbl_no,sheet_name,agent").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase error: {e}")

    return {"status": "ok", "uploaded": len(insert_rows)}
