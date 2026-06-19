"""email verify via numeric code: drop unique token, add attempts

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
"""
from alembic import op
import sqlalchemy as sa

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # код подтверждения теперь 6 цифр и НЕ уникален глобально (у разных юзеров совпадают)
    op.drop_constraint("uq_evt_token", "email_verification_tokens", type_="unique")
    op.add_column(
        "email_verification_tokens",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("email_verification_tokens", "attempts")
    op.create_unique_constraint("uq_evt_token", "email_verification_tokens", ["token"])
