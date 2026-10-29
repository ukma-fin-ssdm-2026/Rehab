"""Shared initial schema agreed in the team's midterm specification.

AI-GENERATED START: prepared with ChatGPT; real PostgreSQL migration tested.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("role", sa.String(12), nullable=False, server_default="user"),
        sa.Column(
            "is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tracking_start_date", sa.Date(), nullable=False),
        sa.Column("best_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("role IN ('user', 'mentor', 'admin')", name="ck_users_role"),
        sa.CheckConstraint("best_streak >= 0", name="ck_users_best_streak"),
        sa.CheckConstraint("token_version >= 0", name="ck_users_token_version"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "day_records",
        sa.Column("record_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("trigger_category", sa.String(16), nullable=True),
        sa.Column(
            "drinks",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("comment", sa.String(2000), nullable=True),
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
        sa.UniqueConstraint("user_id", "date", name="uq_day_records_user_date"),
        sa.CheckConstraint(
            "status IN ('sober','relapse')", name="ck_day_records_status"
        ),
        sa.CheckConstraint(
            "trigger_category IS NULL OR trigger_category IN ('stress','holiday','social','other')",
            name="ck_day_records_trigger",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(drinks) = 'array'", name="ck_day_records_drinks_array"
        ),
        sa.CheckConstraint(
            "status = 'relapse' OR (trigger_category IS NULL AND drinks = '[]'::jsonb)",
            name="ck_day_records_sober_fields",
        ),
    )
    op.create_index("ix_day_records_date", "day_records", ["date"])
    op.create_table(
        "goals",
        sa.Column("goal_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_days", sa.Integer(), nullable=False),
        sa.Column(
            "is_achieved", sa.Boolean(), nullable=False, server_default=sa.false()
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
        sa.CheckConstraint(
            "target_days BETWEEN 1 AND 3650", name="ck_goals_target_days"
        ),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])


def downgrade():
    op.drop_table("goals")
    op.drop_table("day_records")
    op.drop_table("users")


# AI-GENERATED END
