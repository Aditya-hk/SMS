from sqlalchemy import CHAR, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    area_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    ward: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    pincode: Mapped[str] = mapped_column(
        CHAR(6),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "area_name",
            "ward",
            name="uq_area_ward"
        ),
    )