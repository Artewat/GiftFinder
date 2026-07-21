"""product discount: percent-off column on products (+ demo discounts on existing rows)

Revision ID: h7c8d9e0f1a2
Revises: g6b7c8d9e0f1
"""
from alembic import op
import sqlalchemy as sa

revision = "h7c8d9e0f1a2"
down_revision = "g6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Основная цена остаётся в products.price; скидка — в процентах.
    op.add_column(
        "products",
        sa.Column("discount_percent", sa.Integer(), nullable=False, server_default="0"),
    )
    # Демо-данные: ~70% товаров получают скидку 10–50% (шаг 5), чтобы фича
    # была видна на защите. Реальные фиды скидок не отдают — это витрина.
    op.execute(
        "UPDATE products SET discount_percent = (10 + floor(random()*9)*5)::int "
        "WHERE random() < 0.7"
    )


def downgrade() -> None:
    op.drop_column("products", "discount_percent")
