"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wind_actuals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generation_mw", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("start_time", name="uq_wind_actuals_start_time"),
    )
    op.create_index("ix_wind_actuals_start_time", "wind_actuals", ["start_time"])

    op.create_table(
        "wind_forecasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("publish_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generation_mw", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("start_time", "publish_time", name="uq_wind_forecasts_revision"),
    )
    op.create_index("ix_wind_forecasts_start_time", "wind_forecasts", ["start_time"])
    op.create_index("ix_wind_forecasts_publish_time", "wind_forecasts", ["publish_time"])
    op.create_index("ix_wind_forecasts_start_publish", "wind_forecasts", ["start_time", "publish_time"])

    op.create_table(
        "import_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("import_runs")
    op.drop_index("ix_wind_forecasts_start_publish", table_name="wind_forecasts")
    op.drop_index("ix_wind_forecasts_publish_time", table_name="wind_forecasts")
    op.drop_index("ix_wind_forecasts_start_time", table_name="wind_forecasts")
    op.drop_table("wind_forecasts")
    op.drop_index("ix_wind_actuals_start_time", table_name="wind_actuals")
    op.drop_table("wind_actuals")
