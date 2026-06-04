"""Daam Kemon API entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import admin, basket, categories, click, products, search, stores
from .config import settings
from .database import dispose

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(
    title="Daam Kemon API",
    description="Grocery price intelligence for Bangladesh",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(products.router)
app.include_router(basket.router)
app.include_router(stores.router)
app.include_router(click.router)
app.include_router(admin.router)
app.include_router(categories.router)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"name": "Daam Kemon API", "status": "ok"}


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def _startup() -> None:
    if settings().environment == "production":
        logging.info("Starting background scraper scheduler in production environment...")
        try:
            from scrapers.scheduler import start_scheduler_in_background
            start_scheduler_in_background()
        except Exception as e:
            logging.exception("Failed to start scheduler on API startup:")


@app.on_event("shutdown")
async def _shutdown() -> None:
    await dispose()
