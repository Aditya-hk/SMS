# Smart Municipality System — Frontend + FastAPI Integration

## Run the backend

Open Terminal:

```bash
cd "SMS-25b91bd20953f031f1bbb9db67c264a7afa7f7f5"
```

Make sure your `.env` contains the same MySQL `DATABASE_URL` you were already using.

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn backend.main:app --reload --port 8001
```

Backend:
`http://localhost:8001`

## Run the frontend

Open a second Terminal:

```bash
cd frontend
python3 -m http.server 5500
```

Open:

`http://localhost:5500`

## What was integrated

- Frontend `fetch()` calls now point to FastAPI on port 8001.
- Added a frontend compatibility router at `/api/ui`.
- Login and citizen registration are connected to MySQL.
- Browser session/role handling is connected to FastAPI.
- Citizen complaints, status history, feedback and profiles are connected.
- Officer complaint/project workflows are connected.
- Contractor project/progress/maintenance/payment views are connected.
- Admin CRUD pages are connected for officers, contractors, locations, roads, pipelines, projects, payments, maintenance and alerts.
- Public transparency, road, project, contractor and complaint tracking pages are connected.
- Added public statistics and report endpoints expected by the frontend.

The existing DBMS CRUD API under `/api/...` was left in place; the frontend uses `/api/ui/...` as an adapter so the supplied frontend and backend can work together without rewriting the original database models.
