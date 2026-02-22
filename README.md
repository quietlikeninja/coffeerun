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
| Hosting | Vercel (frontend), Railway (backend + database) |
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
│   │   ├── routers/          # API route handlers
│   │   ├── services/         # Business logic (auth, email, order consolidation)
│   │   └── middleware/       # JWT validation
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   ├── Procfile              # Railway start command
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.tsx            # Routes and auth layout
    │   ├── api/client.ts      # Fetch wrapper and TypeScript interfaces
    │   ├── context/           # Auth context
    │   ├── hooks/             # useAuth, useOrder
    │   ├── pages/             # Login, Dashboard, OrderView, Admin pages, Stats
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
| `ADMIN_EMAIL` | Yes | `admin@example.com` | Email address seeded as the first admin |
| `JWT_SECRET` | Yes | `dev-secret-change-in-production` | Secret key for signing JWTs — **change in production** |
| `FRONTEND_URL` | Yes | `http://localhost:5173` | Used for CORS and magic link URLs |
| `RESEND_API_KEY` | No | *(empty)* | Email delivery API key — omit to print links to console |
| `JWT_EXPIRY_DAYS` | No | `7` | JWT token lifetime in days |
| `MAGIC_LINK_EXPIRY_MINUTES` | No | `15` | Magic link expiry in minutes |
| `SENTRY_DSN` | No | *(empty)* | Backend error tracking DSN |
| `ENVIRONMENT` | No | `development` | Environment label for logging and Sentry |

### Frontend (`.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API base URL |
| `VITE_SENTRY_DSN` | No | Frontend error tracking DSN |
| `VITE_ENVIRONMENT` | No | Environment label for Sentry |

## API Overview

All routes are prefixed `/api/v1`. Role requirements: **A** = Admin, **V** = Viewer (any logged-in user), **P** = Public.

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `POST` | `/auth/login` | P | Request magic link email |
| `POST` | `/auth/verify` | P | Verify token, receive JWT cookie |
| `POST` | `/auth/logout` | V | Clear auth cookie |
| `GET` | `/auth/me` | V | Current user info |
| `GET` | `/colleagues` | V | List colleagues with coffee options |
| `POST` | `/colleagues` | A | Add colleague |
| `PUT` | `/colleagues/{id}` | A | Update colleague |
| `DELETE` | `/colleagues/{id}` | A | Soft-delete colleague |
| `POST` | `/colleagues/{id}/coffee-options` | A | Add coffee option |
| `PUT` | `/coffee-options/{id}` | A | Update coffee option |
| `DELETE` | `/coffee-options/{id}` | A | Delete coffee option |
| `PUT` | `/coffee-options/{id}/set-default` | A | Set as colleague default |
| `GET` | `/menu/drink-types` | V | List drink types |
| `POST/PUT/DELETE` | `/menu/drink-types` | A | Manage drink types |
| `GET/POST/PUT/DELETE` | `/menu/sizes` | A/V | Manage cup sizes |
| `GET/POST/PUT/DELETE` | `/menu/milk-options` | A/V | Manage milk options |
| `POST` | `/orders` | V | Create order |
| `GET` | `/orders` | V | List orders (paginated) |
| `GET` | `/orders/{id}` | V | Order details |
| `PUT` | `/orders/{id}` | V | Update order items |
| `GET` | `/orders/share/{token}` | P | Public shareable order |
| `GET` | `/stats/overview` | V | Order counts and busiest day |
| `GET` | `/stats/drinks` | V | Top drinks |
| `GET` | `/stats/colleagues` | V | Per-colleague frequency |
| `GET` | `/api/health` | P | Health check |

## Deployment

The application is deployed with the frontend on Vercel and the backend on Railway.

```
Vercel (React SPA)  ──API──►  Railway (FastAPI)  ──►  Railway (PostgreSQL)
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

**Tables**: `users`, `magic_link_tokens`, `colleagues`, `drink_types`, `sizes`, `milk_options`, `coffee_options`, `orders`, `order_items`

**Design notes:**
- Order items snapshot drink details at creation time so historical orders are unaffected by later menu changes
- Colleagues and menu items use soft deletes (`is_active = false`)
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
- Magic link authentication and role-based access control
- Full ordering workflow (select colleagues → pick coffees → consolidated summary)
- Shareable order URLs
- Order history with pagination
- Admin CRUD for colleagues, coffee options, and menu items
- Analytics dashboard (order frequency, top drinks, per-colleague stats)
- Mobile-responsive UI
- Vercel + Railway deployment with PostgreSQL

**Not yet implemented:**
- Automated test suite (no tests currently exist)
- Graphical charts in the analytics dashboard (currently rendered as lists)
- Sentry error tracking (configured but not activated in `main.py`)

## License

See [LICENSE](LICENSE).
