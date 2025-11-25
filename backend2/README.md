# Shipment Matching Backend (FastAPI)

## Overview
This FastAPI project implements:
- Upload shipments (CSV/Excel) to Supabase
- Upload booking forecasts (CSV/Excel) to Supabase
- Real-time HBL matching endpoint using fuzzy matching

## Local testing (required)
1. Copy `.env.example` to `.env` and fill in:
   ```
   SUPABASE_URL=https://your-supabase-project.supabase.co
   SUPABASE_KEY=your_supabase_service_role_or_anon_key
   ```
2. (Optional) set SSL cert path:
   ```
   export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
   ```
3. Create and activate a virtualenv:
   ```
   python -m venv .venv
   source .venv/bin/activate   # mac/linux
   .venv\Scripts\activate    # windows
   ```
4. Install requirements:
   ```
   pip install -r requirements.txt
   ```
5. Run the app:
   ```
   uvicorn app.main:app --reload --port 8000
   ```
6. Open the interactive docs at: http://localhost:8000/docs

## Notes
- Do NOT commit your real SUPABASE_KEY to version control.
- The project expects Supabase tables: `shipments_raw`, `booking_forecast`. See SQL DDL in `supabase_tables.sql`.
