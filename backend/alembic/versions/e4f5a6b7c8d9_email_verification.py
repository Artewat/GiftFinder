"""email verification: users.email_verified + email_verification_tokens

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
"""
from alembic import op
import sqlalchemy as sa

revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    # ГРАНДФАТЕРИНГ: существующие пользователи (до фичи) считаются подтверждёнными,
    # иначе строгий вход заблокирует их (в т.ч. реальный аккаунт).
    op.execute("UPDATE users SET email_verified = true")

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evt_user_id", "email_verification_tokens", ["user_id"])
    op.create_unique_constraint("uq_evt_token", "email_verification_tokens", ["token"])


def downgrade() -> None:
    op.drop_constraint("uq_evt_token", "email_verification_tokens", type_="unique")
    op.drop_index("ix_evt_user_id", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_column("users", "email_verified")
