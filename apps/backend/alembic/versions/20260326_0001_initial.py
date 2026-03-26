"""initial schema

Revision ID: 20260326_0001
Revises: 
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260326_0001"
down_revision = None
branch_labels = None
depends_on = None


order_status_enum = sa.Enum(
    "draft",
    "pending_payment",
    "payment_submitted",
    "payment_review",
    "processing",
    "completed",
    "cancelled",
    "expired",
    "rejected",
    name="orderstatus",
)

order_event_enum = sa.Enum(
    "created",
    "status_changed",
    "attachment_added",
    "payment_marked",
    "quote_updated",
    "note",
    name="ordereventtype",
)

user_role_enum = sa.Enum("client", "operator", "admin", name="userrole")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_id", sa.BigInteger(), nullable=False, unique=True, index=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("lang", sa.String(length=8), nullable=True),
        sa.Column("role", user_role_enum, nullable=False, server_default="client"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "rate_pairs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("base_currency", sa.String(length=16), nullable=False),
        sa.Column("quote_currency", sa.String(length=16), nullable=False),
        sa.Column("buy_rate", sa.Numeric(20, 8), nullable=False),
        sa.Column("sell_rate", sa.Numeric(20, 8), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("direction", sa.String(length=64), nullable=False),
        sa.Column("base_currency", sa.String(length=16), nullable=False),
        sa.Column("quote_currency", sa.String(length=16), nullable=False),
        sa.Column("amount_from", sa.Numeric(20, 8), nullable=True),
        sa.Column("amount_to", sa.Numeric(20, 8), nullable=True),
        sa.Column("rate", sa.Numeric(20, 8), nullable=True),
        sa.Column("fee_amount", sa.Numeric(20, 8), nullable=True),
        sa.Column("network", sa.String(length=32), nullable=True),
        sa.Column("status", order_status_enum, nullable=False, server_default="pending_payment"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_orders_id", "orders", ["id"])
    op.create_index("ix_orders_public_id", "orders", ["public_id"])

    op.create_table(
        "order_payment_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False, unique=True),
        sa.Column("payout_card_masked", sa.String(length=32), nullable=True),
        sa.Column("payout_wallet", sa.String(length=128), nullable=True),
        sa.Column("payment_card", sa.String(length=32), nullable=True),
        sa.Column("payment_wallet", sa.String(length=128), nullable=True),
        sa.Column("tx_hash", sa.String(length=128), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "order_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("actor_type", sa.String(length=16), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", order_event_enum, nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_order_events_order_id", "order_events", ["order_id"])

    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("storage_url", sa.String(length=256), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_attachments_order_id", "attachments", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_attachments_order_id", table_name="attachments")
    op.drop_table("attachments")

    op.drop_index("ix_order_events_order_id", table_name="order_events")
    op.drop_table("order_events")

    op.drop_table("order_payment_details")

    op.drop_index("ix_orders_public_id", table_name="orders")
    op.drop_index("ix_orders_id", table_name="orders")
    op.drop_table("orders")

    op.drop_table("rate_pairs")
    op.drop_table("app_settings")
    op.drop_table("users")

    order_status_enum.drop(op.get_bind(), checkfirst=False)
    order_event_enum.drop(op.get_bind(), checkfirst=False)
    user_role_enum.drop(op.get_bind(), checkfirst=False)
