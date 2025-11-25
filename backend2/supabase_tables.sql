-- Example DDL for Supabase (Postgres)
CREATE TABLE IF NOT EXISTS shipments_raw (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    hbl_no text,
    sheet_name text,
    agent text,
    raw_json jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS shipments_raw_hbl_sheet_agent_idx
  ON shipments_raw ((hbl_no::text), (sheet_name::text), (agent::text));

CREATE TABLE IF NOT EXISTS booking_forecast (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vessel text,
    vessel_clean text,
    port text,
    booking_eta timestamptz,
    forecast_eta timestamptz,
    raw_json jsonb,
    created_at timestamptz DEFAULT now()
);
