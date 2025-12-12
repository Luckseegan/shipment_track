from rapidfuzz import fuzz
import re
from dateutil import parser
from datetime import datetime
import pandas as pd
from typing import Optional, List, Dict
from app.services.supabase_client import table as supabase_table

TABLE_SHIPMENTS = "shipments_raw"
TABLE_BOOKING = "booking_forecast"

# ---------------------------------------------------------------------
# DATE HANDLING
# ---------------------------------------------------------------------
def safe_parse_date(val) -> Optional[datetime]:
    if not val:
        return None
    try:
        return parser.parse(str(val), dayfirst=True)
    except:
        return None


# ---------------------------------------------------------------------
# VESSEL CLEANING — NEW LOGIC
# ---------------------------------------------------------------------
def clean_vessel(v: Optional[str]) -> str:
    """Keep vessel numbers, remove noise."""
    if not v:
        return ""

    s = str(v).upper()

    # Remove prefixes
    s = re.sub(r'\b(MV|M\/V|SV|MS|MT|HSC)\b', "", s)
    s = re.sub(r'\b(VOY|VOYAGE|V\.)\b', "", s)

    # Remove special characters, leave numbers intact
    s = re.sub(r'[^A-Z0-9 ]', " ", s)

    # Collapse spaces
    s = re.sub(r'\s+', " ", s).strip()

    return s


# ---------------------------------------------------------------------
# SCORE CALCULATION
# ---------------------------------------------------------------------
def vessel_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0
    return fuzz.token_set_ratio(a, b)


def calculate_weighted_score(v_score, port_match, eta_match):
    return (
        v_score * 0.60 +
        (100 if port_match else 0) * 0.20 +
        (100 if eta_match else 0) * 0.20
    )


# ---------------------------------------------------------------------
# BOOKING LOADING
# ---------------------------------------------------------------------
def load_booking_candidates(agent=None, port=None) -> List[dict]:
    q = supabase_table(TABLE_BOOKING).select("*")

    if agent:
        q = q.eq("agent", agent)
    if port:
        q = q.eq("port", port)

    res = q.execute()
    return res.data or []


# ---------------------------------------------------------------------
# CORE MATCHER
# ---------------------------------------------------------------------
def find_best_booking_match(
    bl_vessel: str,
    bl_port: str,
    bl_eta: Optional[datetime],
    agent: Optional[str],
    threshold=75
):
    candidates = load_booking_candidates(agent=agent, port=bl_port)

    if not candidates:
        candidates = load_booking_candidates(agent=agent)

    if not candidates:
        return None, 0

    best = None
    best_score = -1

    bl_clean = clean_vessel(bl_vessel)

    for b in candidates:
        bk_clean = clean_vessel(b.get("vessel") or "")
        v_score = vessel_similarity(bl_clean, bk_clean)

        # ETA comparison
        b_eta = safe_parse_date(b.get("forecast_eta"))
        eta_match = False
        if bl_eta and b_eta:
            delta = abs((bl_eta - b_eta).days)
            eta_match = delta <= 10

        # weighted score
        final_score = calculate_weighted_score(
            v_score,
            bl_port == b.get("port"),
            eta_match
        )

        if final_score > best_score:
            best_score = final_score
            best = b

    if best_score < threshold:
        return None, best_score

    return best, best_score


# ---------------------------------------------------------------------
# MAIN ENTRYPOINT
# ---------------------------------------------------------------------
def get_shipment_with_realtime_match(
    hbl_no: str,
    agent: Optional[str] = None,
    sheet_name: Optional[str] = None,
    similarity_threshold: int = 75
):
    q = supabase_table(TABLE_SHIPMENTS).select("*").eq("hbl_no", hbl_no).limit(1)

    if agent:
        q = q.eq("agent", agent)
    if sheet_name:
        q = q.eq("sheet_name", sheet_name)

    res = q.execute()
    if not res.data:
        return None

    shipment = res.data[0]
    raw = shipment.get("raw_json") or {}

    # USE SECOND VESSEL IF AVAILABLE
    bl_vessel = (
        raw.get("Second Vessel")
        or raw.get("SECOND VESSEL")
        or raw.get("First Vessel")
        or raw.get("Vessel")
        or raw.get("VESSEL")
    )

    bl_port = (
        raw.get("Port of Origin")
        or raw.get("Port")
        or raw.get("POL")
    )

    eta_raw = raw.get("ETA") or raw.get("ETD") or None
    bl_eta = safe_parse_date(eta_raw)

    best, score = find_best_booking_match(
        bl_vessel,
        bl_port,
        bl_eta,
        agent,
        similarity_threshold
    )

    return {
        "hbl_no": shipment.get("hbl_no"),
        "agent": shipment.get("agent"),
        "sheet_name": shipment.get("sheet_name"),
        "bl_vessel": bl_vessel,
        "bl_vessel_clean": clean_vessel(bl_vessel),
        "port": bl_port,
        "similarity_score": round(score, 2),
        "match_found": best is not None,
        "booking_vessel": best.get("vessel") if best else None,
        "booking_vessel_id": best.get("id") if best else None,
        "forecast_eta": best.get("forecast_eta") if best else None,
        "booking_eta": best.get("booking_eta") if best else None,
        "raw_json": raw,
        "matched_at": datetime.utcnow().isoformat()
    }
