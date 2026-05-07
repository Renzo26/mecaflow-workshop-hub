import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="workshop", cascade="all, delete-orphan"
    )
    clients: Mapped[list["Client"]] = relationship(  # noqa: F821
        "Client", back_populates="workshop", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(  # noqa: F821
        "Appointment", back_populates="workshop", cascade="all, delete-orphan"
    )
    labels: Mapped[list["WorkshopLabel"]] = relationship(  # noqa: F821
        "WorkshopLabel", back_populates="workshop", cascade="all, delete-orphan"
    )
