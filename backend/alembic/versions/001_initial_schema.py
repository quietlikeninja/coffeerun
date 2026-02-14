"""Initial schema with seed data

Revision ID: 001
Revises:
Create Date: 2026-02-14

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "viewer", name="userrole"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Magic Link Tokens
    op.create_table(
        "magic_link_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Drink Types
    op.create_table(
        "drink_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("display_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Sizes
    op.create_table(
        "sizes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("abbreviation", sa.String(10), nullable=False),
        sa.Column("display_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Milk Options
    op.create_table(
        "milk_options",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("display_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Colleagues
    op.create_table(
        "colleagues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("usually_in", sa.Boolean(), default=True),
        sa.Column("display_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Coffee Options
    op.create_table(
        "coffee_options",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("colleague_id", sa.Uuid(), sa.ForeignKey("colleagues.id"), nullable=False),
        sa.Column("drink_type_id", sa.Uuid(), sa.ForeignKey("drink_types.id"), nullable=False),
        sa.Column("size_id", sa.Uuid(), sa.ForeignKey("sizes.id"), nullable=False),
        sa.Column("milk_option_id", sa.Uuid(), sa.ForeignKey("milk_options.id"), nullable=True),
        sa.Column("sugar", sa.Integer(), default=0),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("is_default", sa.Boolean(), default=False),
        sa.Column("display_order", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("share_token", sa.String(64), nullable=False, unique=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Order Items
    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("colleague_id", sa.Uuid(), sa.ForeignKey("colleagues.id"), nullable=False),
        sa.Column("coffee_option_id", sa.Uuid(), sa.ForeignKey("coffee_options.id"), nullable=False),
        sa.Column("drink_type_name", sa.String(100), nullable=False),
        sa.Column("size_name", sa.String(50), nullable=False),
        sa.Column("size_abbreviation", sa.String(10), nullable=False),
        sa.Column("milk_option_name", sa.String(50), nullable=True),
        sa.Column("sugar", sa.Integer(), default=0),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed data
    drink_types = [
        ("Flat White", 1), ("Long Black", 2), ("Cappuccino", 3), ("Latte", 4),
        ("Mocha", 5), ("Espresso", 6), ("Macchiato", 7), ("Hot Chocolate", 8),
        ("Chai Latte", 9), ("Piccolo", 10),
    ]
    drink_types_table = sa.table(
        "drink_types",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        drink_types_table,
        [{"id": uuid.uuid4(), "name": name, "display_order": order, "is_active": True}
         for name, order in drink_types],
    )

    sizes = [("Small", "Sm", 1), ("Regular", "Reg", 2), ("Large", "Lrg", 3)]
    sizes_table = sa.table(
        "sizes",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("abbreviation", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        sizes_table,
        [{"id": uuid.uuid4(), "name": name, "abbreviation": abbr, "display_order": order, "is_active": True}
         for name, abbr, order in sizes],
    )

    milk_options = [("Full Cream", 1), ("Skim", 2), ("Soy", 3), ("Oat", 4), ("Almond", 5)]
    milk_options_table = sa.table(
        "milk_options",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        milk_options_table,
        [{"id": uuid.uuid4(), "name": name, "display_order": order, "is_active": True}
         for name, order in milk_options],
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("coffee_options")
    op.drop_table("colleagues")
    op.drop_table("milk_options")
    op.drop_table("sizes")
    op.drop_table("drink_types")
    op.drop_table("magic_link_tokens")
    op.drop_table("users")
