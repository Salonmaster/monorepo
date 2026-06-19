"""create code verifier table

Revision ID: 29f4e46e02de
Revises: 
Create Date: 2025-06-13 23:51:22.053415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '29f4e46e02de'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'code_verifiers',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('verifier', sa.String(128), nullable=False),
        sa.Column('code_challenge', sa.String(128), nullable=False),
        sa.Column('code_challenge_method', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('code_verifiers')
    pass
