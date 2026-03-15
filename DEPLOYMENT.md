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

| Tool       | Version  | Notes                          |
|------------|----------|--------------------------------|
| Python     | 3.12+    | Backend runtime (local dev)    |
| Node.js    | 20 LTS   | Frontend build toolchain       |
| npm        | 10+      | Comes with Node.js             |
| Docker     | 24+      | For building/running container |
| Git        | 2.x      | Version control                |

---

## Local Development

### 1. Clone and set up the backend

```bash
cd coffeerun/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

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

| Setting              | Default Value                     |
|----------------------|-----------------------------------|
| Database             | SQLite (`./coffeerun.db`)         |
| Backend URL          | `http://localhost:8000`           |
| Frontend URL         | `http://localhost:5173`           |
| Admin email          | `admin@example.com`               |
| JWT secret           | `dev-secret-change-in-production` |
| Magic link expiry    | 15 minutes                        |
| JWT expiry           | 7 days                            |
| Email delivery       | Printed to console                |

---

## Environment Variables

### Backend (Docker / Server)

| Variable                    | Required | Default                           | Description                                          |
|-----------------------------|----------|-----------------------------------|------------------------------------------------------|
| `DATABASE_URL`              | Yes      | `sqlite:///./coffeerun.db`        | PostgreSQL connection string for production          |
| `ADMIN_EMAIL`               | Yes      | `admin@example.com`               | Email of the initial admin user                      |
| `JWT_SECRET`                | Yes      | `dev-secret-change-in-production` | Secret key for signing JWTs. **Must change in prod** |
| `FRONTEND_URL`              | Yes      | `http://localhost:5173`           | Frontend URL for CORS and magic link URLs            |
| `RESEND_API_KEY`            | No*      | _(empty)_                         | Resend API key for sending emails. *Required in prod |
| `SENTRY_DSN`                | No       | _(empty)_                         | Sentry DSN for backend error tracking                |
| `ENVIRONMENT`               | No       | `development`                     | `development` or `production`                        |
| `JWT_EXPIRY_DAYS`           | No       | `7`                               | JWT token lifetime in days                           |
| `MAGIC_LINK_EXPIRY_MINUTES` | No       | `15`                              | Magic link token lifetime in minutes                 |

### Frontend (Vercel / Static Hosting)

| Variable          | Required | Default                 | Description                      |
|-------------------|----------|-------------------------|----------------------------------|
| `VITE_API_URL`    | Yes      | `http://localhost:8000` | Backend API base URL             |
| `VITE_SENTRY_DSN` | No       | _(empty)_               | Sentry DSN for frontend tracking |
| `VITE_ENVIRONMENT`| No       | _(empty)_               | Environment tag for Sentry       |

> **Note:** Frontend env vars prefixed with `VITE_` are embedded at build time by Vite. They must be set before running `npm run build`.

---

## Production Deployment

### Architecture

```
┌──────────────┐     HTTPS      ┌──────────────┐     Internal     ┌──────────────┐
│              │ ──────────────► │              │ ───────────────► │              │
│   Vercel     │                 │    Caddy     │                  │  PostgreSQL  │
│  (Frontend)  │   API calls     │  (Reverse    │   DATABASE_URL   │  (Docker)    │
│              │ ◄────────────── │   Proxy)     │ ◄─────────────── │              │
└──────────────┘                 └──────┬───────┘                  └──────────────┘
                                        │
                                        │ proxy
                                        ▼
                                 ┌──────────────┐
                                 │  cr-api      │
                                 │  (Docker,    │
                                 │   port 8002) │
                                 └──────────────┘
                                        │
                                        │ SMTP
                                        ▼
                                 ┌──────────────┐
                                 │   Resend     │
                                 │   (Email)    │
                                 └──────────────┘
```

### Backend — Docker (Dockge on core-docker-01)

#### 1. How the image is built

Pushing to `main` automatically triggers the GitHub Actions workflow (`.github/workflows/docker-publish.yml`), which builds the Docker image from `backend/` and pushes it to GHCR:

```
ghcr.io/quietlikeninja/coffeerun:latest
ghcr.io/quietlikeninja/coffeerun:sha-<commit>
```

The image runs `alembic upgrade head` before starting gunicorn, so migrations are applied automatically on every container start.

#### 2. Dockge compose stack

Create a new stack in Dockge with this compose configuration:

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: cr-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: coffeerun
      POSTGRES_USER: coffeerun
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - cr-db-data:/var/lib/postgresql/data
    networks:
      - cr-internal
    healthcheck:
      test:
        - CMD-SHELL
        - pg_isready -U coffeerun -d coffeerun
      interval: 10s
      timeout: 5s
      retries: 5
  api:
    image: ghcr.io/quietlikeninja/coffeerun:latest
    container_name: cr-api
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://coffeerun:${POSTGRES_PASSWORD}@db:5432/coffeerun
      ADMIN_EMAIL: ${ADMIN_EMAIL}
      JWT_SECRET: ${JWT_SECRET}
      FRONTEND_URL: ${FRONTEND_URL}
      RESEND_API_KEY: ${RESEND_API_KEY}
      EMAIL_FROM: ${EMAIL_FROM}
      ENVIRONMENT: "production"
      SENTRY_DSN: ${SENTRY_DSN:-}
      PYTHONPATH: /app
    ports:
      - 8002:8000
    networks:
      - cr-internal
    entrypoint: |
      sh -c "
        echo 'Running database migrations...' &&
        alembic upgrade head &&
        echo 'Starting application...' &&
        exec gunicorn app.main:app
      "

networks:
  cr-internal:
    driver: bridge

volumes:
  cr-db-data:
    driver: local
```

#### 3. Dockge `.env`

Set the following in Dockge's env editor:

```
POSTGRES_PASSWORD=<generate: openssl rand -hex 32>
ADMIN_EMAIL=your-admin@example.com
JWT_SECRET=<generate: openssl rand -hex 32>
FRONTEND_URL=https://coffeerun.qlndemo.com
RESEND_API_KEY=re_xxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
SENTRY_DSN=
```

#### 4. Deploying an update

When a new image is pushed (automatically on merge to `main`):

1. In Dockge, open the `coffeerun` stack
2. Pull the new image: click **Pull** (or run `docker compose pull` in the stack directory)
3. Restart the stack — migrations run automatically on startup

### Frontend — Vercel

#### 1. Import project to Vercel

- Sign in to [Vercel](https://vercel.com) and import your GitHub repo
- Set the **Root Directory** to `frontend`

#### 2. Configure build settings

Vercel auto-detects Vite projects. Confirm these settings:

| Setting          | Value           |
|------------------|-----------------|
| Framework Preset | Vite            |
| Root Directory   | `frontend`      |
| Build Command    | `npm run build` |
| Output Directory | `dist`          |
| Install Command  | `npm install`   |

#### 3. Set environment variables

In Vercel → Project Settings → Environment Variables:

```
VITE_API_URL=https://api-coffeerun.qlndemo.com
```

The `frontend/vercel.json` rewrite rule ensures SPA routing works for all client-side routes.

### Resend (Email Service)

1. Sign up at [resend.com](https://resend.com)
2. Verify your sending domain
3. Create an API key
4. Set `RESEND_API_KEY` in the Dockge `.env`
5. Update the from address in `backend/app/services/email.py` to match your verified domain

### Post-Deployment Checklist

- [ ] GitHub Actions build succeeded and image is on GHCR
- [ ] `cr-api` and `cr-db` containers are running in Dockge
- [ ] `/api/health` returns `{"status": "ok"}`
- [ ] Database migrations have run (check container logs on startup)
- [ ] Seed data is present (drink types, sizes, milk options)
- [ ] Frontend loads and shows the login page
- [ ] `FRONTEND_URL` matches the actual Vercel deployment URL (for CORS)
- [ ] `VITE_API_URL` matches the Caddy/tunnel URL for the backend
- [ ] Magic link emails are delivered via Resend
- [ ] Admin user can log in with `ADMIN_EMAIL` and sees admin nav items

---

## Database Migrations

### Running migrations

Migrations run automatically when the container starts. To run them manually (e.g. for a dry-run check):

```bash
# Via Docker exec into the running container
docker exec -it <cr-api-container-id> sh -c "PYTHONPATH=. alembic upgrade head"

# Or locally from the backend directory
cd backend
source venv/bin/activate
PYTHONPATH=. alembic upgrade head
```

### Creating new migrations

After modifying SQLAlchemy models:

```bash
PYTHONPATH=. alembic revision --autogenerate -m "description of change"
```

Review the generated file in `alembic/versions/` before committing.

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
- The cookie is `SameSite=None` to support cross-origin requests between Vercel and the homelab domain

### Database connection issues

- **Local dev:** SQLite is used by default. The DB file is created at `backend/coffeerun.db`
- **Production:** Ensure `DATABASE_URL` starts with `postgresql://`. The app converts it to `postgresql+asyncpg://` automatically
- If the `cr-api` container can't reach `cr-db`, confirm both services are in the same Dockge stack (they share a network automatically)

### Alembic "Can't find module 'app'"

Always run Alembic with `PYTHONPATH=.` from the `backend/` directory:

```bash
cd backend
PYTHONPATH=. alembic upgrade head
```
