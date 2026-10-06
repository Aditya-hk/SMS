from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Road(Base):
    __tablename__ = "roads"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    length_km: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False
    )

    width_m: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False
    )

    road_condition: Mapped[str] = mapped_column(
        Enum(
            "GOOD",
            "FAIR",
            "POOR",
            "UNDER_REPAIR",
            name="road_condition"
        ),
        nullable=False
    )

    last_maintained_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    location = relationship("Location")