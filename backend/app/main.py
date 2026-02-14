from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, coffee_options, colleagues, menu, orders, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # TODO: Initialize Sentry when DSN is configured
    # if settings.sentry_dsn:
    #     import sentry_sdk
    #     sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment)
    yield
    # Shutdown


app = FastAPI(
    title="CoffeeRun API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        settings.frontend_url.replace("localhost", "127.0.0.1"),
        settings.frontend_url.replace("127.0.0.1", "localhost"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(colleagues.router, prefix="/api/v1")
app.include_router(coffee_options.router, prefix="/api/v1")
app.include_router(menu.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
