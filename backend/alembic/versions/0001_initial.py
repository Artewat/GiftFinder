"""initial schema: categories, products

Revision ID: 0001
Revises:
Create Date: 2026-06-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column("local_image_path", sa.String(length=1024), nullable=True),
        sa.Column("product_url", sa.String(length=1024), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("scraped_at", sa.DateTime(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("products")
    op.drop_table("categories")
