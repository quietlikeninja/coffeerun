import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    share_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", lazy="selectin"
    )
    creator: Mapped["User"] = relationship(lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    colleague_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("colleagues.id"), nullable=False
    )
    coffee_option_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("coffee_options.id"), nullable=False
    )
    drink_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    size_name: Mapped[str] = mapped_column(String(50), nullable=False)
    size_abbreviation: Mapped[str] = mapped_column(String(10), nullable=False)
    milk_option_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sugar: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="items")
    colleague: Mapped["Colleague"] = relationship(lazy="selectin")
