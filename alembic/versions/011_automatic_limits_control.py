"""Create automatic limits control system

Revision ID: 011_automatic_limits_control
Revises: 010_medical_authorizations
Create Date: 2025-09-18 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011_automatic_limits_control'
down_revision = '010_medical_authorizations'
branch_labels = None
depends_on = None


def upgrade():
    """Create automatic limits control system"""

    # Create service_usage_tracking table for detailed tracking
    op.create_table(
        "service_usage_tracking",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("authorization_id", sa.BigInteger(), nullable=False),
        sa.Column("service_execution_id", sa.BigInteger(), nullable=True),  # Link to actual execution
        sa.Column("execution_date", sa.Date(), nullable=False),
        sa.Column("execution_time", sa.Time(), nullable=False),
        sa.Column("professional_id", sa.BigInteger(), nullable=False),
        sa.Column("sessions_used", sa.Integer(), nullable=False, default=1),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("location_type", sa.String(20), nullable=False, default="HOME"),  # HOME, CLINIC, HOSPITAL
        sa.Column("patient_condition", sa.Text(), nullable=True),
        sa.Column("service_notes", sa.Text(), nullable=True),
        sa.Column("value_charged", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="completed"),
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
        sa.Column("validated_by", sa.BigInteger(), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "location_type IN ('HOME', 'CLINIC', 'HOSPITAL', 'EMERGENCY')",
            name="service_usage_location_check",
        ),
        sa.CheckConstraint(
            "status IN ('completed', 'cancelled', 'pending_validation', 'rejected')",
            name="service_usage_status_check",
        ),
        sa.ForeignKeyConstraint(["authorization_id"], ["master.medical_authorizations.id"]),
        sa.ForeignKeyConstraint(["professional_id"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["validated_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create limits_configuration table for flexible limit rules
    op.create_table(
        "limits_configuration",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_id", sa.BigInteger(), nullable=True),  # NULL = global rule
        sa.Column("service_id", sa.BigInteger(), nullable=True),   # NULL = all services
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),     # SESSION, FINANCIAL, FREQUENCY
        sa.Column("limit_scope", sa.String(20), nullable=False),   # DAILY, WEEKLY, MONTHLY, YEARLY
        sa.Column("limit_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("warning_threshold", sa.Numeric(5, 2), nullable=False, default=0.8),  # 80%
        sa.Column("alert_threshold", sa.Numeric(5, 2), nullable=False, default=0.95),   # 95%
        sa.Column("auto_block", sa.Boolean(), nullable=False, default=True),
        sa.Column("override_allowed", sa.Boolean(), nullable=False, default=False),
        sa.Column("priority", sa.Integer(), nullable=False, default=100),  # Lower = higher priority
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "rule_type IN ('SESSION', 'FINANCIAL', 'FREQUENCY', 'CONCURRENT')",
            name="limits_rule_type_check",
        ),
        sa.CheckConstraint(
            "limit_scope IN ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'TOTAL')",
            name="limits_scope_check",
        ),
        sa.CheckConstraint(
            "warning_threshold <= alert_threshold",
            name="limits_threshold_order_check",
        ),
        sa.CheckConstraint(
            "alert_threshold <= 1.0",
            name="limits_threshold_max_check",
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["master.contracts.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["master.services_catalog.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create limits_violations table for tracking when limits are exceeded
    op.create_table(
        "limits_violations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("limit_rule_id", sa.BigInteger(), nullable=False),
        sa.Column("contract_id", sa.BigInteger(), nullable=True),
        sa.Column("authorization_id", sa.BigInteger(), nullable=True),
        sa.Column("usage_tracking_id", sa.BigInteger(), nullable=True),
        sa.Column("violation_type", sa.String(20), nullable=False),  # WARNING, ALERT, EXCEEDED
        sa.Column("violation_date", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("current_usage", sa.Numeric(12, 2), nullable=False),
        sa.Column("limit_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("percentage_used", sa.Numeric(5, 2), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("auto_action_taken", sa.String(50), nullable=True),  # BLOCKED, ALERT_SENT, etc.
        sa.Column("override_requested", sa.Boolean(), nullable=False, default=False),
        sa.Column("override_approved", sa.Boolean(), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("override_approved_by", sa.BigInteger(), nullable=True),
        sa.Column("override_approved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "violation_type IN ('WARNING', 'ALERT', 'EXCEEDED', 'BLOCKED')",
            name="limits_violation_type_check",
        ),
        sa.ForeignKeyConstraint(["limit_rule_id"], ["master.limits_configuration.id"]),
        sa.ForeignKeyConstraint(["contract_id"], ["master.contracts.id"]),
        sa.ForeignKeyConstraint(["authorization_id"], ["master.medical_authorizations.id"]),
        sa.ForeignKeyConstraint(["usage_tracking_id"], ["master.service_usage_tracking.id"]),
        sa.ForeignKeyConstraint(["override_approved_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create alerts_configuration table for notification rules
    op.create_table(
        "alerts_configuration",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("alert_name", sa.String(100), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),  # LIMIT_WARNING, LIMIT_EXCEEDED, etc.
        sa.Column("trigger_condition", sa.Text(), nullable=False),  # JSON with conditions
        sa.Column("notification_channels", sa.Text(), nullable=False),  # JSON: email, sms, push
        sa.Column("recipients", sa.Text(), nullable=False),  # JSON with user IDs and external contacts
        sa.Column("message_template", sa.Text(), nullable=False),
        sa.Column("escalation_rules", sa.Text(), nullable=True),  # JSON with escalation logic
        sa.Column("frequency_limit", sa.String(20), nullable=False, default="IMMEDIATE"),  # IMMEDIATE, HOURLY, DAILY
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("priority", sa.Integer(), nullable=False, default=100),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "alert_type IN ('LIMIT_WARNING', 'LIMIT_EXCEEDED', 'AUTHORIZATION_EXPIRING', 'USAGE_ANOMALY')",
            name="alerts_type_check",
        ),
        sa.CheckConstraint(
            "frequency_limit IN ('IMMEDIATE', 'HOURLY', 'DAILY', 'WEEKLY')",
            name="alerts_frequency_check",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create alerts_log table for tracking sent notifications
    op.create_table(
        "alerts_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("alert_config_id", sa.BigInteger(), nullable=False),
        sa.Column("violation_id", sa.BigInteger(), nullable=True),
        sa.Column("triggered_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("trigger_data", sa.Text(), nullable=False),  # JSON with context data
        sa.Column("recipients_contacted", sa.Text(), nullable=False),  # JSON with actual recipients
        sa.Column("channels_used", sa.Text(), nullable=False),  # JSON with channels and status
        sa.Column("message_sent", sa.Text(), nullable=False),
        sa.Column("delivery_status", sa.String(20), nullable=False, default="PENDING"),
        sa.Column("delivery_attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("acknowledged_by", sa.BigInteger(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "delivery_status IN ('PENDING', 'SENT', 'DELIVERED', 'FAILED', 'ACKNOWLEDGED')",
            name="alerts_delivery_status_check",
        ),
        sa.ForeignKeyConstraint(["alert_config_id"], ["master.alerts_configuration.id"]),
        sa.ForeignKeyConstraint(["violation_id"], ["master.limits_violations.id"]),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create indexes for performance
    op.create_index("service_usage_auth_date_idx", "service_usage_tracking", ["authorization_id", "execution_date"], schema="master")
    op.create_index("service_usage_professional_idx", "service_usage_tracking", ["professional_id", "execution_date"], schema="master")
    op.create_index("service_usage_status_idx", "service_usage_tracking", ["status"], schema="master")

    op.create_index("limits_config_contract_service_idx", "limits_configuration", ["contract_id", "service_id"], schema="master")
    op.create_index("limits_config_active_idx", "limits_configuration", ["is_active", "valid_from", "valid_until"], schema="master")
    op.create_index("limits_config_type_scope_idx", "limits_configuration", ["rule_type", "limit_scope"], schema="master")

    op.create_index("limits_violations_date_idx", "limits_violations", ["violation_date"], schema="master")
    op.create_index("limits_violations_contract_idx", "limits_violations", ["contract_id", "violation_date"], schema="master")
    op.create_index("limits_violations_type_idx", "limits_violations", ["violation_type"], schema="master")

    op.create_index("alerts_log_triggered_idx", "alerts_log", ["triggered_at"], schema="master")
    op.create_index("alerts_log_status_idx", "alerts_log", ["delivery_status"], schema="master")
    op.create_index("alerts_log_config_idx", "alerts_log", ["alert_config_id", "triggered_at"], schema="master")

    # Create PostgreSQL functions for limits checking
    op.execute("""
        CREATE OR REPLACE FUNCTION master.check_authorization_limits(
            p_authorization_id BIGINT,
            p_sessions_to_use INTEGER DEFAULT 1,
            p_execution_date DATE DEFAULT CURRENT_DATE
        ) RETURNS JSON AS $$
        DECLARE
            auth_record RECORD;
            usage_count INTEGER;
            remaining_sessions INTEGER;
            limit_violations JSON := '[]'::JSON;
            violation_record JSON;
        BEGIN
            -- Get authorization details
            SELECT * INTO auth_record
            FROM master.medical_authorizations
            WHERE id = p_authorization_id AND status = 'active';

            IF NOT FOUND THEN
                RETURN json_build_object(
                    'valid', false,
                    'reason', 'Authorization not found or not active',
                    'violations', '[]'::JSON
                );
            END IF;

            -- Check if authorization is within valid period
            IF p_execution_date < auth_record.valid_from OR p_execution_date > auth_record.valid_until THEN
                RETURN json_build_object(
                    'valid', false,
                    'reason', 'Authorization not valid for this date',
                    'violations', '[]'::JSON
                );
            END IF;

            -- Check total sessions remaining
            IF auth_record.sessions_remaining IS NOT NULL THEN
                IF auth_record.sessions_remaining < p_sessions_to_use THEN
                    RETURN json_build_object(
                        'valid', false,
                        'reason', 'Insufficient sessions remaining',
                        'sessions_remaining', auth_record.sessions_remaining,
                        'sessions_requested', p_sessions_to_use,
                        'violations', '[]'::JSON
                    );
                END IF;
            END IF;

            -- Check daily limit
            IF auth_record.daily_limit IS NOT NULL THEN
                SELECT COALESCE(SUM(sessions_used), 0) INTO usage_count
                FROM master.service_usage_tracking
                WHERE authorization_id = p_authorization_id
                  AND execution_date = p_execution_date
                  AND status = 'completed';

                IF usage_count + p_sessions_to_use > auth_record.daily_limit THEN
                    violation_record := json_build_object(
                        'type', 'DAILY_LIMIT_EXCEEDED',
                        'limit', auth_record.daily_limit,
                        'current_usage', usage_count,
                        'requested', p_sessions_to_use
                    );
                    limit_violations := limit_violations || violation_record::JSON;
                END IF;
            END IF;

            -- Check weekly limit
            IF auth_record.weekly_limit IS NOT NULL THEN
                SELECT COALESCE(SUM(sessions_used), 0) INTO usage_count
                FROM master.service_usage_tracking
                WHERE authorization_id = p_authorization_id
                  AND execution_date >= p_execution_date - INTERVAL '6 days'
                  AND execution_date <= p_execution_date
                  AND status = 'completed';

                IF usage_count + p_sessions_to_use > auth_record.weekly_limit THEN
                    violation_record := json_build_object(
                        'type', 'WEEKLY_LIMIT_EXCEEDED',
                        'limit', auth_record.weekly_limit,
                        'current_usage', usage_count,
                        'requested', p_sessions_to_use
                    );
                    limit_violations := limit_violations || violation_record::JSON;
                END IF;
            END IF;

            -- Check monthly limit
            IF auth_record.monthly_limit IS NOT NULL THEN
                SELECT COALESCE(SUM(sessions_used), 0) INTO usage_count
                FROM master.service_usage_tracking
                WHERE authorization_id = p_authorization_id
                  AND DATE_TRUNC('month', execution_date) = DATE_TRUNC('month', p_execution_date)
                  AND status = 'completed';

                IF usage_count + p_sessions_to_use > auth_record.monthly_limit THEN
                    violation_record := json_build_object(
                        'type', 'MONTHLY_LIMIT_EXCEEDED',
                        'limit', auth_record.monthly_limit,
                        'current_usage', usage_count,
                        'requested', p_sessions_to_use
                    );
                    limit_violations := limit_violations || violation_record::JSON;
                END IF;
            END IF;

            -- Return result
            RETURN json_build_object(
                'valid', json_array_length(limit_violations) = 0,
                'authorization_id', p_authorization_id,
                'sessions_remaining', auth_record.sessions_remaining,
                'violations', limit_violations
            );
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create function for automatic limits monitoring
    op.execute("""
        CREATE OR REPLACE FUNCTION master.monitor_contract_limits(
            p_contract_id BIGINT DEFAULT NULL,
            p_check_date DATE DEFAULT CURRENT_DATE
        ) RETURNS JSON AS $$
        DECLARE
            limit_rule RECORD;
            usage_amount NUMERIC;
            percentage_used NUMERIC;
            violation_id BIGINT;
            result_array JSON := '[]'::JSON;
            result_item JSON;
        BEGIN
            -- Loop through all active limit rules
            FOR limit_rule IN
                SELECT * FROM master.limits_configuration
                WHERE is_active = true
                  AND valid_from <= p_check_date
                  AND (valid_until IS NULL OR valid_until >= p_check_date)
                  AND (contract_id = p_contract_id OR p_contract_id IS NULL)
                ORDER BY priority ASC
            LOOP
                usage_amount := 0;

                -- Calculate current usage based on rule type and scope
                IF limit_rule.rule_type = 'SESSION' THEN
                    IF limit_rule.limit_scope = 'DAILY' THEN
                        SELECT COALESCE(SUM(sut.sessions_used), 0) INTO usage_amount
                        FROM master.service_usage_tracking sut
                        JOIN master.medical_authorizations ma ON sut.authorization_id = ma.id
                        JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
                        WHERE cl.contract_id = COALESCE(limit_rule.contract_id, cl.contract_id)
                          AND sut.execution_date = p_check_date
                          AND sut.status = 'completed'
                          AND (limit_rule.service_id IS NULL OR ma.service_id = limit_rule.service_id);

                    ELSIF limit_rule.limit_scope = 'WEEKLY' THEN
                        SELECT COALESCE(SUM(sut.sessions_used), 0) INTO usage_amount
                        FROM master.service_usage_tracking sut
                        JOIN master.medical_authorizations ma ON sut.authorization_id = ma.id
                        JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
                        WHERE cl.contract_id = COALESCE(limit_rule.contract_id, cl.contract_id)
                          AND sut.execution_date >= p_check_date - INTERVAL '6 days'
                          AND sut.execution_date <= p_check_date
                          AND sut.status = 'completed'
                          AND (limit_rule.service_id IS NULL OR ma.service_id = limit_rule.service_id);

                    ELSIF limit_rule.limit_scope = 'MONTHLY' THEN
                        SELECT COALESCE(SUM(sut.sessions_used), 0) INTO usage_amount
                        FROM master.service_usage_tracking sut
                        JOIN master.medical_authorizations ma ON sut.authorization_id = ma.id
                        JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
                        WHERE cl.contract_id = COALESCE(limit_rule.contract_id, cl.contract_id)
                          AND DATE_TRUNC('month', sut.execution_date) = DATE_TRUNC('month', p_check_date)
                          AND sut.status = 'completed'
                          AND (limit_rule.service_id IS NULL OR ma.service_id = limit_rule.service_id);
                    END IF;

                ELSIF limit_rule.rule_type = 'FINANCIAL' THEN
                    -- Similar logic for financial limits using value_charged
                    SELECT COALESCE(SUM(sut.value_charged), 0) INTO usage_amount
                    FROM master.service_usage_tracking sut
                    JOIN master.medical_authorizations ma ON sut.authorization_id = ma.id
                    JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
                    WHERE cl.contract_id = COALESCE(limit_rule.contract_id, cl.contract_id)
                      AND CASE
                        WHEN limit_rule.limit_scope = 'DAILY' THEN sut.execution_date = p_check_date
                        WHEN limit_rule.limit_scope = 'WEEKLY' THEN sut.execution_date >= p_check_date - INTERVAL '6 days' AND sut.execution_date <= p_check_date
                        WHEN limit_rule.limit_scope = 'MONTHLY' THEN DATE_TRUNC('month', sut.execution_date) = DATE_TRUNC('month', p_check_date)
                        ELSE true
                      END
                      AND sut.status = 'completed'
                      AND (limit_rule.service_id IS NULL OR ma.service_id = limit_rule.service_id);
                END IF;

                -- Calculate percentage used
                percentage_used := CASE
                    WHEN limit_rule.limit_value > 0 THEN usage_amount / limit_rule.limit_value
                    ELSE 0
                END;

                -- Check for violations
                IF percentage_used >= limit_rule.alert_threshold THEN
                    -- Insert violation record
                    INSERT INTO master.limits_violations (
                        limit_rule_id, contract_id, violation_type, current_usage,
                        limit_value, percentage_used, period_start, period_end,
                        auto_action_taken
                    ) VALUES (
                        limit_rule.id,
                        limit_rule.contract_id,
                        CASE
                            WHEN percentage_used >= 1.0 THEN 'EXCEEDED'
                            WHEN percentage_used >= limit_rule.alert_threshold THEN 'ALERT'
                            ELSE 'WARNING'
                        END,
                        usage_amount,
                        limit_rule.limit_value,
                        percentage_used,
                        CASE
                            WHEN limit_rule.limit_scope = 'DAILY' THEN p_check_date
                            WHEN limit_rule.limit_scope = 'WEEKLY' THEN p_check_date - INTERVAL '6 days'
                            WHEN limit_rule.limit_scope = 'MONTHLY' THEN DATE_TRUNC('month', p_check_date)::DATE
                            ELSE p_check_date
                        END,
                        p_check_date,
                        CASE
                            WHEN percentage_used >= 1.0 AND limit_rule.auto_block THEN 'AUTO_BLOCKED'
                            ELSE 'ALERT_GENERATED'
                        END
                    ) RETURNING id INTO violation_id;

                    -- Add to result
                    result_item := json_build_object(
                        'rule_id', limit_rule.id,
                        'rule_name', limit_rule.rule_name,
                        'violation_id', violation_id,
                        'usage_amount', usage_amount,
                        'limit_value', limit_rule.limit_value,
                        'percentage_used', percentage_used,
                        'violation_type', CASE
                            WHEN percentage_used >= 1.0 THEN 'EXCEEDED'
                            WHEN percentage_used >= limit_rule.alert_threshold THEN 'ALERT'
                            ELSE 'WARNING'
                        END
                    );

                    result_array := result_array || result_item::JSON;
                END IF;
            END LOOP;

            RETURN json_build_object(
                'check_date', p_check_date,
                'violations_found', json_array_length(result_array),
                'violations', result_array
            );
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Insert default limit rules
    op.execute("""
        INSERT INTO master.limits_configuration (
            rule_name, rule_type, limit_scope, limit_value, warning_threshold,
            alert_threshold, auto_block, override_allowed, priority, is_active, valid_from, description,
            created_at, updated_at, created_by, updated_by
        ) VALUES
        -- Global session limits
        ('Limite Global Diário de Sessões', 'SESSION', 'DAILY', 10, 0.8, 0.9, false, false, 10, true, CURRENT_DATE,
         'Limite máximo de 10 sessões por dia por contrato', NOW(), NOW(), 1, 1),
        ('Limite Global Semanal de Sessões', 'SESSION', 'WEEKLY', 50, 0.8, 0.9, false, true, 20, true, CURRENT_DATE,
         'Limite máximo de 50 sessões por semana por contrato', NOW(), NOW(), 1, 1),
        ('Limite Global Mensal de Sessões', 'SESSION', 'MONTHLY', 200, 0.8, 0.9, false, true, 30, true, CURRENT_DATE,
         'Limite máximo de 200 sessões por mês por contrato', NOW(), NOW(), 1, 1),

        -- Global financial limits
        ('Limite Global Diário Financeiro', 'FINANCIAL', 'DAILY', 5000.00, 0.8, 0.9, false, true, 40, true, CURRENT_DATE,
         'Limite máximo de R$ 5.000 por dia por contrato', NOW(), NOW(), 1, 1),
        ('Limite Global Mensal Financeiro', 'FINANCIAL', 'MONTHLY', 100000.00, 0.8, 0.9, true, false, 50, true, CURRENT_DATE,
         'Limite máximo de R$ 100.000 por mês por contrato', NOW(), NOW(), 1, 1);
    """)

    # Insert default alert configurations
    op.execute("""
        INSERT INTO master.alerts_configuration (
            alert_name, alert_type, trigger_condition, notification_channels,
            recipients, message_template, frequency_limit, is_active, priority,
            created_at, updated_at, created_by, updated_by
        ) VALUES
        ('Alerta de Limite de Sessões', 'LIMIT_WARNING',
         '{"rule_type": "SESSION", "threshold": "warning"}',
         '["email", "system"]',
         '{"user_roles": ["admin", "manager"], "emails": []}',
         'Atenção: O limite de sessões está próximo de ser atingido. Uso atual: {usage_amount}/{limit_value} ({percentage_used}%)',
         'HOURLY', true, 100, NOW(), NOW(), 1, 1),

        ('Alerta de Limite Financeiro Excedido', 'LIMIT_EXCEEDED',
         '{"rule_type": "FINANCIAL", "threshold": "exceeded"}',
         '["email", "sms", "system"]',
         '{"user_roles": ["admin"], "emails": ["admin@proteamcare.com"]}',
         'CRÍTICO: Limite financeiro excedido! Contrato bloqueado. Uso atual: R$ {usage_amount} / Limite: R$ {limit_value}',
         'IMMEDIATE', true, 10, NOW(), NOW(), 1, 1);
    """)


def downgrade():
    """Remove automatic limits control system"""

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS master.monitor_contract_limits(BIGINT, DATE);")
    op.execute("DROP FUNCTION IF EXISTS master.check_authorization_limits(BIGINT, INTEGER, DATE);")

    # Drop tables in reverse order
    op.drop_table("alerts_log", schema="master")
    op.drop_table("alerts_configuration", schema="master")
    op.drop_table("limits_violations", schema="master")
    op.drop_table("limits_configuration", schema="master")
    op.drop_table("service_usage_tracking", schema="master")