from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ProjectProgress(Base):
    __tablename__ = "project_progress"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False
    )

    progress_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    progress_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    updated_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    project = relationship("Project")
    updater = relationship("User")