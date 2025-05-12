"""
Initial database migration: create tasks table.

Revision ID: 0001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
        op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False, autoincrement=True),
        sa.Column('task_id', sa.String(length=50), nullable=False, unique=True),
        sa.Column('action', sa.String(length=40), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='NOT_START'),
        sa.Column('fail_reason', sa.String(), nullable=True),
        sa.Column('submit_time', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('start_time', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('finish_time', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('search_item', sa.String(length=100), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
    )
    # indexes
    op.create_index(op.f('ix_tasks_task_id'), 'tasks', ['task_id'], unique=True)
    op.create_index(op.f('ix_tasks_action'), 'tasks', ['action'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_submit_time'), 'tasks', ['submit_time'], unique=False)
    op.create_index(op.f('ix_tasks_start_time'), 'tasks', ['start_time'], unique=False)
    op.create_index(op.f('ix_tasks_finish_time'), 'tasks', ['finish_time'], unique=False)
    op.create_index(op.f('ix_tasks_search_item'), 'tasks', ['search_item'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_tasks_search_item'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_finish_time'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_start_time'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_submit_time'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_status'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_action'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_task_id'), table_name='tasks')
    op.drop_table('tasks')