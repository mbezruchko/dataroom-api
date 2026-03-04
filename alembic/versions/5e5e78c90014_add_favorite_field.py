
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5e5e78c90014'
down_revision: Union[str, Sequence[str], None] = '2d8c6a1f59e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:


    op.add_column('files', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index(op.f('ix_files_is_favorite'), 'files', ['is_favorite'], unique=False)
def downgrade() -> None:

    op.drop_index(op.f('ix_files_is_favorite'), table_name='files')
    op.drop_column('files', 'is_favorite')