from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class StoreProduct(Base):
    __tablename__ = "store_products"
    __table_args__ = (UniqueConstraint("store_name", "store_product_id", name="store_products_store_uniq"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    store_name: Mapped[str] = mapped_column(String, nullable=False)
    store_product_id: Mapped[str] = mapped_column(String, nullable=False)
    store_product_name: Mapped[str] = mapped_column(String, nullable=False)
    store_product_url: Mapped[str | None] = mapped_column(String)
    image_url: Mapped[str | None] = mapped_column(String)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    original_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String, default="BDT", nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    delivery_fee: Mapped[float | None] = mapped_column(Numeric(10, 2))
    match_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    match_method: Mapped[str | None] = mapped_column(String)
    is_sponsored: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    # Deferred: the raw scraped payload averages ~3x the rest of the row and is
    # kept for audit only — loading it on every search/ingest fetch was the main
    # driver of the July-2026 free-tier egress blowout (57 GB/mo from a 35 MB DB).
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False, deferred=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="store_listings", lazy="joined")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_product_id: Mapped[int] = mapped_column(ForeignKey("store_products.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
