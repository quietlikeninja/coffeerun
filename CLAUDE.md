# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoffeeRun is a team coffee ordering app. Users create daily orders for colleagues, share them via link, and track order history. The stack is React 19 + TypeScript (frontend on Vercel) and FastAPI + PostgreSQL (backend on Railway).

## Commands

### Frontend (`frontend/`)
```bash
npm run dev       # Vite dev server on port 5173
npm run build     # tsc -b && vite build
npm run lint      # ESLint
npm run preview   # Preview production build
```

### Backend (`backend/`)
```bash
# Run dev server
uvicorn app.main:app --reload --port 8000

# Database migrations
alembic upgrade head          # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Format/lint
ruff format .
ruff check .
```

### Environment Setup
- Backend: copy `backend/.env.example` to `backend/.env`; SQLite is used by default in dev (no Postgres needed)
- Frontend: set `VITE_API_URL` in `frontend/.env` (defaults to `http://localhost:8000`)
- Magic links print to console in dev when `RESEND_API_KEY` is not set

## Architecture

### Frontend
- **Auth flow**: Email → magic link → `/auth/verify?token=` → httpOnly JWT cookie → `AuthContext` loaded via `/auth/me` on mount
- **Protected routes**: `ProtectedRoute` and `AdminRoute` wrappers check `AuthContext`
- **API client**: All fetch calls go through `src/lib/api.ts` (centralized, typed)
- **Shared orders**: `/shared/{shareToken}` is a public route (no auth required)
- **Routing**: React Router v7; Vercel rewrites all paths to `index.html`

### Backend
- **Entry**: `app/main.py` registers all routers under `/api/v1` and mounts CORS middleware
- **Auth middleware**: `app/middleware/auth.py` provides `get_current_user` FastAPI dependency (reads JWT from cookie)
- **Database**: Async SQLAlchemy 2 with `AsyncSession`; PostgreSQL in production, SQLite in dev; all PKs are UUIDs
- **Order items**: Snapshot drink details at creation time — they are immutable historical records and do not reference live menu items
- **Soft deletes**: Colleagues and menu items use `is_active=False` rather than hard deletes
- **Email service**: `app/services/email.py` sends via Resend; falls back to console logging if API key is absent
- **Roles**: `UserRole` enum (`admin`/`viewer`); only admins can mutate colleagues and menu

### Key Relationships
- A `CoffeeOption` belongs to a `Colleague` and stores their default drink preferences
- An `Order` has many `OrderItem` rows; each `OrderItem` stores a snapshot of the drink at order time
- `MagicLinkToken` is consumed on verify and expires after `MAGIC_LINK_EXPIRY_MINUTES`

### Deployment
- **Railway** (backend): `Procfile` runs `alembic upgrade head` then starts Uvicorn on `$PORT`
- **Vercel** (frontend): `vercel.json` rewrites all routes to `index.html` for SPA routing
- Cookie is `SameSite=None; Secure` to support cross-origin requests between Vercel and Railway domains
