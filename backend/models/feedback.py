from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id"),
        unique=True,
        nullable=False
    )

    citizen_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    rating: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )

    comment: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    complaint = relationship("Complaint")
    citizen = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "rating BETWEEN 1 AND 5",
            name="ck_feedback_rating"
        ),
    )