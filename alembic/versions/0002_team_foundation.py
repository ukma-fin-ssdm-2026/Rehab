"""Shared profile, mentorship, inbox and moderation foundation.

Existing routes remain compatible; no messages or emails are sent by migration.
"""

import secrets

from alembic import op
import sqlalchemy as sa

revision = "0002_team_foundation"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL 16/18 provide gen_random_uuid without installing extensions.
    # Each character consumes independent random bits; no random()/md5 codes.
    op.execute(sa.text("""
        CREATE FUNCTION rehab_new_mentor_code() RETURNS text
        LANGUAGE sql VOLATILE AS $$
            SELECT string_agg(substr('ABCDEFGHJKLMNPQRSTUVWXYZ23456789',
                1 + get_byte(decode(replace(gen_random_uuid()::text,'-',''),'hex'),0) % 32,
                1), '') FROM generate_series(1,12)
        $$
    """))
    op.add_column("users", sa.Column("mentor_code", sa.String(12), nullable=True))
    connection = op.get_bind()
    used = set()
    for user_id in connection.execute(sa.text("SELECT user_id FROM users")).scalars():
        while True:
            code = "".join(
                secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(12)
            )
            if code not in used:
                used.add(code)
                break
        connection.execute(
            sa.text("UPDATE users SET mentor_code=:code WHERE user_id=:id"),
            {"id": user_id, "code": code},
        )
    op.alter_column(
        "users",
        "mentor_code",
        nullable=False,
        server_default=sa.text("rehab_new_mentor_code()"),
    )
    op.create_unique_constraint("uq_users_mentor_code", "users", ["mentor_code"])
    op.create_check_constraint(
        "ck_users_mentor_code_format",
        "users",
        "mentor_code ~ '^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{12}$'",
    )
    op.add_column(
        "users",
        sa.Column(
            "email_reminders_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "message_style", sa.String(12), nullable=False, server_default="formal"
        ),
    )
    op.create_check_constraint(
        "ck_users_message_style",
        "users",
        "message_style IN ('formal','humorous','zen','strict')",
    )
    # Full-account blocking is replaced by pair-specific mentorship moderation.
    op.execute("UPDATE users SET is_blocked=false WHERE is_blocked=true")
    op.add_column(
        "day_records", sa.Column("first_relapse_at", sa.DateTime(timezone=True))
    )
    op.execute(
        "UPDATE day_records SET first_relapse_at=created_at WHERE status='relapse'"
    )

    op.create_table(
        "user_avatars",
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.user_id"), primary_key=True
        ),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column(
            "mime_type", sa.String(32), nullable=False, server_default="image/jpeg"
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("mime_type='image/jpeg'", name="ck_user_avatars_mime_type"),
        sa.CheckConstraint(
            "octet_length(image_data) BETWEEN 1 AND 262144",
            name="ck_user_avatars_image_size",
        ),
        sa.CheckConstraint("version >= 1", name="ck_user_avatars_version"),
    )
    op.create_table(
        "mentorships",
        sa.Column("relationship_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "mentor_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column(
            "mentee_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column("status", sa.String(10), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("ended_by", sa.Integer(), sa.ForeignKey("users.user_id")),
        sa.Column("ended_reason", sa.String(16)),
        sa.UniqueConstraint("mentor_id", "mentee_id", name="uq_mentorships_pair"),
        sa.CheckConstraint(
            "mentor_id <> mentee_id", name="ck_mentorships_different_users"
        ),
        sa.CheckConstraint(
            "status IN ('active','ended')", name="ck_mentorships_status"
        ),
        sa.CheckConstraint(
            "(status='active' AND ended_at IS NULL AND ended_by IS NULL AND ended_reason IS NULL) OR (status='ended' AND ended_at IS NOT NULL AND ended_by IS NOT NULL AND ended_reason IS NOT NULL AND ended_reason IN ('mentor_left','mentee_left','complaint'))",
            name="ck_mentorships_ending",
        ),
    )
    op.create_index(
        "uq_mentorships_active_mentee",
        "mentorships",
        ["mentee_id"],
        unique=True,
        postgresql_where=sa.text("status='active'"),
    )
    op.create_index(
        "ix_mentorships_mentor_status", "mentorships", ["mentor_id", "status"]
    )
    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "recipient_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.user_id")),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("event_key", sa.String(100), nullable=False),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column(
            "relationship_id",
            sa.Integer(),
            sa.ForeignKey("mentorships.relationship_id"),
        ),
        sa.Column("record_id", sa.Integer(), sa.ForeignKey("day_records.record_id")),
        sa.Column("support_comment_id", sa.Integer()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "recipient_id", "event_key", name="uq_notifications_recipient_event"
        ),
        sa.CheckConstraint(
            "kind IN ('daily_reminder','relapse','support_comment')",
            name="ck_notifications_kind",
        ),
    )
    op.create_index(
        "ix_notifications_recipient_created",
        "notifications",
        ["recipient_id", "created_at", "notification_id"],
    )
    op.create_table(
        "support_comments",
        sa.Column("support_comment_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "relationship_id",
            sa.Integer(),
            sa.ForeignKey("mentorships.relationship_id"),
            nullable=False,
        ),
        sa.Column(
            "relapse_notification_id",
            sa.Integer(),
            sa.ForeignKey("notifications.notification_id"),
            nullable=False,
        ),
        sa.Column(
            "author_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column(
            "recipient_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column("text", sa.String(2000), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "relapse_notification_id",
            name="uq_support_comments_relapse_notification_id",
        ),
        sa.CheckConstraint(
            "length(btrim(text)) BETWEEN 1 AND 2000", name="ck_support_comments_text"
        ),
    )
    op.create_foreign_key(
        "fk_notifications_support_comment_id_support_comments",
        "notifications",
        "support_comments",
        ["support_comment_id"],
        ["support_comment_id"],
    )
    op.create_table(
        "complaints",
        sa.Column("complaint_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "relationship_id",
            sa.Integer(),
            sa.ForeignKey("mentorships.relationship_id"),
            nullable=False,
        ),
        sa.Column(
            "reporter_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column(
            "reported_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column("reason", sa.String(2000), nullable=False),
        sa.Column(
            "support_comment_id",
            sa.Integer(),
            sa.ForeignKey("support_comments.support_comment_id"),
        ),
        sa.Column("evidence_text", sa.String(2000)),
        sa.Column("evidence_created_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.user_id")),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected')", name="ck_complaints_status"
        ),
        sa.CheckConstraint(
            "length(btrim(reason)) BETWEEN 1 AND 2000", name="ck_complaints_reason"
        ),
        sa.CheckConstraint(
            "reporter_id <> reported_id", name="ck_complaints_different_users"
        ),
        sa.CheckConstraint(
            "(status='pending' AND reviewed_at IS NULL AND reviewed_by IS NULL) OR (status IN ('approved','rejected') AND reviewed_at IS NOT NULL AND reviewed_by IS NOT NULL)",
            name="ck_complaints_review",
        ),
    )
    op.create_index(
        "uq_complaints_pending_pair",
        "complaints",
        ["reporter_id", "reported_id"],
        unique=True,
        postgresql_where=sa.text("status='pending'"),
    )
    op.create_index(
        "ix_complaints_status_created", "complaints", ["status", "created_at"]
    )
    op.create_table(
        "email_reminder_deliveries",
        sa.Column("delivery_id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "notification_id",
            sa.Integer(),
            sa.ForeignKey("notifications.notification_id"),
            nullable=False,
        ),
        sa.Column(
            "recipient_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("provider_message_id", sa.String(254)),
        sa.Column("last_error_code", sa.String(100)),
        sa.UniqueConstraint(
            "notification_id", name="uq_email_reminder_deliveries_notification_id"
        ),
        sa.CheckConstraint(
            "status IN ('pending','sending','sent','skipped','failed','unknown')",
            name="ck_email_reminder_deliveries_status",
        ),
        sa.CheckConstraint(
            "attempts >= 0", name="ck_email_reminder_deliveries_attempts"
        ),
    )
    op.create_index(
        "ix_email_reminder_deliveries_status_date",
        "email_reminder_deliveries",
        ["status", "business_date"],
    )


def downgrade():
    op.drop_table("email_reminder_deliveries")
    op.drop_table("complaints")
    op.drop_constraint(
        "fk_notifications_support_comment_id_support_comments",
        "notifications",
        type_="foreignkey",
    )
    op.drop_table("support_comments")
    op.drop_table("notifications")
    op.drop_table("mentorships")
    op.drop_table("user_avatars")
    op.drop_column("day_records", "first_relapse_at")
    op.drop_constraint("ck_users_message_style", "users", type_="check")
    op.drop_column("users", "message_style")
    op.drop_column("users", "email_reminders_enabled")
    op.drop_constraint("ck_users_mentor_code_format", "users", type_="check")
    op.drop_constraint("uq_users_mentor_code", "users", type_="unique")
    op.drop_column("users", "mentor_code")
    op.execute("DROP FUNCTION rehab_new_mentor_code()")
