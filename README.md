# Alumni Connect

Full-stack rebuild of the "Alumni Connect" project report: a tri-portal (Student / Faculty / Alumni) platform
for mentor discovery, directory governance, mentorship requests, community events and notifications.

- **Frontend:** React 18 + Vite (`frontend/`)
- **Backend:** two cooperating services sharing one SQLite database and one JWT secret (`backend/`)
  - **Flask :5000** - Authentication, Faculty directory CRUD, Mentorship workflow
  - **FastAPI :8000** - Events + poster upload, Notification center, Search, Stats

## Module map (report section 4.3)

| Report module | Where it lives |
| --- | --- |
| Authentication & session (signup, login, JWT refresh 60 s before expiry, logout) | `backend/flask_service/app.py` `/api/auth/*`, `frontend/src/api.js`, `AuthModal.jsx` |
| Data access & storage (REST client, poster storage) | `frontend/src/api.js`, `backend/common/db.py`, `/uploads` |
| Portal hub & role navigation | `Hub.jsx` (portals unlock per account role) |
| Student discovery & outreach (multi-attribute search, duplicate-guarded requests) | `Student.jsx`, `/api/mentorship`, `/api/search` |
| Faculty directory governance (add / edit / delete) | `Faculty.jsx`, `/api/alumni` |
| Alumni profile & mentorship inbox (accept / decline) | `Alumni.jsx`, `PATCH /api/mentorship/{id}` |
| Events & notification center | `Events.jsx`, `Notifications.jsx`, FastAPI `/api/events`, `/api/notifications` |

Seed data is the report's Appendix 9: 24 alumni profiles and 5 events (events that have ended are hidden).

## Run it

Backend (Windows): double-click `start-backend.bat`, or manually:

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python flask_service\app.py
.venv\Scripts\python -m uvicorn fastapi_service.main:app --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api/auth|alumni|mentorship` to Flask and
`/api/events|notifications|search|stats` and `/uploads` to FastAPI.

## Demo accounts (password `password123`)

`student@demo.com`, `faculty@demo.com`, `alumni@demo.com` (the alumni account owns Aarav Mehta's profile).

## Rules enforced server-side

- Passwords of at least 8 characters, hashed with PBKDF2-SHA256; access and refresh JWTs (1 h / 7 d).
- Graduation year 1980-2035; skills are comma-split, trimmed and de-blanked.
- A student cannot open a second non-declined request with the same alumnus; only the addressed alumnus can
  resolve it, and only once (pending -> accepted | declined). Both sides get a notification.
- Faculty can edit/delete any record; an alumnus can only edit or create their own.
- Event end must be after start; poster must be JPEG/PNG/WebP and at most 1,536,000 bytes.

## Differences from the report

- SQLite + Flask/FastAPI replace Supabase (GoTrue, PostgREST, Storage); there is no Google OAuth / PKCE flow,
  since that needs real OAuth credentials.
- No LocalStorage offline fallback; the session is the only thing persisted client-side.
- Set `ALUMNI_JWT_SECRET` to a real secret before deploying anywhere.
