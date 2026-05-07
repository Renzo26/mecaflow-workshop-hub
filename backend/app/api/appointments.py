import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_workshop_id
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentIn, AppointmentOut

router = APIRouter(prefix="/appointments", tags=["appointments"])


async def _get_or_404(
    appointment_id: uuid.UUID, workshop_id: uuid.UUID, db: AsyncSession
) -> Appointment:
    appointment = await db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id, Appointment.workshop_id == workshop_id
        )
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado"
        )
    return appointment


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    data: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    stmt = select(Appointment).where(Appointment.workshop_id == workshop_id)
    if data:
        stmt = stmt.where(Appointment.data == data)
    result = await db.scalars(stmt)
    return result.all()


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    appointment = Appointment(workshop_id=workshop_id, **body.model_dump())
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    appointment = await _get_or_404(appointment_id, workshop_id, db)
    for field, value in body.model_dump().items():
        setattr(appointment, field, value)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    appointment = await _get_or_404(appointment_id, workshop_id, db)
    await db.delete(appointment)
    await db.commit()
