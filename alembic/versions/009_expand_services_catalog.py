"""Expand services catalog with specialized home care services

Revision ID: 009_expand_services_catalog
Revises: 008_create_contract_tables
Create Date: 2025-09-18 21:10:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "009_expand_services_catalog"
down_revision = "008_create_contract_tables"
branch_labels = None
depends_on = None


def upgrade():
    """Add comprehensive home care services catalog"""

    # First, update the check constraint to allow new categories
    op.execute(
        """
        ALTER TABLE master.services_catalog
        DROP CONSTRAINT IF EXISTS services_catalog_category_check;
    """
    )

    op.execute(
        """
        ALTER TABLE master.services_catalog
        ADD CONSTRAINT services_catalog_category_check
        CHECK (service_category IN (
            'ENFERMAGEM', 'FISIOTERAPIA', 'MEDICINA', 'EQUIPAMENTO',
            'NUTRIÇÃO', 'PSICOLOGIA', 'TERAPIA_OCUPACIONAL',
            'FONOAUDIOLOGIA', 'TERAPIA_RESPIRATORIA', 'CUIDADOS'
        ));
    """
    )

    # Also update service_type constraint
    op.execute(
        """
        ALTER TABLE master.services_catalog
        DROP CONSTRAINT IF EXISTS services_catalog_type_check;
    """
    )

    op.execute(
        """
        ALTER TABLE master.services_catalog
        ADD CONSTRAINT services_catalog_type_check
        CHECK (service_type IN (
            'PROCEDIMENTO', 'CONSULTA', 'EXAME', 'TERAPIA',
            'LOCAÇÃO', 'ASSISTENCIA'
        ));
    """
    )

    # Add more specialized services to the catalog
    op.execute(
        """
        INSERT INTO master.services_catalog (service_code, service_name, service_category, service_type, requires_prescription, home_visit_required, default_unit_value, description, created_at, updated_at) VALUES
        -- ENFERMAGEM ESPECIALIZADA
        ('ENF004', 'Sondagem Vesical', 'ENFERMAGEM', 'PROCEDIMENTO', true, true, 95.00, 'Passagem e manutenção de sonda vesical de demora', now(), now()),
        ('ENF005', 'Sondagem Nasoenteral', 'ENFERMAGEM', 'PROCEDIMENTO', true, true, 110.00, 'Passagem de sonda nasoenteral para alimentação', now(), now()),
        ('ENF006', 'Curativo Complexo', 'ENFERMAGEM', 'PROCEDIMENTO', true, true, 85.00, 'Curativo em feridas complexas ou cirúrgicas', now(), now()),
        ('ENF007', 'Administração de Quimioterapia', 'ENFERMAGEM', 'PROCEDIMENTO', true, true, 350.00, 'Administração de quimioterápicos em domicílio', now(), now()),
        ('ENF008', 'Oxigenoterapia', 'ENFERMAGEM', 'TERAPIA', true, true, 75.00, 'Administração e monitoramento de oxigenoterapia', now(), now()),
        ('ENF009', 'Aspiração de Vias Aéreas', 'ENFERMAGEM', 'PROCEDIMENTO', false, true, 65.00, 'Aspiração de secreções das vias aéreas', now(), now()),
        ('ENF010', 'Cuidados com Traqueostomia', 'ENFERMAGEM', 'PROCEDIMENTO', false, true, 90.00, 'Higienização e troca de cânula de traqueostomia', now(), now()),

        -- FISIOTERAPIA ESPECIALIZADA
        ('FIS002', 'Fisioterapia Respiratória', 'FISIOTERAPIA', 'TERAPIA', true, true, 130.00, 'Fisioterapia respiratória domiciliar', now(), now()),
        ('FIS003', 'Fisioterapia Neurológica', 'FISIOTERAPIA', 'TERAPIA', true, true, 140.00, 'Reabilitação neurológica em domicílio', now(), now()),
        ('FIS004', 'Fisioterapia Ortopédica', 'FISIOTERAPIA', 'TERAPIA', true, true, 125.00, 'Reabilitação ortopédica e traumatológica', now(), now()),
        ('FIS005', 'Fisioterapia Pediátrica', 'FISIOTERAPIA', 'TERAPIA', true, true, 150.00, 'Fisioterapia especializada para crianças', now(), now()),
        ('FIS006', 'Fisioterapia Geriátrica', 'FISIOTERAPIA', 'TERAPIA', false, true, 120.00, 'Fisioterapia especializada para idosos', now(), now()),

        -- MEDICINA ESPECIALIZADA
        ('MED002', 'Consulta Cardiológica', 'MEDICINA', 'CONSULTA', false, true, 300.00, 'Consulta cardiológica domiciliar', now(), now()),
        ('MED003', 'Consulta Neurológica', 'MEDICINA', 'CONSULTA', false, true, 350.00, 'Consulta neurológica domiciliar', now(), now()),
        ('MED004', 'Consulta Geriátrica', 'MEDICINA', 'CONSULTA', false, true, 280.00, 'Consulta geriátrica especializada', now(), now()),
        ('MED005', 'Consulta Pediátrica', 'MEDICINA', 'CONSULTA', false, true, 270.00, 'Consulta pediátrica domiciliar', now(), now()),
        ('MED006', 'Consulta Psiquiátrica', 'MEDICINA', 'CONSULTA', false, true, 320.00, 'Consulta psiquiátrica domiciliar', now(), now()),

        -- EXAMES E DIAGNÓSTICOS
        ('EXM001', 'Eletrocardiograma', 'MEDICINA', 'EXAME', false, true, 80.00, 'Realização de ECG em domicílio', now(), now()),
        ('EXM002', 'Holter 24h', 'MEDICINA', 'EXAME', false, true, 200.00, 'Monitorização cardíaca de 24 horas', now(), now()),
        ('EXM003', 'Ecocardiograma', 'MEDICINA', 'EXAME', false, true, 180.00, 'Ecocardiograma domiciliar', now(), now()),
        ('EXM004', 'Ultrassom Abdominal', 'MEDICINA', 'EXAME', false, true, 150.00, 'Ultrassonografia abdominal em domicílio', now(), now()),
        ('EXM005', 'Raio-X Portátil', 'MEDICINA', 'EXAME', false, true, 120.00, 'Radiografia portátil domiciliar', now(), now()),

        -- EQUIPAMENTOS ESPECIALIZADOS
        ('EQP002', 'Concentrador de Oxigênio', 'EQUIPAMENTO', 'LOCAÇÃO', false, false, 450.00, 'Locação mensal de concentrador de oxigênio', now(), now()),
        ('EQP003', 'BIPAP/CPAP', 'EQUIPAMENTO', 'LOCAÇÃO', true, false, 800.00, 'Locação mensal de equipamento de ventilação', now(), now()),
        ('EQP004', 'Cadeira de Rodas', 'EQUIPAMENTO', 'LOCAÇÃO', false, false, 200.00, 'Locação mensal de cadeira de rodas', now(), now()),
        ('EQP005', 'Andador', 'EQUIPAMENTO', 'LOCAÇÃO', false, false, 150.00, 'Locação mensal de andador', now(), now()),
        ('EQP006', 'Bomba de Infusão', 'EQUIPAMENTO', 'LOCAÇÃO', true, false, 600.00, 'Locação mensal de bomba de infusão', now(), now()),
        ('EQP007', 'Monitor Multiparâmetros', 'EQUIPAMENTO', 'LOCAÇÃO', false, false, 750.00, 'Locação mensal de monitor de sinais vitais', now(), now()),

        -- TERAPIAS ESPECIALIZADAS
        ('TER001', 'Terapia Ocupacional', 'TERAPIA_OCUPACIONAL', 'TERAPIA', true, true, 140.00, 'Sessão de terapia ocupacional domiciliar', now(), now()),
        ('TER002', 'Fonoaudiologia', 'FONOAUDIOLOGIA', 'TERAPIA', true, true, 130.00, 'Sessão de fonoaudiologia domiciliar', now(), now()),
        ('TER003', 'Terapia Respiratória', 'TERAPIA_RESPIRATORIA', 'TERAPIA', true, true, 110.00, 'Terapia respiratória especializada', now(), now()),

        -- PSICOLOGIA ESPECIALIZADA
        ('PSI002', 'Neuropsicologia', 'PSICOLOGIA', 'CONSULTA', false, true, 150.00, 'Avaliação e reabilitação neuropsicológica', now(), now()),
        ('PSI003', 'Psicologia Infantil', 'PSICOLOGIA', 'CONSULTA', false, true, 130.00, 'Atendimento psicológico infantil', now(), now()),
        ('PSI004', 'Psicologia Geriátrica', 'PSICOLOGIA', 'CONSULTA', false, true, 140.00, 'Atendimento psicológico para idosos', now(), now()),

        -- NUTRIÇÃO ESPECIALIZADA
        ('NUT002', 'Nutrição Clínica', 'NUTRIÇÃO', 'CONSULTA', false, true, 160.00, 'Consulta de nutrição clínica especializada', now(), now()),
        ('NUT003', 'Nutrição Enteral', 'NUTRIÇÃO', 'PROCEDIMENTO', true, true, 180.00, 'Orientação e acompanhamento de nutrição enteral', now(), now()),
        ('NUT004', 'Nutrição Pediátrica', 'NUTRIÇÃO', 'CONSULTA', false, true, 170.00, 'Consulta nutricional pediátrica', now(), now()),

        -- CUIDADOS PALIATIVOS
        ('PAL001', 'Cuidados Paliativos Médicos', 'MEDICINA', 'CONSULTA', false, true, 400.00, 'Consulta médica em cuidados paliativos', now(), now()),
        ('PAL002', 'Cuidados Paliativos Enfermagem', 'ENFERMAGEM', 'PROCEDIMENTO', false, true, 200.00, 'Cuidados de enfermagem em cuidados paliativos', now(), now()),
        ('PAL003', 'Controle da Dor', 'MEDICINA', 'PROCEDIMENTO', true, true, 250.00, 'Manejo especializado da dor crônica', now(), now()),

        -- SERVIÇOS DE APOIO
        ('APO001', 'Cuidador Técnico', 'CUIDADOS', 'ASSISTENCIA', false, true, 25.00, 'Hora de cuidador técnico em enfermagem', now(), now()),
        ('APO002', 'Cuidador Social', 'CUIDADOS', 'ASSISTENCIA', false, true, 20.00, 'Hora de cuidador social/acompanhante', now(), now()),
        ('APO003', 'Auxiliar de Enfermagem', 'ENFERMAGEM', 'ASSISTENCIA', false, true, 30.00, 'Hora de auxiliar de enfermagem', now(), now());
    """
    )


def downgrade():
    """Remove expanded services from catalog"""

    # Remove the expanded services
    op.execute(
        """
        DELETE FROM master.services_catalog
        WHERE service_code IN (
            'ENF004', 'ENF005', 'ENF006', 'ENF007', 'ENF008', 'ENF009', 'ENF010',
            'FIS002', 'FIS003', 'FIS004', 'FIS005', 'FIS006',
            'MED002', 'MED003', 'MED004', 'MED005', 'MED006',
            'EXM001', 'EXM002', 'EXM003', 'EXM004', 'EXM005',
            'EQP002', 'EQP003', 'EQP004', 'EQP005', 'EQP006', 'EQP007',
            'TER001', 'TER002', 'TER003',
            'PSI002', 'PSI003', 'PSI004',
            'NUT002', 'NUT003', 'NUT004',
            'PAL001', 'PAL002', 'PAL003',
            'APO001', 'APO002', 'APO003'
        );
    """
    )
