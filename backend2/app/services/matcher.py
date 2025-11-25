from rapidfuzz import fuzz
import re
from dateutil import parser
from datetime import datetime
import pandas as pd
from typing import Optional, Tuple, Dict, Any, List
from app.services.supabase_client import table as supabase_table

# table names (match your supabase schema)
TABLE_SHIPMENTS = "shipments_raw"
TABLE_BOOKING = "booking_forecast"

def safe_parse_date(val) -> Optional[str]:
    if val is None:
        return None
    try:
        dt = parser.parse(str(val), dayfirst=True)
        return dt.isoformat()
    except Exception:
        return None

def clean_vessel_name(v: Optional[str]) -> str:
    if not v:
        return ""
    s = str(v).upper()
    # remove common prefixes
    s = re.sub(r'\b(MV|M\/V|S\/V|MT|HSC|MS|MTS)\b', ' ', s)
    s = re.sub(r'\b(VOY|VOYAGE|V\.|VOY#|VOYAGE#)\b', ' ', s)
    # remove tokens like V.034, -034, /034, 001E
    s = re.sub(r'[\-\/\.#]?\s*\d+[A-Z]*', ' ', s)
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s.replace(" ", "")

def clean_vessel_compact(v: Optional[str]) -> str:
    if not v:
        return ""
    return re.sub(r'[^A-Z0-9]', '', str(v).upper())

def similarity_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    s1 = fuzz.token_sort_ratio(a, b)
    s2 = fuzz.partial_ratio(a, b)
    return max(s1, s2)

def row_to_json_safe(row: pd.Series) -> dict:
    out = {}
    for k, v in row.to_dict().items():
        try:
            if pd.isna(v):
                out[k] = None
            else:
                out[k] = v
        except Exception:
            out[k] = v
    return out

def upsert_booking_rows(df: pd.DataFrame) -> Tuple[int, int]:
    inserted = 0
    updated = 0
    for _, r in df.iterrows():
        vessel = r.get("vessel") or r.get("Vessel") or r.get("VESSEL") or r.get("vessel_name")
        port = r.get("port") or r.get("Port") or r.get("PORT")
        booking_eta = r.get("booking_eta") or r.get("Booking ETA") or r.get("booking_etd")
        forecast_eta = r.get("forecast_eta") or r.get("forecast") or r.get("Forecast ETA")

        vessel_clean = clean_vessel_name(vessel)
        payload = {
            "vessel": vessel,
            "vessel_clean": vessel_clean,
            "port": port,
            "booking_eta": safe_parse_date(booking_eta),
            "forecast_eta": safe_parse_date(forecast_eta),
            "raw_json": row_to_json_safe(r)
        }

        # check existing by vessel_clean + port
        q = supabase_table(TABLE_BOOKING).select("id").eq("vessel_clean", vessel_clean)
        if port:
            q = q.eq("port", port)
        res = q.limit(1).execute()
        try:
            if res.data and len(res.data) > 0:
                existing_id = res.data[0]["id"]
                supabase_table(TABLE_BOOKING).update(payload).eq("id", existing_id).execute()
                updated += 1
            else:
                supabase_table(TABLE_BOOKING).insert(payload).execute()
                inserted += 1
        except Exception:
            # continue on failures; caller will handle errors
            continue
    return inserted, updated

def load_booking_candidates(port: Optional[str] = None) -> List[dict]:
    q = supabase_table(TABLE_BOOKING).select("*")
    if port:
        q = q.eq("port", port)
    res = q.execute()
    if not res.data:
        return []
    bookings = []
    for b in res.data:
        vc = b.get("vessel_clean") or clean_vessel_name(b.get("vessel"))
        b["vessel_clean"] = vc
        bookings.append(b)
    return bookings

def find_best_booking_match(bl_vessel: str, port: Optional[str] = None, similarity_threshold: int = 75) -> Tuple[Optional[dict], float]:
    if not bl_vessel:
        return None, 0.0
    bl_vessel_clean = clean_vessel_name(bl_vessel)
    candidates = load_booking_candidates(port=port)
    if not candidates:
        candidates = load_booking_candidates(port=None)
    best = None
    best_score = -1
    for b in candidates:
        score = similarity_score(bl_vessel_clean, b.get("vessel_clean") or "")
        if score > best_score:
            best_score = score
            best = b
    if best and best_score >= similarity_threshold:
        return best, best_score
    return None, best_score

def get_shipment_with_realtime_match(hbl_no: str, agent: Optional[str]=None, sheet_name: Optional[str]=None, similarity_threshold: int=75) -> Optional[dict]:
    q = supabase_table(TABLE_SHIPMENTS).select("id,hbl_no,agent,sheet_name,raw_json").eq("hbl_no", hbl_no).limit(1)
    if agent:
        q = q.eq("agent", agent)
    if sheet_name:
        q = q.eq("sheet_name", sheet_name)
    res = q.execute()
    if not res.data:
        return None
    s = res.data[0]
    raw = s.get("raw_json") or {}

    bl_vessel = (
        raw.get("Vessel")
        or raw.get("First Vessel")
        or raw.get("Second Vessel")
        or raw.get("First Vessel Name")
        or raw.get("VESSEL")
        or raw.get("vessel")
        or raw.get("Vessel Name")
    )

    port = (
        raw.get("Port of Origin")
        or raw.get("Port")
        or raw.get("port")
        or raw.get("Port of Loading")
        or raw.get("POL")
    )

    best_match, best_score = find_best_booking_match(bl_vessel, port, similarity_threshold)

    result = {
        "hbl_no": s.get("hbl_no"),
        "agent": s.get("agent"),
        "sheet_name": s.get("sheet_name"),
        "bl_vessel": bl_vessel,
        "bl_vessel_clean": clean_vessel_name(bl_vessel),
        "port": port,
        "booking_vessel": best_match.get("vessel") if best_match else None,
        "booking_vessel_id": best_match.get("id") if best_match else None,
        "similarity_score": float(best_score),
        "forecast_eta": best_match.get("forecast_eta") if best_match else None,
        "booking_eta": best_match.get("booking_eta") if best_match else None,
        "raw_json": raw,
        "match_found": best_match is not None,
        "matched_at": datetime.utcnow().isoformat()
    }
    return result
