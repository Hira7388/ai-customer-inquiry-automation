"""Create customers and inquiries.

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(100), nullable=False),
    )
    op.create_table(
        "inquiries",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id", sa.Uuid(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), server_default=sa.text("'RECEIVED'"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_inquiries_idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("inquiries")
    op.drop_table("customers")
