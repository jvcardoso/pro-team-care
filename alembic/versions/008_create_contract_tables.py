"""Create contract and services tables for home care

Revision ID: 008_create_contract_tables
Revises: f6c3a4d2e4dc
Create Date: 2025-01-18 20:35:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "008_create_contract_tables"
down_revision = "f6c3a4d2e4dc"
branch_labels = None
depends_on = None


def upgrade():
    """Create home care contract and services tables."""

    # Create services_catalog table
    op.create_table(
        "services_catalog",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("service_code", sa.String(length=20), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("service_category", sa.String(length=50), nullable=False),
        sa.Column("service_type", sa.String(length=30), nullable=False),
        sa.Column("requires_prescription", sa.Boolean(), default=False),
        sa.Column("requires_specialist", sa.Boolean(), default=False),
        sa.Column("home_visit_required", sa.Boolean(), default=True),
        sa.Column("default_unit_value", sa.Numeric(precision=10, scale=2)),
        sa.Column("billing_unit", sa.String(length=20), default="UNIT"),
        sa.Column("anvisa_regulated", sa.Boolean(), default=False),
        sa.Column("requires_authorization", sa.Boolean(), default=False),
        sa.Column("description", sa.Text()),
        sa.Column("instructions", sa.Text()),
        sa.Column("contraindications", sa.Text()),
        sa.Column("status", sa.String(length=20), default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.CheckConstraint(
            "service_category IN ('ENFERMAGEM', 'FISIOTERAPIA', 'MEDICINA', 'NUTRIÇÃO', 'PSICOLOGIA', 'FONOAUDIOLOGIA', 'TERAPIA_OCUPACIONAL', 'EQUIPAMENTO')",
            name="services_catalog_category_check",
        ),
        sa.CheckConstraint(
            "service_type IN ('VISITA', 'PROCEDIMENTO', 'MEDICAÇÃO', 'EQUIPAMENTO', 'CONSULTA', 'TERAPIA', 'EXAME', 'LOCAÇÃO')",
            name="services_catalog_type_check",
        ),
        sa.CheckConstraint(
            "billing_unit IN ('UNIT', 'HOUR', 'DAY', 'WEEK', 'MONTH', 'SESSION')",
            name="services_catalog_billing_unit_check",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'draft')",
            name="services_catalog_status_check",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_code", name="services_catalog_code_unique"),
        schema="master",
    )

    # Create indexes for services_catalog
    op.create_index(
        "services_catalog_category_idx",
        "services_catalog",
        ["service_category"],
        schema="master",
    )
    op.create_index(
        "services_catalog_type_idx",
        "services_catalog",
        ["service_type"],
        schema="master",
    )
    op.create_index(
        "services_catalog_status_idx", "services_catalog", ["status"], schema="master"
    )
    op.create_index(
        "services_catalog_code_idx",
        "services_catalog",
        ["service_code"],
        schema="master",
    )

    # Create contracts table
    op.create_table(
        "contracts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.BigInteger(), nullable=False),
        sa.Column("contract_number", sa.String(length=50), nullable=False),
        sa.Column("contract_type", sa.String(length=20), nullable=False),
        sa.Column("lives_contracted", sa.Integer(), nullable=False, default=1),
        sa.Column("lives_minimum", sa.Integer()),
        sa.Column("lives_maximum", sa.Integer()),
        sa.Column("allows_substitution", sa.Boolean(), default=False),
        sa.Column("control_period", sa.String(length=10), default="MONTHLY"),
        sa.Column("plan_name", sa.String(length=100), nullable=False),
        sa.Column("monthly_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("service_addresses", sa.JSON()),
        sa.Column("status", sa.String(length=20), default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger()),
        sa.Column("updated_by", sa.BigInteger()),
        sa.CheckConstraint(
            "contract_type IN ('INDIVIDUAL', 'CORPORATIVO', 'EMPRESARIAL')",
            name="contracts_type_check",
        ),
        sa.CheckConstraint(
            "control_period IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY')",
            name="contracts_control_period_check",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'cancelled', 'expired')",
            name="contracts_status_check",
        ),
        sa.ForeignKeyConstraint(["client_id"], ["master.clients.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_number", name="contracts_number_unique"),
        schema="master",
    )

    # Create indexes for contracts
    op.create_index(
        "contracts_client_id_idx", "contracts", ["client_id"], schema="master"
    )
    op.create_index("contracts_status_idx", "contracts", ["status"], schema="master")
    op.create_index(
        "contracts_start_date_idx", "contracts", ["start_date"], schema="master"
    )
    op.create_index(
        "contracts_number_idx", "contracts", ["contract_number"], schema="master"
    )

    # Create contract_lives table
    op.create_table(
        "contract_lives",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_id", sa.BigInteger(), nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("relationship_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), default="active"),
        sa.Column("substitution_reason", sa.String(length=100)),
        sa.Column("primary_service_address", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger()),
        sa.CheckConstraint(
            "relationship_type IN ('TITULAR', 'DEPENDENTE', 'FUNCIONARIO', 'BENEFICIARIO')",
            name="contract_lives_relationship_check",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'substituted', 'cancelled')",
            name="contract_lives_status_check",
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["master.contracts.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["master.people.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contract_id",
            "person_id",
            "start_date",
            name="contract_lives_unique_period",
        ),
        schema="master",
    )

    # Create indexes for contract_lives
    op.create_index(
        "contract_lives_contract_id_idx",
        "contract_lives",
        ["contract_id"],
        schema="master",
    )
    op.create_index(
        "contract_lives_person_id_idx", "contract_lives", ["person_id"], schema="master"
    )
    op.create_index(
        "contract_lives_status_idx", "contract_lives", ["status"], schema="master"
    )
    op.create_index(
        "contract_lives_date_range_idx",
        "contract_lives",
        ["start_date", "end_date"],
        schema="master",
    )

    # Create contract_services table
    op.create_table(
        "contract_services",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_id", sa.BigInteger(), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("monthly_limit", sa.Integer()),
        sa.Column("daily_limit", sa.Integer()),
        sa.Column("annual_limit", sa.Integer()),
        sa.Column("unit_value", sa.Numeric(precision=10, scale=2)),
        sa.Column("requires_pre_authorization", sa.Boolean(), default=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("status", sa.String(length=20), default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger()),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="contract_services_status_check",
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["master.contracts.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["master.services_catalog.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contract_id",
            "service_id",
            "start_date",
            name="contract_services_unique_period",
        ),
        schema="master",
    )

    # Create indexes for contract_services
    op.create_index(
        "contract_services_contract_id_idx",
        "contract_services",
        ["contract_id"],
        schema="master",
    )
    op.create_index(
        "contract_services_service_id_idx",
        "contract_services",
        ["service_id"],
        schema="master",
    )
    op.create_index(
        "contract_services_status_idx", "contract_services", ["status"], schema="master"
    )
    op.create_index(
        "contract_services_date_range_idx",
        "contract_services",
        ["start_date", "end_date"],
        schema="master",
    )

    # Create contract_life_services table
    op.create_table(
        "contract_life_services",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_life_id", sa.BigInteger(), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("is_authorized", sa.Boolean(), default=True),
        sa.Column("authorization_date", sa.Date()),
        sa.Column("authorized_by", sa.BigInteger()),
        sa.Column("monthly_limit_override", sa.Integer()),
        sa.Column("daily_limit_override", sa.Integer()),
        sa.Column("annual_limit_override", sa.Integer()),
        sa.Column("medical_indication", sa.Text()),
        sa.Column("contraindications", sa.Text()),
        sa.Column("special_instructions", sa.Text()),
        sa.Column("priority_level", sa.String(length=20), default="NORMAL"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("status", sa.String(length=20), default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger()),
        sa.CheckConstraint(
            "priority_level IN ('URGENT', 'HIGH', 'NORMAL', 'LOW')",
            name="contract_life_services_priority_check",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="contract_life_services_status_check",
        ),
        sa.ForeignKeyConstraint(["contract_life_id"], ["master.contract_lives.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["master.services_catalog.id"]),
        sa.ForeignKeyConstraint(["authorized_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contract_life_id",
            "service_id",
            "start_date",
            name="contract_life_services_unique_period",
        ),
        schema="master",
    )

    # Create indexes for contract_life_services
    op.create_index(
        "contract_life_services_contract_life_id_idx",
        "contract_life_services",
        ["contract_life_id"],
        schema="master",
    )
    op.create_index(
        "contract_life_services_service_id_idx",
        "contract_life_services",
        ["service_id"],
        schema="master",
    )
    op.create_index(
        "contract_life_services_status_idx",
        "contract_life_services",
        ["status"],
        schema="master",
    )
    op.create_index(
        "contract_life_services_authorized_idx",
        "contract_life_services",
        ["is_authorized"],
        schema="master",
    )

    # Create service_executions table
    op.create_table(
        "service_executions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_life_id", sa.BigInteger(), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("execution_date", sa.DateTime(), nullable=False),
        sa.Column("professional_id", sa.BigInteger()),
        sa.Column("quantity", sa.Numeric(precision=8, scale=2), default=1),
        sa.Column("unit_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("total_value", sa.Numeric(precision=10, scale=2)),
        sa.Column("service_address", sa.JSON()),
        sa.Column("arrival_time", sa.DateTime()),
        sa.Column("departure_time", sa.DateTime()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("execution_notes", sa.Text()),
        sa.Column("patient_response", sa.Text()),
        sa.Column("complications", sa.Text()),
        sa.Column("materials_used", sa.JSON()),
        sa.Column("quality_score", sa.Integer()),
        sa.Column("family_satisfaction", sa.Integer()),
        sa.Column("status", sa.String(length=20), default="executed"),
        sa.Column("cancellation_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger()),
        sa.CheckConstraint(
            "status IN ('scheduled', 'executed', 'cancelled', 'no_show')",
            name="service_executions_status_check",
        ),
        sa.CheckConstraint(
            "quality_score >= 1 AND quality_score <= 5",
            name="service_executions_quality_score_check",
        ),
        sa.CheckConstraint(
            "family_satisfaction >= 1 AND family_satisfaction <= 5",
            name="service_executions_satisfaction_check",
        ),
        sa.ForeignKeyConstraint(["contract_life_id"], ["master.contract_lives.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["master.services_catalog.id"]),
        sa.ForeignKeyConstraint(["professional_id"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create indexes for service_executions
    op.create_index(
        "service_executions_contract_life_id_idx",
        "service_executions",
        ["contract_life_id"],
        schema="master",
    )
    op.create_index(
        "service_executions_service_id_idx",
        "service_executions",
        ["service_id"],
        schema="master",
    )
    op.create_index(
        "service_executions_professional_id_idx",
        "service_executions",
        ["professional_id"],
        schema="master",
    )
    op.create_index(
        "service_executions_execution_date_idx",
        "service_executions",
        ["execution_date"],
        schema="master",
    )
    op.create_index(
        "service_executions_status_idx",
        "service_executions",
        ["status"],
        schema="master",
    )

    # Insert some example services in the catalog
    op.execute(
        """
        INSERT INTO master.services_catalog (service_code, service_name, service_category, service_type, requires_prescription, home_visit_required, default_unit_value, description, created_at, updated_at) VALUES
        ('ENF001', 'Aplicação de Medicação EV', 'ENFERMAGEM', 'PROCEDIMENTO', true, true, 80.00, 'Aplicação de medicação endovenosa domiciliar', now(), now()),
        ('ENF002', 'Curativo Simples', 'ENFERMAGEM', 'PROCEDIMENTO', false, true, 45.00, 'Realização de curativo simples em domicílio', now(), now()),
        ('ENF003', 'Coleta de Sangue', 'ENFERMAGEM', 'EXAME', false, true, 35.00, 'Coleta de sangue para exames laboratoriais', now(), now()),
        ('FIS001', 'Fisioterapia Motora', 'FISIOTERAPIA', 'TERAPIA', true, true, 120.00, 'Sessão de fisioterapia motora domiciliar', now(), now()),
        ('MED001', 'Consulta Médica Domiciliar', 'MEDICINA', 'CONSULTA', false, true, 250.00, 'Consulta médica realizada em domicílio', now(), now()),
        ('EQP001', 'Locação Cama Hospitalar', 'EQUIPAMENTO', 'LOCAÇÃO', false, false, 300.00, 'Locação mensal de cama hospitalar', now(), now()),
        ('NUT001', 'Consulta Nutricional', 'NUTRIÇÃO', 'CONSULTA', false, true, 150.00, 'Consulta nutricional domiciliar', now(), now()),
        ('PSI001', 'Atendimento Psicológico', 'PSICOLOGIA', 'CONSULTA', false, true, 120.00, 'Sessão de psicoterapia domiciliar', now(), now());
    """
    )


def downgrade():
    """Drop home care contract and services tables."""

    # Drop tables in reverse order due to foreign key dependencies
    op.drop_table("service_executions", schema="master")
    op.drop_table("contract_life_services", schema="master")
    op.drop_table("contract_services", schema="master")
    op.drop_table("contract_lives", schema="master")
    op.drop_table("contracts", schema="master")
    op.drop_table("services_catalog", schema="master")
