"""Create contract billing system tables

Revision ID: 015_contract_billing_system
Revises: 014_add_service_address_fields
Create Date: 2025-01-22 15:30:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "015_contract_billing_system"
down_revision = "014_add_service_address_fields"
branch_labels = None
depends_on = None


def upgrade():
    """Create contract billing system tables."""

    # Create contract_billing_schedules table
    op.create_table(
        "contract_billing_schedules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "billing_cycle", sa.String(length=20), nullable=False, default="MONTHLY"
        ),
        sa.Column("billing_day", sa.Integer(), nullable=False, default=1),
        sa.Column("next_billing_date", sa.Date(), nullable=False),
        sa.Column(
            "amount_per_cycle", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger()),
        sa.CheckConstraint(
            "billing_cycle IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI_ANNUAL', 'ANNUAL')",
            name="contract_billing_schedules_cycle_check",
        ),
        sa.CheckConstraint(
            "billing_day >= 1 AND billing_day <= 31",
            name="contract_billing_schedules_day_check",
        ),
        sa.ForeignKeyConstraint(
            ["contract_id"], ["master.contracts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contract_id", name="contract_billing_schedules_contract_unique"
        ),
        schema="master",
    )

    # Create indexes for contract_billing_schedules
    op.create_index(
        "contract_billing_schedules_contract_id_idx",
        "contract_billing_schedules",
        ["contract_id"],
        schema="master",
    )
    op.create_index(
        "contract_billing_schedules_next_billing_idx",
        "contract_billing_schedules",
        ["next_billing_date"],
        schema="master",
    )
    op.create_index(
        "contract_billing_schedules_is_active_idx",
        "contract_billing_schedules",
        ["is_active"],
        schema="master",
    )

    # Create contract_invoices table
    op.create_table(
        "contract_invoices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_id", sa.BigInteger(), nullable=False),
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column("billing_period_start", sa.Date(), nullable=False),
        sa.Column("billing_period_end", sa.Date(), nullable=False),
        sa.Column("lives_count", sa.Integer(), nullable=False),
        sa.Column("base_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "additional_services_amount",
            sa.Numeric(precision=10, scale=2),
            default=0.00,
        ),
        sa.Column("discounts", sa.Numeric(precision=10, scale=2), default=0.00),
        sa.Column("taxes", sa.Numeric(precision=10, scale=2), default=0.00),
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, default="pendente"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "issued_date", sa.Date(), nullable=False, default=sa.func.current_date()
        ),
        sa.Column("paid_date", sa.Date()),
        sa.Column("payment_method", sa.String(length=50)),
        sa.Column("payment_reference", sa.String(length=100)),
        sa.Column("payment_notes", sa.Text()),
        sa.Column("observations", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger()),
        sa.Column("updated_by", sa.BigInteger()),
        sa.CheckConstraint(
            "status IN ('pendente', 'enviada', 'paga', 'vencida', 'cancelada', 'em_atraso')",
            name="contract_invoices_status_check",
        ),
        sa.CheckConstraint(
            "lives_count >= 0",
            name="contract_invoices_lives_count_check",
        ),
        sa.CheckConstraint(
            "base_amount >= 0",
            name="contract_invoices_base_amount_check",
        ),
        sa.CheckConstraint(
            "total_amount >= 0",
            name="contract_invoices_total_amount_check",
        ),
        sa.ForeignKeyConstraint(
            ["contract_id"], ["master.contracts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number", name="contract_invoices_number_unique"),
        schema="master",
    )

    # Create indexes for contract_invoices
    op.create_index(
        "contract_invoices_contract_id_idx",
        "contract_invoices",
        ["contract_id"],
        schema="master",
    )
    op.create_index(
        "contract_invoices_status_idx", "contract_invoices", ["status"], schema="master"
    )
    op.create_index(
        "contract_invoices_due_date_idx",
        "contract_invoices",
        ["due_date"],
        schema="master",
    )
    op.create_index(
        "contract_invoices_issued_date_idx",
        "contract_invoices",
        ["issued_date"],
        schema="master",
    )
    op.create_index(
        "contract_invoices_billing_period_idx",
        "contract_invoices",
        ["billing_period_start", "billing_period_end"],
        schema="master",
    )
    op.create_index(
        "contract_invoices_number_idx",
        "contract_invoices",
        ["invoice_number"],
        schema="master",
    )

    # Create payment_receipts table
    op.create_table(
        "payment_receipts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("invoice_id", sa.BigInteger(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=10)),
        sa.Column("file_size", sa.BigInteger()),
        sa.Column("upload_date", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("verification_status", sa.String(length=20), default="pendente"),
        sa.Column("verified_by", sa.BigInteger()),
        sa.Column("verified_at", sa.DateTime()),
        sa.Column("notes", sa.Text()),
        sa.Column("uploaded_by", sa.BigInteger()),
        sa.CheckConstraint(
            "verification_status IN ('pendente', 'aprovado', 'rejeitado')",
            name="payment_receipts_verification_status_check",
        ),
        sa.CheckConstraint(
            "file_size >= 0",
            name="payment_receipts_file_size_check",
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"], ["master.contract_invoices.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["verified_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create indexes for payment_receipts
    op.create_index(
        "payment_receipts_invoice_id_idx",
        "payment_receipts",
        ["invoice_id"],
        schema="master",
    )
    op.create_index(
        "payment_receipts_verification_status_idx",
        "payment_receipts",
        ["verification_status"],
        schema="master",
    )
    op.create_index(
        "payment_receipts_upload_date_idx",
        "payment_receipts",
        ["upload_date"],
        schema="master",
    )
    op.create_index(
        "payment_receipts_uploaded_by_idx",
        "payment_receipts",
        ["uploaded_by"],
        schema="master",
    )

    # Create billing_audit_log table for tracking changes
    op.create_table(
        "billing_audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("old_values", sa.JSON()),
        sa.Column("new_values", sa.JSON()),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("timestamp", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("ip_address", sa.String(length=45)),
        sa.Column("user_agent", sa.String(length=500)),
        sa.CheckConstraint(
            "entity_type IN ('invoice', 'receipt', 'schedule')",
            name="billing_audit_log_entity_type_check",
        ),
        sa.CheckConstraint(
            "action IN ('created', 'updated', 'deleted', 'status_changed')",
            name="billing_audit_log_action_check",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create indexes for billing_audit_log
    op.create_index(
        "billing_audit_log_entity_idx",
        "billing_audit_log",
        ["entity_type", "entity_id"],
        schema="master",
    )
    op.create_index(
        "billing_audit_log_timestamp_idx",
        "billing_audit_log",
        ["timestamp"],
        schema="master",
    )
    op.create_index(
        "billing_audit_log_user_id_idx",
        "billing_audit_log",
        ["user_id"],
        schema="master",
    )

    # Insert initial billing schedules for existing active contracts
    op.execute(
        """
        INSERT INTO master.contract_billing_schedules (
            contract_id,
            billing_cycle,
            billing_day,
            next_billing_date,
            amount_per_cycle,
            is_active,
            created_at,
            updated_at
        )
        SELECT
            c.id,
            COALESCE(c.control_period, 'MONTHLY') as billing_cycle,
            1 as billing_day,
            CASE
                WHEN c.control_period = 'MONTHLY' THEN
                    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                WHEN c.control_period = 'QUARTERLY' THEN
                    DATE_TRUNC('quarter', CURRENT_DATE) + INTERVAL '3 months'
                ELSE
                    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            END as next_billing_date,
            COALESCE(c.monthly_value, 0.00) as amount_per_cycle,
            true as is_active,
            NOW() as created_at,
            NOW() as updated_at
        FROM master.contracts c
        WHERE c.status = 'active'
        AND c.monthly_value IS NOT NULL
        AND c.monthly_value > 0;
    """
    )

    # Create function to auto-update next_billing_date after invoice creation
    op.execute(
        """
        CREATE OR REPLACE FUNCTION master.update_next_billing_date()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' AND NEW.status = 'enviada' THEN
                UPDATE master.contract_billing_schedules
                SET next_billing_date = CASE
                    WHEN billing_cycle = 'MONTHLY' THEN
                        next_billing_date + INTERVAL '1 month'
                    WHEN billing_cycle = 'QUARTERLY' THEN
                        next_billing_date + INTERVAL '3 months'
                    WHEN billing_cycle = 'SEMI_ANNUAL' THEN
                        next_billing_date + INTERVAL '6 months'
                    WHEN billing_cycle = 'ANNUAL' THEN
                        next_billing_date + INTERVAL '1 year'
                    ELSE
                        next_billing_date + INTERVAL '1 month'
                END,
                updated_at = NOW()
                WHERE contract_id = NEW.contract_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Create trigger for auto-updating next billing date
    op.execute(
        """
        CREATE TRIGGER trigger_update_next_billing_date
        AFTER INSERT ON master.contract_invoices
        FOR EACH ROW
        EXECUTE FUNCTION master.update_next_billing_date();
    """
    )


def downgrade():
    """Drop contract billing system tables."""

    # Drop trigger and function
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_next_billing_date ON master.contract_invoices;"
    )
    op.execute("DROP FUNCTION IF EXISTS master.update_next_billing_date();")

    # Drop tables in reverse order due to foreign key dependencies
    op.drop_table("billing_audit_log", schema="master")
    op.drop_table("payment_receipts", schema="master")
    op.drop_table("contract_invoices", schema="master")
    op.drop_table("contract_billing_schedules", schema="master")
