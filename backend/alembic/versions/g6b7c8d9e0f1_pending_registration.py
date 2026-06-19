"""pending registration: unverified users live outside `users` until code is confirmed

Revision ID: g6b7c8d9e0f1
Revises: f5a6b7c8d9e0
"""
from alembic import op
import sqlalchemy as sa

revision = "g6b7c8d9e0f1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Заявки на регистрацию до подтверждения почты — НЕ в `users`.
    op.create_table(
        "pending_registrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_pending_email", "pending_registrations", ["email"])
    op.create_index("ix_pending_email", "pending_registrations", ["email"])

    # Старая модель кодов больше не нужна: подтверждённые юзеры держатся в `users`,
    # неподтверждённые — в pending_registrations.
    op.drop_table("email_verification_tokens")

    # В `users` отныне все подтверждены по построению. Грандфатерим существующих
    # (включая реальные аккаунты), иначе вход строго гейтился бы старым флагом.
    op.execute("UPDATE users SET email_verified = true")


def downgrade() -> None:
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evt_user_id", "email_verification_tokens", ["user_id"])

    op.drop_index("ix_pending_email", table_name="pending_registrations")
    op.drop_constraint("uq_pending_email", "pending_registrations", type_="unique")
    op.drop_table("pending_registrations")
