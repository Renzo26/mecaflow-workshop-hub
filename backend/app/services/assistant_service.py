import os
import uuid
from collections import Counter
from datetime import date, timedelta

import anthropic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.client import Client
from app.models.conversation import Conversation, ConversationStatus
from app.models.workshop import Workshop

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


async def _build_context(db: AsyncSession, workshop_id: uuid.UUID) -> str:
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    thirty_days_ago = today - timedelta(days=30)
    week_end = today + timedelta(days=7)

    workshop = await db.scalar(select(Workshop).where(Workshop.id == workshop_id))

    total_clients = await db.scalar(
        select(func.count(Client.id)).where(Client.workshop_id == workshop_id)
    ) or 0

    clients_last_30d = await db.scalar(
        select(func.count(Client.id))
        .where(Client.workshop_id == workshop_id)
        .where(Client.created_at >= thirty_days_ago.isoformat())
    ) or 0

    all_clients = list((await db.scalars(
        select(Client).where(Client.workshop_id == workshop_id).order_by(Client.created_at.desc())
    )).all())

    appts_today = list((await db.scalars(
        select(Appointment)
        .where(Appointment.workshop_id == workshop_id)
        .where(Appointment.data == today_str)
        .order_by(Appointment.hora)
    )).all())

    appts_week = list((await db.scalars(
        select(Appointment)
        .where(Appointment.workshop_id == workshop_id)
        .where(Appointment.data > today_str)
        .where(Appointment.data <= week_end.strftime("%Y-%m-%d"))
        .order_by(Appointment.data, Appointment.hora)
    )).all())

    open_convs = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.status.in_([ConversationStatus.UNASSIGNED, ConversationStatus.HUMAN, ConversationStatus.BOT])
        )
    ) or 0

    resolved_today = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.status == ConversationStatus.RESOLVED,
            Conversation.updated_at >= today.isoformat(),
        )
    ) or 0

    # Analisa serviços mais realizados a partir do campo resumo
    resumos = [c.resumo for c in all_clients if c.resumo]
    service_counter: Counter = Counter()
    for r in resumos:
        for word in r.lower().replace(",", " ").replace(";", " ").split():
            if len(word) > 4:
                service_counter[word] += 1
    top_services = service_counter.most_common(10)

    lines = [
        f"Data de hoje: {today_str}",
        "",
        "=== OFICINA ===",
        f"Nome: {workshop.name if workshop else 'N/D'}",
    ]
    if workshop:
        if workshop.phone:
            lines.append(f"Telefone: {workshop.phone}")
        if workshop.address:
            lines.append(f"Endereço: {workshop.address}, {workshop.city or ''} - {workshop.state or ''}")
        if workshop.business_hours:
            lines.append(f"Horário: {workshop.business_hours}")
        if workshop.services:
            lines.append(f"Serviços: {workshop.services}")

    lines += [
        "",
        "=== CLIENTES ===",
        f"Total de clientes cadastrados: {total_clients}",
        f"Novos clientes nos últimos 30 dias: {clients_last_30d}",
    ]

    if top_services:
        lines.append("Serviços mais citados nos atendimentos (por resumo):")
        for svc, count in top_services:
            lines.append(f"  - {svc}: {count}x")

    if all_clients:
        lines.append(f"\nÚltimos 5 clientes cadastrados:")
        for c in all_clients[:5]:
            info = f"  - {c.nome}"
            if c.veiculo:
                info += f" | {c.veiculo}"
            if c.placa:
                info += f" | Placa: {c.placa}"
            if c.ultimo_atendimento:
                info += f" | Último atendimento: {c.ultimo_atendimento}"
            if c.resumo:
                info += f" | Serviço: {c.resumo[:80]}"
            lines.append(info)

    lines += [
        "",
        "=== AGENDAMENTOS ===",
        f"Agendamentos hoje ({today_str}): {len(appts_today)}",
    ]
    for a in appts_today:
        lines.append(f"  {a.hora} - {a.cliente} | {a.titulo}")

    if appts_week:
        lines.append(f"Próximos agendamentos (próximos 7 dias): {len(appts_week)}")
        for a in appts_week[:5]:
            lines.append(f"  {a.data} {a.hora} - {a.cliente} | {a.titulo}")

    lines += [
        "",
        "=== CONVERSAS (WhatsApp) ===",
        f"Conversas abertas/em atendimento: {open_convs}",
        f"Conversas resolvidas hoje: {resolved_today}",
    ]

    return "\n".join(lines)


async def chat(
    db: AsyncSession,
    workshop_id: uuid.UUID,
    question: str,
    history: list[dict],
) -> str:
    context = await _build_context(db, workshop_id)

    system = f"""Você é o assistente interno da MecaFlow, sistema de gestão da oficina mecânica.
Você tem acesso aos dados reais da oficina e responde perguntas com base nessas informações.
Seja direto, objetivo e use os dados fornecidos. Responda sempre em português do Brasil.

{context}"""

    messages = []
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    response = _get_client().messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=system,
        messages=messages,
    )

    return response.content[0].text
