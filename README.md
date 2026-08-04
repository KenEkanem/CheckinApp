# WeGatherEvents

A guest check-in client for the WeGatherEvents management platform, with two independent services:

- `frontend-checkin` — Vite, React, and TypeScript single-page application
- `backend-checkin` — Flask JSON gateway to the management API

## Run locally

### 1. Backend

Start the WeGatherEvents management backend on port `5004` first. Configure the
same `CHECKIN_SERVICE_TOKEN` in both applications, then open a terminal:

```powershell
cd backend-checkin
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:MANAGEMENT_API_URL = "http://127.0.0.1:5004/api"
$env:CHECKIN_SERVICE_TOKEN = "replace-with-a-long-random-secret"
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

## Data ownership

The management service owns events, guests, event memberships, and check-in
timestamps. This backend has no data-store credentials or persistence models. It
validates public requests and forwards them to the authenticated management API.
Guest imports and event administration are performed in the management portal.

## Tests and production build

```powershell
cd backend-checkin
python -m pytest

cd ..\frontend-checkin
npm run lint
npm run build
```
