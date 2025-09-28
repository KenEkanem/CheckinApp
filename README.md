# Gather Check-in

A full-stack guest check-in application with two independent services:

- `frontend-checkin` — Vite, React, and TypeScript single-page application
- `backend-checkin` — Flask JSON API backed by PostgreSQL

## Run locally

### 1. Backend

Start the included PostgreSQL service (Docker Desktop must be running):

```powershell
docker compose up -d postgres
```

Then open a terminal:

```powershell
cd backend-checkin
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://checkin:checkin_local@localhost:5432/checkin_app"
flask --app run init-db
flask --app run run --port 5003
```

The API is available at <http://127.0.0.1:5003/api>. Copy `.env.example` values
into your environment and adjust them for your event.

### 2. Frontend

Open a second terminal:

```powershell
cd frontend-checkin
npm install
npm run dev
```

Open <http://localhost:5173>. The Vite development server proxies `/api` to the
Flask server. For separate deployments, set `VITE_API_URL` to the public API URL.

## API

### Health check

```http
GET /api/health
```

### Public event configuration

```http
GET /api/config
```

### Select an event for a check-in booth

```http
POST /api/events/select
Content-Type: application/json

{
  "eventCode": "GATHER2026"
}
```

### Check in a guest

```http
POST /api/check-ins
Content-Type: application/json

{
  "email": "guest@example.com",
  "method": "email",
  "eventCode": "GATHER2026"
}
```

For barcode check-in, send `"method": "barcode"` and include
`"uniqueId": "GTHR-2048"`.

QR codes should contain a frontend URL in this format:

```text
http://localhost:5173/checkin-by-barcode?unique_id=GTHR-2048&email=guest@example.com&event_code=GATHER2026
```

Opening that URL from a camera scanner automatically submits the protected
email-and-ID pair to the API. QR check-in is intentionally not shown as an
option on the public email form.

## Guest schema

The PostgreSQL `guests` table stores `name`, `email`, `unique_id`, `xn` (the
guest group), `time_checked_in`, and `created_at`. Email and unique ID are unique.
The backend creates the table with `flask --app run init-db`; guest data can be
imported once its source format is available.

Events are resolved from the `events` table by their unique booth code. The
generic landing page does not expose event details; the selected event's name,
schedule, and venue are returned only after a valid code is submitted. The
`init-db` command creates a starter event from `EVENT_CODE` and `EVENT_NAME` if
that code is not already managed in the database.

Import a CSV containing `first_name`, `last_name`, and `email` columns with:

```powershell
flask --app run import-guests ..\attendees_list.csv
```

The importer is repeatable: existing and repeated email addresses are skipped,
and stable invitation IDs are generated when the source has none.

## Tests and production build

```powershell
cd backend-checkin
python -m pytest

cd ..\frontend-checkin
npm run lint
npm run build
```
