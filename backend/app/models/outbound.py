from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class OutboundClick(Base):
    __tablename__ = "outbound_clicks"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_product_id: Mapped[int | None] = mapped_column(ForeignKey("store_products.id", ondelete="SET NULL"))
    store_name: Mapped[str] = mapped_column(String, nullable=False)
    session_id: Mapped[str | None] = mapped_column(String)
    referrer: Mapped[str | None] = mapped_column(String)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
