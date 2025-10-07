"""Create service execution interface system

Revision ID: 012_service_execution_interface
Revises: 011_automatic_limits_control
Create Date: 2025-09-18 22:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012_service_execution_interface"
down_revision: Union[str, None] = "011_automatic_limits_control"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create service executions table
    op.create_table(
        "service_executions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("authorization_id", sa.BigInteger(), nullable=False),
        sa.Column("professional_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("execution_code", sa.String(30), nullable=False),
        sa.Column("execution_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("sessions_consumed", sa.Integer(), nullable=False, default=1),
        sa.Column(
            "location_type", sa.String(20), nullable=False
        ),  # home, clinic, hospital, telemedicine
        sa.Column("address_id", sa.BigInteger()),
        sa.Column("coordinates", sa.String(50)),  # GPS coordinates
        sa.Column(
            "status", sa.String(20), nullable=False, default="scheduled"
        ),  # scheduled, in_progress, completed, cancelled, no_show
        sa.Column("pre_execution_notes", sa.Text()),
        sa.Column("execution_notes", sa.Text()),
        sa.Column("post_execution_notes", sa.Text()),
        sa.Column("patient_signature", sa.Text()),  # Base64 signature
        sa.Column("professional_signature", sa.Text()),  # Base64 signature
        sa.Column("materials_used", sa.JSON()),
        sa.Column("equipment_used", sa.JSON()),
        sa.Column("complications", sa.Text()),
        sa.Column("next_session_recommended", sa.Date()),
        sa.Column("satisfaction_rating", sa.Integer()),  # 1-5 scale
        sa.Column("satisfaction_comments", sa.Text()),
        sa.Column("photos", sa.JSON()),  # Array of photo metadata
        sa.Column("documents", sa.JSON()),  # Array of document metadata
        sa.Column("billing_amount", sa.Numeric(10, 2)),
        sa.Column(
            "billing_status", sa.String(20), default="pending"
        ),  # pending, approved, rejected, paid
        sa.Column("cancelled_reason", sa.Text()),
        sa.Column("cancelled_by", sa.BigInteger()),
        sa.Column("cancelled_at", sa.DateTime()),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column("updated_by", sa.BigInteger()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["authorization_id"],
            ["master.medical_authorizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["master.users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["master.users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["master.services_catalog.id"],
        ),
        sa.ForeignKeyConstraint(
            ["address_id"],
            ["master.addresses.id"],
        ),
        sa.ForeignKeyConstraint(
            ["cancelled_by"],
            ["master.users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["master.users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["master.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_code"),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show')",
            name="service_executions_status_check",
        ),
        sa.CheckConstraint(
            "location_type IN ('home', 'clinic', 'hospital', 'telemedicine')",
            name="service_executions_location_type_check",
        ),
        sa.CheckConstraint(
            "billing_status IN ('pending', 'approved', 'rejected', 'paid')",
            name="service_executions_billing_status_check",
        ),
        sa.CheckConstraint(
            "satisfaction_rating IS NULL OR (satisfaction_rating >= 1 AND satisfaction_rating <= 5)",
            name="service_executions_satisfaction_rating_check",
        ),
        sa.CheckConstraint(
            "sessions_consumed > 0", name="service_executions_sessions_consumed_check"
        ),
        schema="master",
    )

    # Create professional schedules table
    op.create_table(
        "professional_schedules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("professional_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, default=True),
        sa.Column("location_preference", sa.String(20)),  # home, clinic, any
        sa.Column("max_distance_km", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column("updated_by", sa.BigInteger()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["master.users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["master.users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["master.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "professional_id",
            "date",
            "start_time",
            name="professional_schedules_unique",
        ),
        sa.CheckConstraint(
            "location_preference IN ('home', 'clinic', 'any')",
            name="professional_schedules_location_preference_check",
        ),
        sa.CheckConstraint(
            "end_time > start_time", name="professional_schedules_time_check"
        ),
        schema="master",
    )

    # Create execution checklists table
    op.create_table(
        "execution_checklists",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("execution_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "checklist_type", sa.String(30), nullable=False
        ),  # pre_execution, during_execution, post_execution
        sa.Column("item_code", sa.String(50), nullable=False),
        sa.Column("item_description", sa.String(200), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, default=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("completed_by", sa.BigInteger()),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["master.service_executions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["completed_by"],
            ["master.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "checklist_type IN ('pre_execution', 'during_execution', 'post_execution')",
            name="execution_checklists_type_check",
        ),
        schema="master",
    )

    # Create indexes for performance
    op.create_index(
        "service_executions_authorization_idx",
        "service_executions",
        ["authorization_id"],
        schema="master",
    )
    op.create_index(
        "service_executions_professional_idx",
        "service_executions",
        ["professional_id"],
        schema="master",
    )
    op.create_index(
        "service_executions_patient_idx",
        "service_executions",
        ["patient_id"],
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
    op.create_index(
        "service_executions_billing_status_idx",
        "service_executions",
        ["billing_status"],
        schema="master",
    )

    op.create_index(
        "professional_schedules_professional_date_idx",
        "professional_schedules",
        ["professional_id", "date"],
        schema="master",
    )
    op.create_index(
        "professional_schedules_date_available_idx",
        "professional_schedules",
        ["date", "is_available"],
        schema="master",
    )

    op.create_index(
        "execution_checklists_execution_idx",
        "execution_checklists",
        ["execution_id"],
        schema="master",
    )
    op.create_index(
        "execution_checklists_type_idx",
        "execution_checklists",
        ["checklist_type"],
        schema="master",
    )

    # Create function to generate execution codes
    op.execute(
        """
        CREATE OR REPLACE FUNCTION master.generate_execution_code()
        RETURNS TRIGGER AS $$
        DECLARE
            new_code TEXT;
            counter INTEGER := 1;
            date_part TEXT;
        BEGIN
            -- Format: EXE-YYYYMMDD-001
            date_part := TO_CHAR(NEW.execution_date, 'YYYYMMDD');

            LOOP
                new_code := 'EXE-' || date_part || '-' || LPAD(counter::TEXT, 3, '0');

                -- Check if code already exists
                IF NOT EXISTS (SELECT 1 FROM master.service_executions WHERE execution_code = new_code) THEN
                    EXIT;
                END IF;

                counter := counter + 1;
            END LOOP;

            NEW.execution_code := new_code;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Create trigger for execution code generation
    op.execute(
        """
        CREATE TRIGGER trigger_generate_execution_code
            BEFORE INSERT ON master.service_executions
            FOR EACH ROW
            WHEN (NEW.execution_code IS NULL OR NEW.execution_code = '')
            EXECUTE FUNCTION master.generate_execution_code();
    """
    )

    # Create function to validate execution scheduling
    op.execute(
        """
        CREATE OR REPLACE FUNCTION master.validate_execution_scheduling(
            p_professional_id BIGINT,
            p_execution_date DATE,
            p_start_time TIME,
            p_end_time TIME,
            p_execution_id BIGINT DEFAULT NULL
        ) RETURNS JSON AS $$
        DECLARE
            conflicts_count INTEGER;
            schedule_available BOOLEAN;
            result JSON;
        BEGIN
            -- Check for scheduling conflicts with other executions
            SELECT COUNT(*)
            INTO conflicts_count
            FROM master.service_executions se
            WHERE se.professional_id = p_professional_id
              AND se.execution_date = p_execution_date
              AND se.status IN ('scheduled', 'in_progress')
              AND (p_execution_id IS NULL OR se.id != p_execution_id)
              AND (
                  (se.start_time <= p_start_time AND se.end_time > p_start_time) OR
                  (se.start_time < p_end_time AND se.end_time >= p_end_time) OR
                  (se.start_time >= p_start_time AND se.end_time <= p_end_time)
              );

            -- Check if professional has availability in schedule
            SELECT COALESCE(ps.is_available, false)
            INTO schedule_available
            FROM master.professional_schedules ps
            WHERE ps.professional_id = p_professional_id
              AND ps.date = p_execution_date
              AND ps.start_time <= p_start_time
              AND ps.end_time >= p_end_time;

            -- Build result
            result := json_build_object(
                'valid', (conflicts_count = 0 AND COALESCE(schedule_available, false)),
                'conflicts_count', conflicts_count,
                'schedule_available', COALESCE(schedule_available, false),
                'validation_date', NOW()
            );

            RETURN result;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Insert standard checklist items for different service types
    op.execute(
        """
        INSERT INTO master.execution_checklists (execution_id, checklist_type, item_code, item_description, is_required)
        SELECT
            0 as execution_id, -- Template items (execution_id = 0)
            checklist_type,
            item_code,
            item_description,
            is_required
        FROM (VALUES
            -- Pre-execution checklist
            ('pre_execution', 'PRE_001', 'Confirmar identidade do paciente', true),
            ('pre_execution', 'PRE_002', 'Verificar autorização médica válida', true),
            ('pre_execution', 'PRE_003', 'Conferir materiais e equipamentos', true),
            ('pre_execution', 'PRE_004', 'Avaliar condições do ambiente', true),
            ('pre_execution', 'PRE_005', 'Revisar histórico médico relevante', true),
            ('pre_execution', 'PRE_006', 'Confirmar consentimento do paciente', true),

            -- During execution checklist
            ('during_execution', 'DUR_001', 'Seguir protocolo técnico estabelecido', true),
            ('during_execution', 'DUR_002', 'Monitorar sinais vitais quando aplicável', true),
            ('during_execution', 'DUR_003', 'Documentar procedimentos realizados', true),
            ('during_execution', 'DUR_004', 'Observar reações do paciente', true),
            ('during_execution', 'DUR_005', 'Manter ambiente seguro', true),

            -- Post-execution checklist
            ('post_execution', 'POST_001', 'Orientar paciente sobre cuidados', true),
            ('post_execution', 'POST_002', 'Documentar resultados obtidos', true),
            ('post_execution', 'POST_003', 'Coletar assinatura do paciente', true),
            ('post_execution', 'POST_004', 'Agendar próxima sessão se necessário', false),
            ('post_execution', 'POST_005', 'Organizar materiais utilizados', true),
            ('post_execution', 'POST_006', 'Atualizar sistema com informações', true)
        ) AS checklist_items(checklist_type, item_code, item_description, is_required);
    """
    )


def downgrade() -> None:
    # Drop triggers and functions
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_generate_execution_code ON master.service_executions;"
    )
    op.execute("DROP FUNCTION IF EXISTS master.generate_execution_code();")
    op.execute(
        "DROP FUNCTION IF EXISTS master.validate_execution_scheduling(BIGINT, DATE, TIME, TIME, BIGINT);"
    )

    # Drop indexes
    op.drop_index(
        "execution_checklists_type_idx",
        table_name="execution_checklists",
        schema="master",
    )
    op.drop_index(
        "execution_checklists_execution_idx",
        table_name="execution_checklists",
        schema="master",
    )
    op.drop_index(
        "professional_schedules_date_available_idx",
        table_name="professional_schedules",
        schema="master",
    )
    op.drop_index(
        "professional_schedules_professional_date_idx",
        table_name="professional_schedules",
        schema="master",
    )
    op.drop_index(
        "service_executions_billing_status_idx",
        table_name="service_executions",
        schema="master",
    )
    op.drop_index(
        "service_executions_status_idx",
        table_name="service_executions",
        schema="master",
    )
    op.drop_index(
        "service_executions_execution_date_idx",
        table_name="service_executions",
        schema="master",
    )
    op.drop_index(
        "service_executions_patient_idx",
        table_name="service_executions",
        schema="master",
    )
    op.drop_index(
        "service_executions_professional_idx",
        table_name="service_executions",
        schema="master",
    )
    op.drop_index(
        "service_executions_authorization_idx",
        table_name="service_executions",
        schema="master",
    )

    # Drop tables
    op.drop_table("execution_checklists", schema="master")
    op.drop_table("professional_schedules", schema="master")
    op.drop_table("service_executions", schema="master")
