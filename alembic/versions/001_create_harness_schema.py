"""Create harness schema and tables.

Revision ID: 001
Revises:
Create Date: 2026-06-27

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create harness schema
    op.execute("CREATE SCHEMA IF NOT EXISTS harness")

    # Create runs table
    op.create_table(
        'runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('thread_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('RUNNING', 'COMPLETED', 'FAILED', name='runstatus', schema='harness'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='harness'
    )
    op.create_index('ix_harness_runs_thread_id', 'runs', ['thread_id'], schema='harness')

    # Create run_steps table
    op.create_table(
        'run_steps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('node_name', sa.String(length=64), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('input_state', sa.JSON(), nullable=True),
        sa.Column('output_state', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['harness.runs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='harness'
    )
    op.create_index('ix_harness_run_steps_run_id', 'run_steps', ['run_id'], schema='harness')

    # Create run_traces table
    op.create_table(
        'run_traces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=64), nullable=False),
        sa.Column('called_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['harness.runs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='harness'
    )
    op.create_index('ix_harness_run_traces_run_id', 'run_traces', ['run_id'], schema='harness')


def downgrade() -> None:
    op.drop_index('ix_harness_run_traces_run_id', table_name='run_traces', schema='harness')
    op.drop_table('run_traces', schema='harness')
    op.drop_index('ix_harness_run_steps_run_id', table_name='run_steps', schema='harness')
    op.drop_table('run_steps', schema='harness')
    op.drop_index('ix_harness_runs_thread_id', table_name='runs', schema='harness')
    op.drop_table('runs', schema='harness')
    op.execute("DROP TYPE IF EXISTS harness.runstatus")
    op.execute("DROP SCHEMA IF EXISTS harness")
