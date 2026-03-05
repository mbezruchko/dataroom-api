"""add_session_guid_to_workspaces

Revision ID: 5e8f1a2b3c4d
Revises: 2bb48ecb63cf
Create Date: 2026-03-05 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e8f1a2b3c4d'
down_revision: Union[str, Sequence[str], None] = '2bb48ecb63cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('workspaces', sa.Column('session_guid', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_workspaces_session_guid'), 'workspaces', ['session_guid'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_workspaces_session_guid'), table_name='workspaces')
    op.drop_column('workspaces', 'session_guid')
