import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationStatus
from app.models.label import ConversationLabel
from app.models.message import Message, MessageType
from app.schemas.webhook import WahaWebhookRequest
from app.services.sse_service import broadcaster
from app.services.waha_service import waha_service


def _normalize_chat_id(raw: str) -> str:
    return raw.replace("@s.whatsapp.net", "@c.us")


def _detect_type(payload) -> MessageType:
    if not payload.hasMedia or payload.media is None:
        return MessageType.TEXT
    mime = (payload.media.mimetype or "").lower()
    if mime.startswith("image"):
        return MessageType.IMAGE
    if mime.startswith("audio"):
        return MessageType.AUDIO
    return MessageType.DOCUMENT


class ConversationService:

    async def process_webhook(self, db: AsyncSession, body: WahaWebhookRequest) -> None:
        p = body.payload
        is_from_me = bool(p.fromMe)

        # Determina o chat_id: para mensagens do bot (fromMe), o destinatário está em "to"
        if is_from_me:
            raw_chat_id = p.to or p.from_field or ""
        else:
            raw_chat_id = p.from_field or ""

        waha_chat_id = _normalize_chat_id(raw_chat_id)
        if not waha_chat_id:
            return

        existing_msg = await db.scalar(
            select(Message).where(Message.waha_message_id == p.id)
        )
        if existing_msg:
            return

        conv = await db.scalar(
            select(Conversation)
            .where(Conversation.waha_chat_id == waha_chat_id)
            .options(selectinload(Conversation.labels))
        )

        # Se não existe conversa e é mensagem do bot, ignora (não cria conversa sem lead)
        if conv is None and is_from_me:
            return

        notify_name = ""
        if p.inner_data:
            notify_name = p.inner_data.notifyName or ""
        lead_name = notify_name or waha_chat_id.split("@")[0]
        lead_phone = waha_chat_id.split("@")[0]

        if conv is None:
            conv = Conversation(
                waha_chat_id=waha_chat_id,
                lead_name=lead_name,
                lead_phone=lead_phone,
                session="Cloudy",
                status=ConversationStatus.UNASSIGNED,
            )
            db.add(conv)
            await db.flush()

        sender_name = "Bot" if is_from_me else lead_name

        msg = Message(
            conversation_id=conv.id,
            content=p.body,
            type=_detect_type(p),
            sender_name=sender_name,
            is_from_lead=not is_from_me,
            media_url=p.media.url if p.media else None,
            waha_message_id=p.id,
        )
        db.add(msg)

        conv.last_message = p.body or ""
        conv.last_message_at = datetime.now(timezone.utc)
        if not is_from_me:
            conv.unread_count = (conv.unread_count or 0) + 1

        await db.flush()

        await broadcaster.publish("message", {
            "conversationId": str(conv.id),
            "messageId": str(msg.id),
            "content": msg.content,
            "type": msg.type.value,
            "senderName": msg.sender_name,
            "isFromLead": msg.is_from_lead,
            "createdAt": msg.created_at.isoformat() if msg.created_at else None,
        })
        await broadcaster.publish("conversation", {
            "id": str(conv.id),
            "leadName": conv.lead_name,
            "status": conv.status.value,
            "unreadCount": conv.unread_count,
            "lastMessage": conv.last_message,
        })

    async def list_conversations(
        self,
        db: AsyncSession,
        tab: str = "ALL",
        agent_id: Optional[str] = None,
    ) -> list[Conversation]:
        q = select(Conversation).options(selectinload(Conversation.labels))

        if tab == "RESOLVED":
            q = q.where(Conversation.status == ConversationStatus.RESOLVED)
        elif tab == "UNASSIGNED":
            q = q.where(Conversation.status == ConversationStatus.UNASSIGNED)
        elif tab == "MINE" and agent_id:
            q = q.where(Conversation.assigned_agent_id == agent_id)
        else:
            q = q.where(Conversation.status != ConversationStatus.RESOLVED)

        q = q.order_by(Conversation.last_message_at.desc().nullslast())
        result = await db.scalars(q)
        return list(result.all())

    async def get_conversation(self, db: AsyncSession, conv_id: uuid.UUID) -> Optional[Conversation]:
        return await db.scalar(
            select(Conversation)
            .where(Conversation.id == conv_id)
            .options(selectinload(Conversation.labels))
        )

    async def list_messages(
        self, db: AsyncSession, conv_id: uuid.UUID, page: int = 0, size: int = 50
    ) -> tuple[list[Message], int]:
        total = await db.scalar(
            select(func.count(Message.id)).where(Message.conversation_id == conv_id)
        )
        msgs = await db.scalars(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.asc())
            .offset(page * size)
            .limit(size)
        )
        return list(msgs.all()), total or 0

    async def send_message(
        self,
        db: AsyncSession,
        conv: Conversation,
        content: str,
        agent_name: str = "Agente",
    ) -> Message:
        await waha_service.send_text(conv.waha_chat_id, content)

        msg = Message(
            conversation_id=conv.id,
            content=content,
            type=MessageType.TEXT,
            sender_name=agent_name,
            is_from_lead=False,
        )
        db.add(msg)

        conv.last_message = content
        conv.last_message_at = datetime.now(timezone.utc)
        await db.flush()

        await broadcaster.publish("message", {
            "conversationId": str(conv.id),
            "messageId": str(msg.id),
            "content": msg.content,
            "type": msg.type.value,
            "senderName": msg.sender_name,
            "isFromLead": False,
            "createdAt": msg.created_at.isoformat() if msg.created_at else None,
        })
        return msg

    async def resolve(self, db: AsyncSession, conv: Conversation) -> Conversation:
        conv.status = ConversationStatus.RESOLVED
        conv.unread_count = 0
        await db.flush()
        await broadcaster.publish("conversation", {"id": str(conv.id), "status": conv.status.value})
        return conv

    async def assign(
        self, db: AsyncSession, conv: Conversation, agent_id: str, agent_name: str
    ) -> Conversation:
        conv.assigned_agent_id = agent_id
        conv.assigned_agent_name = agent_name
        conv.status = ConversationStatus.HUMAN
        await db.flush()
        await broadcaster.publish("conversation", {
            "id": str(conv.id),
            "status": conv.status.value,
            "assignedAgentId": agent_id,
            "assignedAgentName": agent_name,
        })
        return conv

    async def set_human(
        self, db: AsyncSession, conv: Conversation, redis_service
    ) -> Conversation:
        await redis_service.set_human_block(conv.waha_chat_id)
        conv.status = ConversationStatus.HUMAN
        await db.flush()
        await broadcaster.publish("conversation", {"id": str(conv.id), "status": conv.status.value})
        return conv

    async def set_bot(
        self, db: AsyncSession, conv: Conversation, redis_service
    ) -> Conversation:
        await redis_service.del_human_block(conv.waha_chat_id)
        conv.status = ConversationStatus.BOT
        await db.flush()
        await broadcaster.publish("conversation", {"id": str(conv.id), "status": conv.status.value})
        return conv

    async def add_label(
        self, db: AsyncSession, conv: Conversation, name: str, color: Optional[str]
    ) -> ConversationLabel:
        label = ConversationLabel(conversation_id=conv.id, name=name, color=color)
        db.add(label)
        await db.flush()
        return label

    async def remove_label(
        self, db: AsyncSession, conv_id: uuid.UUID, label_id: uuid.UUID
    ) -> bool:
        label = await db.scalar(
            select(ConversationLabel).where(
                ConversationLabel.id == label_id,
                ConversationLabel.conversation_id == conv_id,
            )
        )
        if not label:
            return False
        await db.delete(label)
        await db.flush()
        return True


conversation_service = ConversationService()
