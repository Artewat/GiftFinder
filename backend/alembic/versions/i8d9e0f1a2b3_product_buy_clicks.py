"""product popularity: buy_clicks counter on products (+ demo clicks on existing rows)

Revision ID: i8d9e0f1a2b3
Revises: h7c8d9e0f1a2
"""
from alembic import op
import sqlalchemy as sa

revision = "i8d9e0f1a2b3"
down_revision = "h7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("buy_clicks", sa.Integer(), nullable=False, server_default="0"),
    )
    # Демо-данные: часть товаров получает случайное число «покупок» (0–20),
    # чтобы эффект ранжирования по популярности был виден на защите.
    # Реальные клики копятся через POST /api/track/buy/{id}.
    op.execute("UPDATE products SET buy_clicks = floor(random()*21)::int WHERE random() < 0.6")


def downgrade() -> None:
    op.drop_column("products", "buy_clicks")
