import pandas as pd
import io
from typing import Optional

def read_uploaded_file(file_bytes: bytes, filename: str) -> Optional[pd.DataFrame]:
    try:
        if filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls"):
            return pd.read_excel(io.BytesIO(file_bytes))
        else:
            # assume CSV
            return pd.read_csv(io.BytesIO(file_bytes))
    except Exception:
        return None
