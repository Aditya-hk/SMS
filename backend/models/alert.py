from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    severity: Mapped[str] = mapped_column(
        Enum(
            "INFO",
            "WARNING",
            "CRITICAL",
            name="alert_severity"
        ),
        nullable=False
    )

    audience: Mapped[str] = mapped_column(
        Enum(
            "PUBLIC",
            "OFFICER",
            name="alert_audience"
        ),
        nullable=False
    )

    expires_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    creator = relationship("User")