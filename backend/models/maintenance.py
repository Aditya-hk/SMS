from datetime import date

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Maintenance(Base):
    __tablename__ = "maintenance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"),
        nullable=True
    )

    road_id: Mapped[int | None] = mapped_column(
        ForeignKey("roads.id"),
        nullable=True
    )

    pipeline_id: Mapped[int | None] = mapped_column(
        ForeignKey("pipelines.id"),
        nullable=True
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "SCHEDULED",
            "IN_PROGRESS",
            "COMPLETED",
            name="maintenance_status"
        ),
        nullable=False
    )

    maintenance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    assigned_contractor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    assigned_officer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    project = relationship("Project")
    road = relationship("Road")
    pipeline = relationship("Pipeline")
    contractor = relationship(
        "User",
        foreign_keys=[assigned_contractor_id]
    )
    officer = relationship(
        "User",
        foreign_keys=[assigned_officer_id]
    )

    __table_args__ = (
        CheckConstraint(
            "road_id IS NOT NULL OR pipeline_id IS NOT NULL",
            name="ck_maintenance_road_or_pipeline"
        ),
    )