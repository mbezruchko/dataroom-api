
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2d8c6a1f59e8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:


    op.create_table('folders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('is_favorite', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_folders_id'), 'folders', ['id'], unique=False)
    op.create_index(op.f('ix_folders_parent_id'), 'folders', ['parent_id'], unique=False)
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('storage_path', sa.Text(), nullable=False),
    sa.Column('size', sa.BigInteger(), nullable=True),
    sa.Column('folder_id', sa.Integer(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_folder_id'), 'files', ['folder_id'], unique=False)
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    op.create_index(op.f('ix_files_is_deleted'), 'files', ['is_deleted'], unique=False)
def downgrade() -> None:

    op.drop_index(op.f('ix_files_is_deleted'), table_name='files')
    op.drop_index(op.f('ix_files_id'), table_name='files')
    op.drop_index(op.f('ix_files_folder_id'), table_name='files')
    op.drop_table('files')
    op.drop_index(op.f('ix_folders_parent_id'), table_name='folders')
    op.drop_index(op.f('ix_folders_id'), table_name='folders')
    op.drop_table('folders')