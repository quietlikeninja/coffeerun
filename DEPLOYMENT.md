# CoffeeRun Deployment Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [Production Deployment](#production-deployment)
- [Database Migrations](#database-migrations)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Tool       | Version  | Notes                         |
|------------|----------|-------------------------------|
| Python     | 3.12+    | Backend runtime               |
| Node.js    | 20 LTS   | Frontend build toolchain      |
| npm        | 10+      | Comes with Node.js            |
| PostgreSQL | 15+      | Production database (Railway) |
| Git        | 2.x      | Version control               |

---

## Local Development

### 1. Clone and set up the backend

```bash
cd coffeerun/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env as needed (defaults work for local dev)

# Run database migrations (creates SQLite DB + seed data)
PYTHONPATH=. alembic upgrade head

# Start the backend server
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.

- API docs (Swagger): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 2. Set up the frontend

```bash
cd coffeerun/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend is now available at `http://localhost:5173`.

### 3. Local auth flow

In development mode (no `RESEND_API_KEY` set), magic link URLs are printed to the backend console instead of emailed. The flow:

1. Open `http://localhost:5173` — you'll be redirected to `/login`
2. Enter any email address and click "Send magic link"
3. Check the backend terminal output for the magic link URL
4. Click or paste the link to complete login

The email matching `ADMIN_EMAIL` (default: `admin@example.com`) is automatically assigned the admin role on first login. All other emails get the viewer role.

### 4. Local dev defaults

| Setting              | Default Value                  |
|----------------------|--------------------------------|
| Database             | SQLite (`./coffeerun.db`)      |
| Backend URL          | `http://localhost:8000`        |
| Frontend URL         | `http://localhost:5173`        |
| Admin email          | `admin@example.com`            |
| JWT secret           | `dev-secret-change-in-production` |
| Magic link expiry    | 15 minutes                     |
| JWT expiry           | 7 days                         |
| Email delivery       | Printed to console             |

---

## Environment Variables

### Backend (Railway / Server)

| Variable                    | Required | Default                          | Description                                       |
|-----------------------------|----------|----------------------------------|---------------------------------------------------|
| `DATABASE_URL`              | Yes      | `sqlite:///./coffeerun.db`       | PostgreSQL connection string for production        |
| `ADMIN_EMAIL`               | Yes      | `admin@example.com`              | Email of the initial admin user                    |
| `JWT_SECRET`                | Yes      | `dev-secret-change-in-production`| Secret key for signing JWTs. **Must change in prod** |
| `FRONTEND_URL`              | Yes      | `http://localhost:5173`          | Frontend URL for CORS and magic link URLs          |
| `RESEND_API_KEY`            | No*      | _(empty)_                        | Resend API key for sending emails. *Required in prod |
| `SENTRY_DSN`                | No       | _(empty)_                        | Sentry DSN for backend error tracking              |
| `ENVIRONMENT`               | No       | `development`                    | `development` or `production`                      |
| `JWT_EXPIRY_DAYS`           | No       | `7`                              | JWT token lifetime in days                         |
| `MAGIC_LINK_EXPIRY_MINUTES` | No       | `15`                             | Magic link token lifetime in minutes               |
| `PORT`                      | No       | `8000`                           | Server port (auto-set by Railway)                  |

### Frontend (Vercel / Static Hosting)

| Variable          | Required | Default                   | Description                      |
|-------------------|----------|---------------------------|----------------------------------|
| `VITE_API_URL`    | Yes      | `http://localhost:8000`   | Backend API base URL             |
| `VITE_SENTRY_DSN` | No       | _(empty)_                 | Sentry DSN for frontend tracking |
| `VITE_ENVIRONMENT`| No       | _(empty)_                 | Environment tag for Sentry       |

> **Note:** Frontend env vars prefixed with `VITE_` are embedded at build time by Vite. They must be set before running `npm run build`.

---

## Production Deployment

### Architecture

```
┌──────────────┐     HTTPS      ┌──────────────┐     Internal     ┌──────────────┐
│              │ ──────────────► │              │ ───────────────► │              │
│   Vercel     │                 │   Railway    │                  │  PostgreSQL  │
│  (Frontend)  │   API calls     │  (Backend)   │   DATABASE_URL   │  (Railway)   │
│              │ ◄────────────── │              │ ◄─────────────── │              │
└──────────────┘                 └──────────────┘                  └──────────────┘
                                        │
                                        │ SMTP
                                        ▼
                                 ┌──────────────┐
                                 │   Resend     │
                                 │   (Email)    │
                                 └──────────────┘
```

### Backend — Railway

#### 1. Create a Railway project

- Sign in to [Railway](https://railway.app) and create a new project
- Add a **PostgreSQL** database service — Railway provides `DATABASE_URL` automatically
- Add a new service from your GitHub repo, pointing to the `backend/` directory

#### 2. Configure build settings

In Railway service settings:

| Setting           | Value                          |
|-------------------|--------------------------------|
| Root directory    | `backend`                      |
| Build command     | `pip install -r requirements.txt` |
| Start command     | Uses `Procfile` automatically  |

The `Procfile` runs:
```
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

#### 3. Set environment variables

In Railway service → Variables, set:

```
ADMIN_EMAIL=your-admin@yourcompany.com
JWT_SECRET=<generate a strong random string: openssl rand -hex 32>
FRONTEND_URL=https://your-app.vercel.app
RESEND_API_KEY=re_xxxxxxxxxxxx
ENVIRONMENT=production
```

`DATABASE_URL` is automatically injected by Railway when you link the PostgreSQL service.

#### 4. Run database migrations

After the first deploy, run migrations via Railway CLI or the service shell:

```bash
PYTHONPATH=. alembic upgrade head
```

Alternatively, modify the `Procfile` to run migrations before starting:

```
web: PYTHONPATH=. alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

> **Important:** The initial migration creates all tables and seeds default drink types (Flat White, Long Black, Cappuccino, etc.), sizes (Small, Regular, Large), and milk options (Full Cream, Skim, Soy, Oat, Almond).

#### 5. PostgreSQL driver note

The backend uses `psycopg2-binary` for PostgreSQL. The database URL is automatically converted from `postgresql://` to the async `postgresql+asyncpg://` format. However, `asyncpg` is not currently in the requirements. For production PostgreSQL, add `asyncpg` to `requirements.txt`:

```
asyncpg>=0.30.0
```

Or alternatively, keep using the synchronous driver by updating `database.py` to not transform the URL for PostgreSQL (the current aiosqlite setup works for SQLite dev).

### Frontend — Vercel

#### 1. Import project to Vercel

- Sign in to [Vercel](https://vercel.com) and import your GitHub repo
- Set the **Root Directory** to `frontend`

#### 2. Configure build settings

Vercel auto-detects Vite projects. Confirm these settings:

| Setting          | Value             |
|------------------|-------------------|
| Framework Preset | Vite              |
| Root Directory   | `frontend`        |
| Build Command    | `npm run build`   |
| Output Directory | `dist`            |
| Install Command  | `npm install`     |

#### 3. Set environment variables

In Vercel → Project Settings → Environment Variables:

```
VITE_API_URL=https://your-backend.up.railway.app
```

#### 4. Configure rewrites for SPA routing

Create `frontend/vercel.json`:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

This ensures client-side routing works (e.g., `/login`, `/order/123`, `/shared/abc`).

### Resend (Email Service)

1. Sign up at [resend.com](https://resend.com)
2. Verify your sending domain (or use the sandbox for testing)
3. Create an API key
4. Set `RESEND_API_KEY` in the Railway backend environment
5. Emails are sent from `CoffeeRun <noreply@coffeerun.app>` — update the from address in `backend/app/services/email.py` to match your verified domain

### Post-Deployment Checklist

- [ ] Backend starts and `/api/health` returns `{"status": "ok"}`
- [ ] Database migrations have run (`alembic upgrade head`)
- [ ] Seed data is present (drink types, sizes, milk options)
- [ ] Frontend loads and shows the login page
- [ ] `FRONTEND_URL` matches the actual Vercel deployment URL
- [ ] `VITE_API_URL` matches the actual Railway deployment URL
- [ ] CORS is working (no browser console errors on API calls)
- [ ] Magic link emails are delivered via Resend
- [ ] Admin user can log in with `ADMIN_EMAIL` and sees admin nav items
- [ ] JWT cookies are set with `httpOnly`, `Secure`, and `SameSite=Lax`
- [ ] Shared order links (`/shared/{token}`) work without authentication

---

## Database Migrations

### Running migrations

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. alembic upgrade head
```

### Creating new migrations

After modifying SQLAlchemy models:

```bash
PYTHONPATH=. alembic revision --autogenerate -m "description of change"
```

Review the generated file in `alembic/versions/` before running `upgrade head`.

### Checking migration status

```bash
PYTHONPATH=. alembic current   # Show current revision
PYTHONPATH=. alembic history   # Show migration history
```

### Rolling back

```bash
PYTHONPATH=. alembic downgrade -1   # Roll back one migration
```

---

## Troubleshooting

### CORS errors in the browser

The backend only allows requests from the URL set in `FRONTEND_URL`. Ensure this exactly matches your frontend deployment URL (including `https://`, no trailing slash).

### Magic links not arriving

- **Dev mode:** If `RESEND_API_KEY` is not set, links are printed to the backend console output (stdout)
- **Production:** Check that `RESEND_API_KEY` is set and the sending domain is verified in Resend
- Check the `FRONTEND_URL` is correct — magic links use this as the base URL

### "Not authenticated" errors

- JWT tokens are stored in httpOnly cookies. Ensure `credentials: 'include'` is set on API requests (this is the default in the API client)
- In production, cookies require HTTPS (`Secure` flag is set). Ensure both frontend and backend use HTTPS
- If the frontend and backend are on different domains, cookies may be blocked by browsers. Consider using the same root domain or adjusting `SameSite` settings

### Database connection issues

- **Local dev:** SQLite is used by default. The DB file is created at `backend/coffeerun.db`
- **Production:** Ensure `DATABASE_URL` starts with `postgresql://`. Railway provides this automatically when a PostgreSQL service is linked
- For async PostgreSQL, ensure `asyncpg` is installed

### Alembic "Can't find module 'app'"

Always run Alembic with `PYTHONPATH=.` from the `backend/` directory:

```bash
cd backend
PYTHONPATH=. alembic upgrade head
```
