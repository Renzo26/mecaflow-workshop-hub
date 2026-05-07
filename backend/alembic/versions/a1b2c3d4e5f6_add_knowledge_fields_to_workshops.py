"""add_knowledge_fields_to_workshops

Revision ID: a1b2c3d4e5f6
Revises: 91973c2ec9b2
Branch Labels: None
Depends On: None

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '91973c2ec9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('workshops', sa.Column('address', sa.String(length=300), nullable=True))
    op.add_column('workshops', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('workshops', sa.Column('state', sa.String(length=2), nullable=True))
    op.add_column('workshops', sa.Column('cep', sa.String(length=10), nullable=True))
    op.add_column('workshops', sa.Column('business_hours', sa.String(length=300), nullable=True))
    op.add_column('workshops', sa.Column('services', sa.String(length=2000), nullable=True))
    op.add_column('workshops', sa.Column('bot_info', sa.String(length=2000), nullable=True))


def downgrade() -> None:
    op.drop_column('workshops', 'bot_info')
    op.drop_column('workshops', 'services')
    op.drop_column('workshops', 'business_hours')
    op.drop_column('workshops', 'cep')
    op.drop_column('workshops', 'state')
    op.drop_column('workshops', 'city')
    op.drop_column('workshops', 'address')
