from fastapi import APIRouter, Query, HTTPException
from app.services.matcher import get_shipment_with_realtime_match
from typing import Optional

router = APIRouter()

@router.get("/hbl")
def match_hbl(hbl: str = Query(...), agent: Optional[str] = Query(None), sheet: Optional[str] = Query(None), similarity_threshold: int = Query(75)):
    result = get_shipment_with_realtime_match(hbl, agent=agent, sheet_name=sheet, similarity_threshold=similarity_threshold)
    if not result:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return result
