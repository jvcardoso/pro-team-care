"""Create medical authorizations system

Revision ID: 010_medical_authorizations
Revises: 009_expand_services_catalog
Create Date: 2025-09-18 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_medical_authorizations'
down_revision = '009_expand_services_catalog'
branch_labels = None
depends_on = None


def upgrade():
    """Create medical authorizations system"""

    # Create medical_authorizations table
    op.create_table(
        "medical_authorizations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_life_id", sa.BigInteger(), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("doctor_id", sa.BigInteger(), nullable=False),  # User ID of the doctor
        sa.Column("authorization_code", sa.String(length=50), nullable=False),
        sa.Column("authorization_date", sa.Date(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("sessions_authorized", sa.Integer()),  # Total sessions authorized
        sa.Column("sessions_remaining", sa.Integer()),   # Sessions left to use
        sa.Column("monthly_limit", sa.Integer()),        # Max sessions per month
        sa.Column("weekly_limit", sa.Integer()),         # Max sessions per week
        sa.Column("daily_limit", sa.Integer()),          # Max sessions per day
        sa.Column("medical_indication", sa.Text(), nullable=False),
        sa.Column("contraindications", sa.Text()),
        sa.Column("special_instructions", sa.Text()),
        sa.Column("urgency_level", sa.String(length=20), default="NORMAL"),
        sa.Column("requires_supervision", sa.Boolean(), default=False),
        sa.Column("supervision_notes", sa.Text()),
        sa.Column("diagnosis_cid", sa.String(length=10)),  # CID-10 code
        sa.Column("diagnosis_description", sa.Text()),
        sa.Column("treatment_goals", sa.Text()),
        sa.Column("expected_duration_days", sa.Integer()),
        sa.Column("renewal_allowed", sa.Boolean(), default=True),
        sa.Column("renewal_conditions", sa.Text()),
        sa.Column("status", sa.String(length=20), default="active"),
        sa.Column("cancellation_reason", sa.Text()),
        sa.Column("cancelled_at", sa.DateTime()),
        sa.Column("cancelled_by", sa.BigInteger()),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger()),
        sa.Column("updated_by", sa.BigInteger()),
        sa.CheckConstraint(
            "urgency_level IN ('URGENT', 'HIGH', 'NORMAL', 'LOW')",
            name="medical_authorizations_urgency_check",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'expired', 'cancelled', 'suspended')",
            name="medical_authorizations_status_check",
        ),
        sa.CheckConstraint(
            "valid_from <= valid_until",
            name="medical_authorizations_date_range_check",
        ),
        sa.CheckConstraint(
            "sessions_remaining <= sessions_authorized",
            name="medical_authorizations_sessions_check",
        ),
        sa.ForeignKeyConstraint(["contract_life_id"], ["master.contract_lives.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["master.services_catalog.id"]),
        sa.ForeignKeyConstraint(["doctor_id"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["cancelled_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["master.users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("authorization_code", name="medical_authorizations_code_unique"),
        schema="master",
    )

    # Create indexes for medical_authorizations
    op.create_index("medical_authorizations_contract_life_id_idx", "medical_authorizations", ["contract_life_id"], schema="master")
    op.create_index("medical_authorizations_service_id_idx", "medical_authorizations", ["service_id"], schema="master")
    op.create_index("medical_authorizations_doctor_id_idx", "medical_authorizations", ["doctor_id"], schema="master")
    op.create_index("medical_authorizations_status_idx", "medical_authorizations", ["status"], schema="master")
    op.create_index("medical_authorizations_date_range_idx", "medical_authorizations", ["valid_from", "valid_until"], schema="master")
    op.create_index("medical_authorizations_code_idx", "medical_authorizations", ["authorization_code"], schema="master")

    # Create authorization_renewals table for tracking renewals
    op.create_table(
        "authorization_renewals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("original_authorization_id", sa.BigInteger(), nullable=False),
        sa.Column("new_authorization_id", sa.BigInteger(), nullable=False),
        sa.Column("renewal_date", sa.Date(), nullable=False),
        sa.Column("renewal_reason", sa.Text()),
        sa.Column("changes_made", sa.Text()),  # JSON string of what changed
        sa.Column("approved_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(["original_authorization_id"], ["master.medical_authorizations.id"]),
        sa.ForeignKeyConstraint(["new_authorization_id"], ["master.medical_authorizations.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create authorization_history table for audit trail
    op.create_table(
        "authorization_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("authorization_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),  # created, updated, cancelled, expired, etc.
        sa.Column("field_changed", sa.String(length=100)),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("reason", sa.Text()),
        sa.Column("performed_by", sa.BigInteger(), nullable=False),
        sa.Column("performed_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("ip_address", sa.String(length=45)),
        sa.Column("user_agent", sa.Text()),
        sa.CheckConstraint(
            "action IN ('created', 'updated', 'cancelled', 'expired', 'suspended', 'renewed', 'sessions_updated')",
            name="authorization_history_action_check",
        ),
        sa.ForeignKeyConstraint(["authorization_id"], ["master.medical_authorizations.id"]),
        sa.ForeignKeyConstraint(["performed_by"], ["master.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="master",
    )

    # Create indexes for history tables
    op.create_index("authorization_renewals_original_idx", "authorization_renewals", ["original_authorization_id"], schema="master")
    op.create_index("authorization_renewals_new_idx", "authorization_renewals", ["new_authorization_id"], schema="master")
    op.create_index("authorization_history_authorization_idx", "authorization_history", ["authorization_id"], schema="master")
    op.create_index("authorization_history_action_idx", "authorization_history", ["action"], schema="master")
    op.create_index("authorization_history_date_idx", "authorization_history", ["performed_at"], schema="master")

    # Create function to automatically generate authorization codes
    op.execute("""
        CREATE OR REPLACE FUNCTION master.generate_authorization_code()
        RETURNS TEXT AS $$
        DECLARE
            new_code TEXT;
            counter INTEGER := 1;
        BEGIN
            -- Generate code in format: AUTH-YYYY-NNNNNN
            LOOP
                new_code := 'AUTH-' || EXTRACT(YEAR FROM CURRENT_DATE) || '-' || LPAD(counter::TEXT, 6, '0');

                -- Check if code already exists
                IF NOT EXISTS (SELECT 1 FROM master.medical_authorizations WHERE authorization_code = new_code) THEN
                    RETURN new_code;
                END IF;

                counter := counter + 1;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to auto-generate authorization codes
    op.execute("""
        CREATE OR REPLACE FUNCTION master.set_authorization_code()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.authorization_code IS NULL OR NEW.authorization_code = '' THEN
                NEW.authorization_code := master.generate_authorization_code();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_set_authorization_code
        BEFORE INSERT ON master.medical_authorizations
        FOR EACH ROW
        EXECUTE FUNCTION master.set_authorization_code();
    """)

    # Create trigger to update sessions_remaining when sessions are used
    op.execute("""
        CREATE OR REPLACE FUNCTION master.update_authorization_sessions()
        RETURNS TRIGGER AS $$
        BEGIN
            -- This will be called when a service execution is completed
            -- For now, we'll create the structure for future use
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create view for active authorizations
    op.execute("""
        CREATE VIEW master.active_medical_authorizations AS
        SELECT
            ma.*,
            sc.service_name,
            sc.service_category,
            sc.service_type,
            COALESCE(up.name, u.email_address) as doctor_name,
            u.email_address as doctor_email,
            cl.person_id,
            p.name as patient_name
        FROM master.medical_authorizations ma
        JOIN master.services_catalog sc ON ma.service_id = sc.id
        JOIN master.users u ON ma.doctor_id = u.id
        LEFT JOIN master.people up ON u.person_id = up.id
        JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
        JOIN master.people p ON cl.person_id = p.id
        WHERE ma.status = 'active'
          AND ma.valid_from <= CURRENT_DATE
          AND ma.valid_until >= CURRENT_DATE
          AND (ma.sessions_remaining IS NULL OR ma.sessions_remaining > 0);
    """)


def downgrade():
    """Remove medical authorizations system"""

    # Drop view
    op.execute("DROP VIEW IF EXISTS master.active_medical_authorizations;")

    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trigger_set_authorization_code ON master.medical_authorizations;")
    op.execute("DROP FUNCTION IF EXISTS master.set_authorization_code();")
    op.execute("DROP FUNCTION IF EXISTS master.update_authorization_sessions();")
    op.execute("DROP FUNCTION IF EXISTS master.generate_authorization_code();")

    # Drop tables in reverse order
    op.drop_table("authorization_history", schema="master")
    op.drop_table("authorization_renewals", schema="master")
    op.drop_table("medical_authorizations", schema="master")