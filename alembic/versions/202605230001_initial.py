"""initial schema

Revision ID: 202605230001
Revises:
Create Date: 2026-05-23

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202605230001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


visibility_enum = sa.Enum("private", "shared", name="visibility")
board_mode_enum = sa.Enum("parallel", "sequential", "discussion", name="board_mode")
run_status_enum = sa.Enum(
    "pending", "running", "done", "failed", "cancelled", name="run_status"
)
message_role_enum = sa.Enum("director", "synthesis", name="message_role")


def upgrade() -> None:
    bind = op.get_bind()
    visibility_enum.create(bind, checkfirst=True)
    board_mode_enum.create(bind, checkfirst=True)
    run_status_enum.create(bind, checkfirst=True)
    message_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "directors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(120), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("tools", postgresql.JSONB(), nullable=True),
        sa.Column(
            "visibility",
            visibility_enum,
            nullable=False,
            server_default="private",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_directors_owner_id", "directors", ["owner_id"])

    op.create_table(
        "boards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "mode",
            board_mode_enum,
            nullable=False,
            server_default="parallel",
        ),
        sa.Column("rounds", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "synthesis_director_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("directors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "visibility",
            visibility_enum,
            nullable=False,
            server_default="private",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_boards_owner_id", "boards", ["owner_id"])

    op.create_table(
        "board_directors",
        sa.Column(
            "board_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("boards.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "director_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("directors.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt_override", sa.Text(), nullable=True),
    )

    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column(
            "board_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("boards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            run_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_runs_owner_id", "runs", ["owner_id"])
    op.create_index("ix_runs_board_id", "runs", ["board_id"])

    op.create_table(
        "director_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "director_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("directors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("round", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "role",
            message_role_enum,
            nullable=False,
            server_default="director",
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "completion_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_director_messages_run_id", "director_messages", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_director_messages_run_id", table_name="director_messages")
    op.drop_table("director_messages")
    op.drop_index("ix_runs_board_id", table_name="runs")
    op.drop_index("ix_runs_owner_id", table_name="runs")
    op.drop_table("runs")
    op.drop_table("board_directors")
    op.drop_index("ix_boards_owner_id", table_name="boards")
    op.drop_table("boards")
    op.drop_index("ix_directors_owner_id", table_name="directors")
    op.drop_table("directors")

    bind = op.get_bind()
    message_role_enum.drop(bind, checkfirst=True)
    run_status_enum.drop(bind, checkfirst=True)
    board_mode_enum.drop(bind, checkfirst=True)
    visibility_enum.drop(bind, checkfirst=True)
