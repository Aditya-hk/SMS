from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Citizen(Base):
    __tablename__ = "citizens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    ward: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    user = relationship("User")