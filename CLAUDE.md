# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoffeeRun is a team coffee ordering app. Users create daily orders for colleagues, share them via link, and track order history. The stack is React 19 + TypeScript (frontend on Vercel) and FastAPI + PostgreSQL (backend self-hosted on Docker, core-docker-01).

**Active work: Multi-team support.** The app is being refactored from a single-team deployment to support multiple independent teams. See `CoffeeRun_MultiTeam_Roadmap_v2.docx` in the project root for the full roadmap. Implementation is split into 5 phases.

## Current Status

**Phase 1 (Schema & Models) is COMPLETE.** The database schema has been updated:
- New tables: `teams`, `team_memberships`, `team_invites`
- New enums: `TeamRole` (owner/manager/member), `ColleagueType` (colleague/visitor)
- `users` table: `role` column removed, `display_name` added
- `colleagues`: `team_id`, `user_id`, `colleague_type` added
- `orders`, `drink_types`, `sizes`, `milk_options`: `team_id` added
- Menu seeding moved from migration to runtime (`app/services/team.py`)
- Single clean-slate Alembic migration in `alembic/versions/`

**Phase 2 (Auth & Team CRUD) is NEXT.** See `CoffeeRun_Phase2_Handoff.docx` for the detailed implementation specification. Key deliverables: updated auth middleware, team CRUD endpoints, membership management, invite system.

**The existing routers (colleagues, coffee_options, menu, orders, stats) are currently broken** because they reference the removed `User.role` and don't pass `team_id`. This is expected. Phase 2 fixes auth/middleware; Phase 3 fixes the resource routers.

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
- **Auth middleware**: `app/middleware/auth.py` provides `get_current_user` FastAPI dependency (reads JWT from cookie). **Being rewritten in Phase 2** to add `get_team_member` and `require_role()`.
- **Database**: Async SQLAlchemy 2 with `AsyncSession`; PostgreSQL in production, SQLite in dev; all PKs are UUIDs
- **Models**: Team-scoped. `Team` owns `Colleague`, `Order`, `DrinkType`, `Size`, `MilkOption` via `team_id` FK. Roles are per-team via `TeamMembership` (not on User).
- **Order items**: Snapshot drink details at creation time — immutable historical records
- **Soft deletes**: Colleagues, menu items, and teams use `is_active=False`
- **Email service**: `app/services/email.py` sends via Resend; falls back to console logging if API key is absent

### Key Relationships
- A `Team` has many `TeamMembership` rows linking to `User` with a `TeamRole`
- A `Colleague` belongs to a `Team` and optionally links to a `User` (via `user_id`)
- A `CoffeeOption` belongs to a `Colleague` and stores their drink preferences
- An `Order` belongs to a `Team` and has many `OrderItem` rows (denormalized drink snapshots)
- `MagicLinkToken` is consumed on verify and expires after `MAGIC_LINK_EXPIRY_MINUTES`

### Deployment
- **Docker/Dockge** (backend): compose entrypoint runs `alembic upgrade head` then starts gunicorn; image is built by GitHub Actions on push to `main` and pushed to GHCR (`ghcr.io/quietlikeninja/coffeerun:latest`)
- **Vercel** (frontend): `vercel.json` rewrites all routes to `index.html` for SPA routing
- Cookie is `SameSite=None; Secure` to support cross-origin requests between Vercel and the homelab domain

## Multi-Team Roadmap

The full specification is in `CoffeeRun_MultiTeam_Roadmap_v2.docx`. Phase-specific handoff documents are provided for each phase.

### Implementation Phases
1. **Phase 1 — Schema & Models** ✅ COMPLETE
2. **Phase 2 — Auth & Team CRUD** ← CURRENT. See `CoffeeRun_Phase2_Handoff.docx`
3. **Phase 3 — Scope Existing Endpoints**: Re-mount all resource routers under `/teams/{team_id}/`, team-scoped queries, visitor support.
4. **Phase 4 — Frontend: Team Management**: Team switcher, create team, team settings, invite accept, empty state.
5. **Phase 5 — Frontend: Updated Workflows**: Team-scoped dashboard, visitor creation, self-service drink editing, stats scoping.

### Phase 2 Scope (What to Change)
- `backend/app/middleware/auth.py` — Remove UserRole refs. Add `get_team_member`, `require_role()`, update `CurrentUser` (no role), add `TeamMember` dataclass
- `backend/app/services/auth.py` — Remove ADMIN_EMAIL auto-promotion, remove role from JWT, update `get_or_create_user`
- `backend/app/services/email.py` — Add `send_team_invite_email` function
- `backend/app/services/team.py` — Add invite generation and acceptance logic (or create separate `invite.py`)
- `backend/app/schemas/auth.py` — Remove role from UserResponse, add teams list, add `UserTeamMembership`
- `backend/app/schemas/team.py` — NEW: schemas for teams, memberships, invites
- `backend/app/routers/auth.py` — Update /verify (no role in JWT), /me (return team memberships)
- `backend/app/routers/teams.py` — NEW: team CRUD, membership management, invite endpoints
- `backend/app/main.py` — Register the new teams router

### Phase 2 Scope (What NOT to Change)
- `backend/app/routers/colleagues.py` — Fixed in Phase 3
- `backend/app/routers/coffee_options.py` — Fixed in Phase 3
- `backend/app/routers/menu.py` — Fixed in Phase 3
- `backend/app/routers/orders.py` — Fixed in Phase 3
- `backend/app/routers/stats.py` — Fixed in Phase 3
- `backend/app/schemas/colleague.py` — Fixed in Phase 3
- `backend/app/schemas/menu.py` — Fixed in Phase 3
- `backend/app/schemas/order.py` — Fixed in Phase 3
- All frontend code — Updated in Phases 4/5
- Database models and migrations — Complete from Phase 1

### Important: Expected Breakage After Phase 2
After Phase 2, the auth system and team management are fully functional. The old resource routers (colleagues, menu, orders, stats) are **still broken** — they don't pass `team_id` and use the old `require_admin` dependency. This is expected. Phase 3 fixes them by re-mounting under `/teams/{team_id}/`.
