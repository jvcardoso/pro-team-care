"""Create B2B billing system for Pro Team Care

Revision ID: 017_b2b_billing_system
Revises: 016_pagbank_integration
Create Date: 2025-09-28 14:30:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "017_b2b_billing_system"
down_revision = "016_pagbank_integration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscription plans table
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("monthly_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("features", postgresql.JSONB(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("max_establishments", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create company subscriptions table
    op.create_table(
        "company_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("billing_day", sa.Integer(), nullable=False, default=1),
        sa.Column("payment_method", sa.String(20), nullable=False, default="manual"),
        sa.Column("pagbank_subscription_id", sa.String(100), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["master.companies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["master.subscription_plans.id"],
        ),
        schema="master",
    )

    # Create Pro Team Care invoices table
    op.create_table(
        "proteamcare_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("billing_period_start", sa.Date(), nullable=False),
        sa.Column("billing_period_end", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("payment_method", sa.String(20), nullable=False, default="manual"),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("pagbank_checkout_url", sa.Text(), nullable=True),
        sa.Column("pagbank_session_id", sa.String(100), nullable=True),
        sa.Column("pagbank_transaction_id", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["master.companies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["master.company_subscriptions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("invoice_number"),
        schema="master",
    )

    # Create indexes for better performance
    op.create_index(
        "idx_company_subscriptions_company_id",
        "company_subscriptions",
        ["company_id"],
        schema="master",
    )
    op.create_index(
        "idx_company_subscriptions_status",
        "company_subscriptions",
        ["status"],
        schema="master",
    )
    op.create_index(
        "idx_proteamcare_invoices_company_id",
        "proteamcare_invoices",
        ["company_id"],
        schema="master",
    )
    op.create_index(
        "idx_proteamcare_invoices_status",
        "proteamcare_invoices",
        ["status"],
        schema="master",
    )
    op.create_index(
        "idx_proteamcare_invoices_due_date",
        "proteamcare_invoices",
        ["due_date"],
        schema="master",
    )

    # Insert default subscription plans
    op.execute(
        """
        INSERT INTO master.subscription_plans (name, description, monthly_price, features, max_users, max_establishments) VALUES
        ('Básico', 'Plano ideal para clínicas pequenas', 299.00, '{"reports": "basic", "support": "email", "integrations": "limited"}', 5, 1),
        ('Premium', 'Para clínicas de médio porte', 599.00, '{"reports": "advanced", "support": "priority", "integrations": "full", "analytics": true}', 15, 3),
        ('Enterprise', 'Solução completa para grandes redes', 1200.00, '{"reports": "premium", "support": "dedicated", "integrations": "unlimited", "analytics": true, "custom_features": true}', NULL, NULL);
    """
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "idx_proteamcare_invoices_due_date", "proteamcare_invoices", schema="master"
    )
    op.drop_index(
        "idx_proteamcare_invoices_status", "proteamcare_invoices", schema="master"
    )
    op.drop_index(
        "idx_proteamcare_invoices_company_id", "proteamcare_invoices", schema="master"
    )
    op.drop_index(
        "idx_company_subscriptions_status", "company_subscriptions", schema="master"
    )
    op.drop_index(
        "idx_company_subscriptions_company_id", "company_subscriptions", schema="master"
    )

    # Drop tables
    op.drop_table("proteamcare_invoices", schema="master")
    op.drop_table("company_subscriptions", schema="master")
    op.drop_table("subscription_plans", schema="master")
