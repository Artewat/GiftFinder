"""wishlist

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wishlist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(),
                  sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="RUB"),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("product_url", sa.String(1000), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_wishlist_user_id", "wishlist", ["user_id"])
    op.create_unique_constraint(
        "uq_wishlist_user_product", "wishlist", ["user_id", "product_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_wishlist_user_product", "wishlist", type_="unique")
    op.drop_index("ix_wishlist_user_id", table_name="wishlist")
    op.drop_table("wishlist")
