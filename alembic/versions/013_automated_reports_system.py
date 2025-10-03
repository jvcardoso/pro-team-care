"""Create automated reports system

Revision ID: 013_automated_reports_system
Revises: 012_service_execution_interface
Create Date: 2025-09-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '013_automated_reports_system'
down_revision: Union[str, None] = '012_service_execution_interface'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create automated reports table
    op.create_table('automated_reports',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('report_type', sa.String(30), nullable=False),  # monthly_contract, monthly_company, annual_summary
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('contract_id', sa.BigInteger(), nullable=True),
        sa.Column('report_year', sa.Integer(), nullable=False),
        sa.Column('report_month', sa.Integer(), nullable=True),  # NULL para relatórios anuais
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('report_data', sa.JSON(), nullable=False),  # Dados completos do relatório
        sa.Column('file_path', sa.String(500)),  # Caminho para arquivo PDF/Excel se gerado
        sa.Column('email_sent', sa.Boolean(), default=False),  # Flag se foi enviado por email
        sa.Column('email_sent_at', sa.DateTime()),
        sa.Column('recipients', sa.JSON()),  # Lista de destinatários do email
        sa.Column('status', sa.String(20), default='generated'),  # generated, sent, archived, failed
        sa.Column('error_message', sa.Text()),  # Mensagem de erro se falhou
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['company_id'], ['master.companies.id'], ),
        sa.ForeignKeyConstraint(['contract_id'], ['master.contracts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("report_type IN ('monthly_contract', 'monthly_company', 'annual_summary', 'custom')", name='automated_reports_type_check'),
        sa.CheckConstraint("status IN ('generated', 'sent', 'archived', 'failed')", name='automated_reports_status_check'),
        sa.CheckConstraint("report_month IS NULL OR (report_month >= 1 AND report_month <= 12)", name='automated_reports_month_check'),
        schema='master'
    )

    # Create report schedules table for automated generation
    op.create_table('report_schedules',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_name', sa.String(100), nullable=False),
        sa.Column('schedule_type', sa.String(20), nullable=False),  # monthly, quarterly, annual
        sa.Column('company_id', sa.BigInteger(), nullable=True),  # NULL = todos as empresas
        sa.Column('contract_id', sa.BigInteger(), nullable=True),  # NULL = todos os contratos da empresa
        sa.Column('report_types', sa.JSON(), nullable=False),  # Tipos de relatório a gerar
        sa.Column('recipients', sa.JSON(), nullable=False),  # Lista de emails destinatários
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('next_execution', sa.DateTime(), nullable=False),
        sa.Column('last_execution', sa.DateTime()),
        sa.Column('execution_day', sa.Integer()),  # Dia do mês para execução (1-31)
        sa.Column('execution_hour', sa.Integer(), default=8),  # Hora de execução (0-23)
        sa.Column('timezone', sa.String(50), default='America/Sao_Paulo'),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_by', sa.BigInteger()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['company_id'], ['master.companies.id'], ),
        sa.ForeignKeyConstraint(['contract_id'], ['master.contracts.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['master.users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['master.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("schedule_type IN ('monthly', 'quarterly', 'annual')", name='report_schedules_type_check'),
        sa.CheckConstraint("execution_day IS NULL OR (execution_day >= 1 AND execution_day <= 31)", name='report_schedules_day_check'),
        sa.CheckConstraint("execution_hour >= 0 AND execution_hour <= 23", name='report_schedules_hour_check'),
        schema='master'
    )

    # Create report execution log for tracking
    op.create_table('report_execution_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), nullable=True),  # NULL para execuções manuais
        sa.Column('execution_type', sa.String(20), nullable=False),  # scheduled, manual, api
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('status', sa.String(20), nullable=False),  # running, completed, failed
        sa.Column('total_reports', sa.Integer(), default=0),
        sa.Column('successful_reports', sa.Integer(), default=0),
        sa.Column('failed_reports', sa.Integer(), default=0),
        sa.Column('execution_summary', sa.JSON()),  # Resumo detalhado da execução
        sa.Column('error_details', sa.Text()),
        sa.Column('triggered_by', sa.BigInteger()),  # User que iniciou execução manual
        sa.ForeignKeyConstraint(['schedule_id'], ['master.report_schedules.id'], ),
        sa.ForeignKeyConstraint(['triggered_by'], ['master.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("execution_type IN ('scheduled', 'manual', 'api')", name='report_execution_log_type_check'),
        sa.CheckConstraint("status IN ('running', 'completed', 'failed', 'cancelled')", name='report_execution_log_status_check'),
        schema='master'
    )

    # Create indexes for performance
    op.create_index('automated_reports_company_date_idx', 'automated_reports', ['company_id', 'report_year', 'report_month'], schema='master')
    op.create_index('automated_reports_contract_date_idx', 'automated_reports', ['contract_id', 'report_year', 'report_month'], schema='master')
    op.create_index('automated_reports_type_date_idx', 'automated_reports', ['report_type', 'report_year', 'report_month'], schema='master')
    op.create_index('automated_reports_generated_at_idx', 'automated_reports', ['generated_at'], schema='master')
    op.create_index('automated_reports_status_idx', 'automated_reports', ['status'], schema='master')

    op.create_index('report_schedules_next_execution_idx', 'report_schedules', ['next_execution', 'is_active'], schema='master')
    op.create_index('report_schedules_company_idx', 'report_schedules', ['company_id'], schema='master')

    op.create_index('report_execution_log_started_at_idx', 'report_execution_log', ['started_at'], schema='master')
    op.create_index('report_execution_log_status_idx', 'report_execution_log', ['status'], schema='master')

    # Create function to update next_execution automatically
    op.execute("""
        CREATE OR REPLACE FUNCTION master.update_report_schedule_next_execution()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Calculate next execution based on schedule type
            CASE NEW.schedule_type
                WHEN 'monthly' THEN
                    -- Next month, same day
                    NEW.next_execution := date_trunc('month', NEW.last_execution) + interval '1 month' +
                                         (NEW.execution_day - 1) * interval '1 day' +
                                         NEW.execution_hour * interval '1 hour';

                WHEN 'quarterly' THEN
                    -- Next quarter, same day
                    NEW.next_execution := date_trunc('quarter', NEW.last_execution) + interval '3 months' +
                                         (NEW.execution_day - 1) * interval '1 day' +
                                         NEW.execution_hour * interval '1 hour';

                WHEN 'annual' THEN
                    -- Next year, same month/day
                    NEW.next_execution := date_trunc('year', NEW.last_execution) + interval '1 year' +
                                         (NEW.execution_day - 1) * interval '1 day' +
                                         NEW.execution_hour * interval '1 hour';
            END CASE;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger for automatic next_execution update
    op.execute("""
        CREATE TRIGGER trigger_update_report_schedule_next_execution
            BEFORE UPDATE ON master.report_schedules
            FOR EACH ROW
            WHEN (OLD.last_execution IS DISTINCT FROM NEW.last_execution)
            EXECUTE FUNCTION master.update_report_schedule_next_execution();
    """)

    # Create function to find pending scheduled reports
    op.execute("""
        CREATE OR REPLACE FUNCTION master.get_pending_scheduled_reports(
            check_time TIMESTAMP DEFAULT NOW()
        ) RETURNS TABLE (
            schedule_id BIGINT,
            schedule_name TEXT,
            company_id BIGINT,
            contract_id BIGINT,
            report_types JSON,
            recipients JSON,
            next_execution TIMESTAMP
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                rs.id,
                rs.schedule_name,
                rs.company_id,
                rs.contract_id,
                rs.report_types,
                rs.recipients,
                rs.next_execution
            FROM master.report_schedules rs
            WHERE rs.is_active = true
              AND rs.next_execution <= check_time
            ORDER BY rs.next_execution;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Insert default monthly report schedule for system admin
    op.execute("""
        INSERT INTO master.report_schedules (
            schedule_name,
            schedule_type,
            company_id,
            contract_id,
            report_types,
            recipients,
            is_active,
            next_execution,
            execution_day,
            execution_hour,
            created_by
        )
        SELECT
            'Relatórios Mensais Automáticos',
            'monthly',
            NULL,  -- Todas as empresas
            NULL,  -- Todos os contratos
            '["monthly_company", "monthly_contract"]'::json,
            '["admin@proteamcare.com"]'::json,
            true,
            date_trunc('month', NOW()) + interval '1 month' + interval '5 days' + interval '8 hours',  -- Dia 5 do próximo mês às 8h
            5,     -- Dia 5
            8,     -- 8h
            u.id
        FROM master.users u
        WHERE u.email_address = 'admin@proteamcare.com'
        LIMIT 1;
    """)

    # Create view for report dashboard
    op.execute("""
        CREATE VIEW master.v_reports_dashboard AS
        SELECT
            ar.id,
            ar.report_type,
            ar.company_id,
            cp.name as company_name,
            ar.contract_id,
            hc.plan_name as contract_name,
            ar.report_year,
            ar.report_month,
            ar.generated_at,
            ar.status,
            ar.email_sent,
            ar.email_sent_at,
            CASE
                WHEN ar.report_month IS NOT NULL THEN
                    ar.report_year || '/' || LPAD(ar.report_month::text, 2, '0')
                ELSE
                    ar.report_year::text
            END as period_display,
            ar.created_at
        FROM master.automated_reports ar
        LEFT JOIN master.companies c ON ar.company_id = c.id
        LEFT JOIN master.people cp ON c.person_id = cp.id
        LEFT JOIN master.contracts hc ON ar.contract_id = hc.id
        ORDER BY ar.generated_at DESC;
    """)


def downgrade() -> None:
    # Drop view
    op.execute("DROP VIEW IF EXISTS master.v_reports_dashboard;")

    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trigger_update_report_schedule_next_execution ON master.report_schedules;")
    op.execute("DROP FUNCTION IF EXISTS master.update_report_schedule_next_execution();")
    op.execute("DROP FUNCTION IF EXISTS master.get_pending_scheduled_reports(TIMESTAMP);")

    # Drop indexes
    op.drop_index('report_execution_log_status_idx', table_name='report_execution_log', schema='master')
    op.drop_index('report_execution_log_started_at_idx', table_name='report_execution_log', schema='master')
    op.drop_index('report_schedules_company_idx', table_name='report_schedules', schema='master')
    op.drop_index('report_schedules_next_execution_idx', table_name='report_schedules', schema='master')
    op.drop_index('automated_reports_status_idx', table_name='automated_reports', schema='master')
    op.drop_index('automated_reports_generated_at_idx', table_name='automated_reports', schema='master')
    op.drop_index('automated_reports_type_date_idx', table_name='automated_reports', schema='master')
    op.drop_index('automated_reports_contract_date_idx', table_name='automated_reports', schema='master')
    op.drop_index('automated_reports_company_date_idx', table_name='automated_reports', schema='master')

    # Drop tables
    op.drop_table('report_execution_log', schema='master')
    op.drop_table('report_schedules', schema='master')
    op.drop_table('automated_reports', schema='master')