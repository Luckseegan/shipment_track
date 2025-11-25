from pydantic import BaseModel
from typing import Optional, Any

class UploadResponse(BaseModel):
    inserted: int
    updated: int

class MatchQuery(BaseModel):
    hbl_no: str
    agent: Optional[str] = None
    sheet_name: Optional[str] = None
    similarity_threshold: Optional[int] = 75
