from sqlalchemy import Enum, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Pipeline(Base):
    __tablename__ = "pipelines"

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

    pipeline_type: Mapped[str] = mapped_column(
        Enum(
            "WATER",
            "SEWER",
            "GAS",
            "STORM_DRAIN",
            name="pipeline_type"
        ),
        nullable=False
    )

    length_km: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "ACTIVE",
            "UNDER_MAINTENANCE",
            "DAMAGED",
            name="pipeline_status"
        ),
        nullable=False
    )

    installed_year: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )

    location = relationship("Location")