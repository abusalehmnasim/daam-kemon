from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str | None] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String)
    size_value: Mapped[float | None] = mapped_column(Numeric(10, 3))
    size_unit: Mapped[str | None] = mapped_column(String)
    base_unit_qty: Mapped[float | None] = mapped_column(Numeric(12, 4))
    is_loose: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    barcode: Mapped[str | None] = mapped_column(String)
    product_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    store_listings = relationship("StoreProduct", back_populates="product", lazy="selectin")
