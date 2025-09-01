"""add_enrichment_fields_to_addresses

Revision ID: f6c3a4d2e4db
Revises: 4c47259799c2
Create Date: 2025-09-01 08:15:47.900583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6c3a4d2e4db'
down_revision: Union[str, Sequence[str], None] = '4c47259799c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add enrichment fields to addresses table
    op.add_column('addresses', sa.Column('coordinates_added_at', sa.DateTime(), nullable=True), schema='master')
    op.add_column('addresses', sa.Column('coordinates_source', sa.String(50), nullable=True), schema='master')
    op.add_column('addresses', sa.Column('enriched_at', sa.DateTime(), nullable=True), schema='master')
    op.add_column('addresses', sa.Column('enrichment_source', sa.String(50), nullable=True), schema='master')


def downgrade() -> None:
    """Downgrade schema."""
    # Remove enrichment fields from addresses table
    op.drop_column('addresses', 'enrichment_source', schema='master')
    op.drop_column('addresses', 'enriched_at', schema='master')
    op.drop_column('addresses', 'coordinates_source', schema='master')
    op.drop_column('addresses', 'coordinates_added_at', schema='master')
