from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id"),
        nullable=False
    )

    old_status: Mapped[str | None] = mapped_column(
        Enum(
            "SUBMITTED",
            "ASSIGNED",
            "IN_PROGRESS",
            "RESOLVED",
            "CLOSED",
            "REJECTED",
            name="history_old_status"
        ),
        nullable=True
    )

    new_status: Mapped[str] = mapped_column(
        Enum(
            "SUBMITTED",
            "ASSIGNED",
            "IN_PROGRESS",
            "RESOLVED",
            "CLOSED",
            "REJECTED",
            name="history_new_status"
        ),
        nullable=False
    )

    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    complaint = relationship("Complaint")
    user = relationship("User")