"""Add service address fields to contracts

Revision ID: 014_add_service_address_fields
Revises: 013_automated_reports_system
Create Date: 2025-09-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_service_address_fields'
down_revision = '013_automated_reports_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add service_address_type column with default value
    op.add_column('contracts', sa.Column('service_address_type', sa.String(10), nullable=True, default='PATIENT'))

    # Update existing records to have default values
    op.execute("UPDATE contracts SET service_address_type = 'PATIENT' WHERE service_address_type IS NULL")


def downgrade() -> None:
    # Remove the added column
    op.drop_column('contracts', 'service_address_type')