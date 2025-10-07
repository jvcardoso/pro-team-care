"""Add PagBank integration fields and tables

Revision ID: 016_pagbank_integration
Revises: 015_contract_billing_system
Create Date: 2025-01-22 16:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "016_pagbank_integration"
down_revision = "015_contract_billing_system"
branch_labels = None
depends_on = None


def upgrade():
    """Add PagBank integration fields and tables."""

    # Add PagBank fields to contract_billing_schedules
    op.add_column(
        "contract_billing_schedules",
        sa.Column("billing_method", sa.String(length=20), default="manual"),
        schema="master",
    )
    op.add_column(
        "contract_billing_schedules",
        sa.Column("pagbank_subscription_id", sa.String(length=100)),
        schema="master",
    )
    op.add_column(
        "contract_billing_schedules",
        sa.Column("pagbank_customer_id", sa.String(length=100)),
        schema="master",
    )
    op.add_column(
        "contract_billing_schedules",
        sa.Column("auto_fallback_enabled", sa.Boolean(), default=True),
        schema="master",
    )
    op.add_column(
        "contract_billing_schedules",
        sa.Column("last_attempt_date", sa.Date()),
        schema="master",
    )
    op.add_column(
        "contract_billing_schedules",
        sa.Column("attempt_count", sa.Integer(), default=0),
        schema="master",
    )

    # Add constraint for billing_method
    op.create_check_constraint(
        "billing_method_check",
        "contract_billing_schedules",
        "billing_method IN ('recurrent', 'manual')",
        schema="master",
    )

    # Create indexes for new fields
    op.create_index(
        "contract_billing_schedules_billing_method_idx",
        "contract_billing_schedules",
        ["billing_method"],
        schema="master",
    )
    op.create_index(
        "contract_billing_schedules_pagbank_subscription_idx",
        "contract_billing_schedules",
        ["pagbank_subscription_id"],
        schema="master",
    )
    op.create_index(
        "contract_billing_schedules_pagbank_customer_idx",
        "contract_billing_schedules",
        ["pagbank_customer_id"],
        schema="master",
    )

    # Create pagbank_transactions table
    op.create_table(
        "pagbank_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("invoice_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("pagbank_transaction_id", sa.String(length=100)),
        sa.Column("pagbank_charge_id", sa.String(length=100)),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=20)),
        sa.Column("error_message", sa.Text()),
        sa.Column("webhook_data", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.CheckConstraint(
            "transaction_type IN ('recurrent', 'checkout')",
            name="pagbank_trans_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'declined', 'failed', 'cancelled')",
            name="pagbank_status_check",
        ),
        sa.CheckConstraint(
            "amount >= 0",
            name="pagbank_amount_check",
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"], ["master.contract_invoices.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create indexes for pagbank_transactions
    op.create_index(
        "pagbank_transactions_invoice_id_idx",
        "pagbank_transactions",
        ["invoice_id"],
        schema="master",
    )
    op.create_index(
        "pagbank_transactions_status_idx",
        "pagbank_transactions",
        ["status"],
        schema="master",
    )
    op.create_index(
        "pagbank_transactions_type_idx",
        "pagbank_transactions",
        ["transaction_type"],
        schema="master",
    )
    op.create_index(
        "pagbank_transactions_pagbank_transaction_id_idx",
        "pagbank_transactions",
        ["pagbank_transaction_id"],
        schema="master",
    )
    op.create_index(
        "pagbank_transactions_pagbank_charge_id_idx",
        "pagbank_transactions",
        ["pagbank_charge_id"],
        schema="master",
    )
    op.create_index(
        "pagbank_transactions_created_at_idx",
        "pagbank_transactions",
        ["created_at"],
        schema="master",
    )

    # Create trigger to update updated_at automatically
    op.execute(
        """
        CREATE OR REPLACE FUNCTION master.update_pagbank_transaction_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER trigger_update_pagbank_transaction_timestamp
        BEFORE UPDATE ON master.pagbank_transactions
        FOR EACH ROW
        EXECUTE FUNCTION master.update_pagbank_transaction_timestamp();
    """
    )

    # Update existing billing schedules to default manual method
    op.execute(
        """
        UPDATE master.contract_billing_schedules
        SET billing_method = 'manual'
        WHERE billing_method IS NULL;
    """
    )


def downgrade():
    """Remove PagBank integration fields and tables."""

    # Drop trigger and function for pagbank_transactions
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_pagbank_transaction_timestamp ON master.pagbank_transactions;"
    )
    op.execute("DROP FUNCTION IF EXISTS master.update_pagbank_transaction_timestamp();")

    # Drop pagbank_transactions table
    op.drop_table("pagbank_transactions", schema="master")

    # Drop indexes for contract_billing_schedules new fields
    op.drop_index(
        "contract_billing_schedules_pagbank_customer_idx",
        "contract_billing_schedules",
        schema="master",
    )
    op.drop_index(
        "contract_billing_schedules_pagbank_subscription_idx",
        "contract_billing_schedules",
        schema="master",
    )
    op.drop_index(
        "contract_billing_schedules_billing_method_idx",
        "contract_billing_schedules",
        schema="master",
    )

    # Drop constraint
    op.drop_constraint(
        "billing_method_check", "contract_billing_schedules", schema="master"
    )

    # Remove columns from contract_billing_schedules
    op.drop_column("contract_billing_schedules", "attempt_count", schema="master")
    op.drop_column("contract_billing_schedules", "last_attempt_date", schema="master")
    op.drop_column(
        "contract_billing_schedules", "auto_fallback_enabled", schema="master"
    )
    op.drop_column("contract_billing_schedules", "pagbank_customer_id", schema="master")
    op.drop_column(
        "contract_billing_schedules", "pagbank_subscription_id", schema="master"
    )
    op.drop_column("contract_billing_schedules", "billing_method", schema="master")
