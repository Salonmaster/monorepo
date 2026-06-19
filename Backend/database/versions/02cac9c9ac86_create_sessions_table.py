"""Create sessions table

Revision ID: 02cac9c9ac86
Revises: 29f4e46e02de
Create Date: 2025-06-14 04:57:51.714983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '02cac9c9ac86'
down_revision: Union[str, None] = '29f4e46e02de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sessions',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('verifier', sa.String(128), nullable=False),
        sa.Column('code_challenge', sa.String(128), nullable=False),
        sa.Column('code_challenge_method', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        # Store all relevant token fields individually for querying and indexing
        sa.Column('access_token', sa.Text, nullable=True),
        sa.Column('expires_in', sa.Integer, nullable=True),
        sa.Column('refresh_expires_in', sa.Integer, nullable=True),
        sa.Column('refresh_token', sa.Text, nullable=True),
        sa.Column('token_type', sa.String(32), nullable=True),
        sa.Column('not_before_policy', sa.Integer, nullable=True),
        sa.Column('session_state', sa.String(128), nullable=True),
        sa.Column('scope', sa.Text, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sessions')
    pass
