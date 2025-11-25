import os
from supabase import create_client, Client
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # load .env if present

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper to safely call table operations
def table(name: str):
    return supabase.table(name)
