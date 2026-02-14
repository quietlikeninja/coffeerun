import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class CoffeeOption(Base):
    __tablename__ = "coffee_options"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    colleague_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("colleagues.id"), nullable=False
    )
    drink_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("drink_types.id"), nullable=False
    )
    size_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sizes.id"), nullable=False)
    milk_option_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milk_options.id"), nullable=True
    )
    sugar: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    colleague: Mapped["Colleague"] = relationship(back_populates="coffee_options")
    drink_type: Mapped["DrinkType"] = relationship(lazy="selectin")
    size: Mapped["Size"] = relationship(lazy="selectin")
    milk_option: Mapped["MilkOption | None"] = relationship(lazy="selectin")
