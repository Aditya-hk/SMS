from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Contractor(Base):
    __tablename__ = "contractors"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True
    )

    company_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    license_no: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )