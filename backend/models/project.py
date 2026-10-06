from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False
    )

    road_id: Mapped[int | None] = mapped_column(
        ForeignKey("roads.id"),
        nullable=True
    )

    pipeline_id: Mapped[int | None] = mapped_column(
        ForeignKey("pipelines.id"),
        nullable=True
    )

    officer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    contractor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    budget: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    expected_completion_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    actual_completion_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "PLANNED",
            "APPROVED",
            "IN_PROGRESS",
            "COMPLETED",
            "CANCELLED",
            name="project_status"
        ),
        nullable=False
    )

    progress_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    location = relationship("Location")
    road = relationship("Road")
    pipeline = relationship("Pipeline")