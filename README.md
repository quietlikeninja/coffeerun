# CoffeeRun

A web application for managing daily office coffee orders. Each morning, select which colleagues are in the office, pick their coffee, and generate a consolidated order to take to the cafe.

## Features

- **Daily ordering** — Select who's in the office, choose their coffee, and get a clean consolidated order summary
- **Shareable orders** — Share a read-only order summary via URL (no login required)
- **Order history** — Browse past orders with paginated results
- **Analytics** — Order frequency, busiest days, top drinks, and per-colleague stats
- **Colleague management** — Maintain a team list with saved coffee preferences and defaults
- **Menu management** — Configure drink types, sizes, and milk options
- **Magic link auth** — Passwordless email login; no passwords stored

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic |
| Database | PostgreSQL (production), SQLite (development) |
| Auth | Magic links via Resend, JWT in httpOnly cookies |
| Hosting | Vercel (frontend), Docker / homelab (backend + database) |
| Monitoring | Sentry, Vercel Analytics |

## Project Structure

```
coffeerun/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, router registration
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── database.py       # Async SQLAlchemy engine and session
│   │   ├── models/           # ORM models (user, colleague, menu, order)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # API route handlers (auth, teams, colleagues, menu, orders, stats)
│   │   ├── services/         # Business logic (auth, email, order consolidation)
│   │   └── middleware/       # JWT validation
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   ├── Procfile              # Legacy Railway start command (superseded by compose entrypoint)
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.tsx            # Routes and auth layout
    │   ├── api/client.ts      # Fetch wrapper and TypeScript interfaces
    │   ├── context/           # Auth context
    │   ├── hooks/             # useAuth, useOrder
    │   ├── pages/             # Login, Dashboard, OrderView, Admin pages, Stats, TeamSettings, CreateTeam, InviteAccept
    │   └── components/        # ColleagueCard, OrderSummary, UI primitives
    ├── package.json
    ├── vite.config.ts
    └── vercel.json            # SPA routing rewrites
```

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.12+
- (Optional) PostgreSQL — SQLite is used by default in development

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — at minimum set ADMIN_EMAIL

# Run database migrations
PYTHONPATH=. alembic upgrade head

# Start the dev server
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend

npm install

# Configure environment
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
```

The app will be available at `http://localhost:5173`.

### First Login

With `RESEND_API_KEY` unset, magic link emails are printed to the backend console instead of being sent. Navigate to the app, enter the email you set as `ADMIN_EMAIL`, and copy the link from the terminal output.

## Configuration

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./coffeerun.db` | PostgreSQL URL in production, SQLite in dev |
| `JWT_SECRET` | Yes | `dev-secret-change-in-production` | Secret key for signing JWTs — **change in production** |
| `FRONTEND_URL` | Yes | `http://localhost:5173` | Used for CORS and magic link/invite URLs |
| `ADMIN_EMAIL` | No | `admin@example.com` | Email seeded as a user on first deploy (no special role) |
| `RESEND_API_KEY` | No | *(empty)* | Email delivery API key — omit to print links to console |
| `EMAIL_FROM` | No | `CoffeeRun <noreply@example.com>` | From address for outgoing emails |
| `JWT_EXPIRY_DAYS` | No | `7` | JWT token lifetime in days |
| `MAGIC_LINK_EXPIRY_MINUTES` | No | `15` | Magic link expiry in minutes |
| `INVITE_EXPIRY_DAYS` | No | `7` | Team invite token lifetime in days |
| `SENTRY_DSN` | No | *(empty)* | Backend error tracking DSN |
| `ENVIRONMENT` | No | `development` | Environment label for logging and Sentry |

### Frontend (`.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API base URL |
| `VITE_SENTRY_DSN` | No | Frontend error tracking DSN |
| `VITE_ENVIRONMENT` | No | Environment label for Sentry |

## API Overview

All routes are prefixed `/api/v1`. Role requirements: **O** = Owner, **M** = Manager, **V** = Member (any logged-in team member), **P** = Public. Team-scoped routes are prefixed `/teams/{team_id}/`.

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `POST` | `/auth/login` | P | Request magic link email |
| `POST` | `/auth/verify` | P | Verify token, receive JWT cookie |
| `POST` | `/auth/logout` | V | Clear auth cookie |
| `GET` | `/auth/me` | V | Current user info + team memberships |
| `GET` | `/teams` | V | List teams the current user belongs to |
| `POST` | `/teams` | V | Create a new team |
| `GET/PUT/DELETE` | `/teams/{team_id}` | O | Get, update, or delete team |
| `GET` | `/teams/{team_id}/members` | V | List team members |
| `PUT/DELETE` | `/teams/{team_id}/members/{user_id}` | O/M | Update role or remove member |
| `POST` | `/teams/{team_id}/invites` | O/M | Send invite email |
| `GET` | `/teams/{team_id}/invites` | O/M | List pending invites |
| `DELETE` | `/teams/{team_id}/invites/{id}` | O/M | Revoke invite |
| `POST` | `/invites/accept` | V | Accept invite by token |
| `GET` | `/teams/{team_id}/colleagues` | V | List colleagues with coffee options |
| `POST` | `/teams/{team_id}/colleagues` | O/M | Add colleague or visitor |
| `PUT` | `/teams/{team_id}/colleagues/{id}` | O/M | Update colleague |
| `DELETE` | `/teams/{team_id}/colleagues/{id}` | O/M | Soft-delete colleague |
| `POST` | `/teams/{team_id}/colleagues/{id}/coffee-options` | O/M/V* | Add coffee option |
| `PUT` | `/teams/{team_id}/coffee-options/{id}` | O/M/V* | Update coffee option |
| `DELETE` | `/teams/{team_id}/coffee-options/{id}` | O/M/V* | Delete coffee option |
| `PUT` | `/teams/{team_id}/coffee-options/{id}/set-default` | O/M/V* | Set as colleague default |
| `GET` | `/teams/{team_id}/menu/drink-types` | V | List drink types |
| `POST/PUT/DELETE` | `/teams/{team_id}/menu/drink-types` | O/M | Manage drink types |
| `GET/POST/PUT/DELETE` | `/teams/{team_id}/menu/sizes` | O/M/V | Manage cup sizes |
| `GET/POST/PUT/DELETE` | `/teams/{team_id}/menu/milk-options` | O/M/V | Manage milk options |
| `POST` | `/teams/{team_id}/orders` | V | Create order |
| `GET` | `/teams/{team_id}/orders` | V | List orders (paginated) |
| `GET` | `/teams/{team_id}/orders/{id}` | V | Order details |
| `PUT` | `/teams/{team_id}/orders/{id}` | V | Update order items |
| `GET` | `/orders/share/{token}` | P | Public shareable order |
| `GET` | `/teams/{team_id}/stats/overview` | O/M | Order counts and busiest day |
| `GET` | `/teams/{team_id}/stats/drinks` | O/M | Top drinks |
| `GET` | `/teams/{team_id}/stats/colleagues` | O/M | Per-colleague frequency |
| `GET` | `/api/health` | P | Health check |

*V* = Members can only modify their own linked colleague's coffee options.

## Deployment

The application is deployed with the frontend on Vercel and the backend self-hosted on Docker.

```
Vercel (React SPA)  ──API──►  Caddy (core-docker-01)  ──►  cr-api (Docker)  ──►  cr-db (PostgreSQL, Docker)
                                                                    │
                                                                    └──SMTP──►  Resend (Email)
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full step-by-step deployment guide.

### Key deployment notes

- Set `JWT_SECRET` to a securely generated random string
- Set `FRONTEND_URL` exactly to the Vercel deployment URL (no trailing slash) for CORS to work
- Migrations run automatically: `PYTHONPATH=. alembic upgrade head`
- The `ADMIN_EMAIL` user is promoted to admin on their first successful login

## Database

Schema uses PostgreSQL in production. Migrations are managed with Alembic.

**Tables**: `users`, `magic_link_tokens`, `teams`, `team_memberships`, `team_invites`, `colleagues`, `drink_types`, `sizes`, `milk_options`, `coffee_options`, `orders`, `order_items`

**Design notes:**
- Order items snapshot drink details at creation time so historical orders are unaffected by later menu changes
- Roles are per-team via `team_memberships` — users have no global role
- All domain data is team-scoped (every table except `users` has a `team_id`)
- Colleagues support two types: `colleague` and `visitor`. Visitors can be linked to a user account.
- Teams, colleagues, and menu items use soft deletes (`is_active = false`)
- All primary keys are UUIDs
- All timestamps are timezone-aware UTC

```bash
# Create a new migration after model changes
PYTHONPATH=. alembic revision --autogenerate -m "describe the change"

# Apply migrations
PYTHONPATH=. alembic upgrade head
```

## Current Status

The application is feature-complete at MVP level and deployed to production.

**Working:**
- Magic link authentication with per-team role-based access control (owner / manager / member)
- Multi-team support — users can create and belong to multiple teams, switch active team
- Team invites — invite by email with role assignment and optional colleague pre-linking
- Full ordering workflow (select colleagues → pick coffees → consolidated summary)
- Shareable order URLs (public, no auth required)
- Order history with pagination
- Owner/Manager CRUD for colleagues (including visitor type), coffee options, and menu items
- Members can edit their own linked colleague's drink preferences
- Analytics dashboard (order frequency, top drinks, per-colleague stats)
- Mobile-responsive UI
- Vercel + Docker/homelab deployment with PostgreSQL
- Automated test suite

**Not yet implemented:**
- Graphical charts in the analytics dashboard (currently rendered as lists)
- Sentry error tracking (configured but not activated)

## License

See [LICENSE](LICENSE).
