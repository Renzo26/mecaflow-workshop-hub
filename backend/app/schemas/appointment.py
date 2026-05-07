import uuid
from datetime import datetime

from pydantic import BaseModel


class AppointmentIn(BaseModel):
    data: str
    hora: str
    titulo: str
    cliente: str


class AppointmentOut(AppointmentIn):
    id: uuid.UUID
    workshop_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
