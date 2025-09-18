"""Allow null values for company_id and person_id"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6c3a4d2e4dc"
down_revision: Union[str, None] = "f6c3a4d2e4db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Allow NULL values for company_id in people table
    op.alter_column(
        "people",
        "company_id",
        existing_type=sa.BigInteger(),
        nullable=True,
        schema="master",
    )

    # Allow NULL values for person_id in companies table
    op.alter_column(
        "companies",
        "person_id",
        existing_type=sa.BigInteger(),
        nullable=True,
        schema="master",
    )


def downgrade() -> None:
    # Revert to NOT NULL
    op.alter_column(
        "people",
        "company_id",
        existing_type=sa.BigInteger(),
        nullable=False,
        schema="master",
    )

    op.alter_column(
        "companies",
        "person_id",
        existing_type=sa.BigInteger(),
        nullable=False,
        schema="master",
    )
