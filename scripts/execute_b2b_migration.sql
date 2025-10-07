-- Migração B2B para criação das tabelas de faturamento
-- Executa: PGPASSWORD=Jvc@1702 psql -h 192.168.11.62 -U postgres -d pro_team_care_11 -f execute_b2b_migration.sql

BEGIN;

-- Create subscription plans table
CREATE TABLE IF NOT EXISTS master.subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    monthly_price NUMERIC(10, 2) NOT NULL,
    features JSONB,
    max_users INTEGER,
    max_establishments INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Create company subscriptions table
CREATE TABLE IF NOT EXISTS master.company_subscriptions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES master.companies(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES master.subscription_plans(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'suspended', 'expired')),
    start_date DATE NOT NULL,
    end_date DATE,
    billing_day INTEGER NOT NULL DEFAULT 1 CHECK (billing_day >= 1 AND billing_day <= 31),
    payment_method VARCHAR(20) NOT NULL DEFAULT 'manual' CHECK (payment_method IN ('manual', 'recurrent')),
    pagbank_subscription_id VARCHAR(100),
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Create Pro Team Care invoices table
CREATE TABLE IF NOT EXISTS master.proteamcare_invoices (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES master.companies(id) ON DELETE CASCADE,
    subscription_id INTEGER NOT NULL REFERENCES master.company_subscriptions(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled')),
    payment_method VARCHAR(20) NOT NULL DEFAULT 'manual' CHECK (payment_method IN ('manual', 'recurrent')),
    paid_at TIMESTAMP,
    pagbank_checkout_url TEXT,
    pagbank_session_id VARCHAR(100),
    pagbank_transaction_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subscription_plans_name ON master.subscription_plans(name);
CREATE INDEX IF NOT EXISTS idx_subscription_plans_is_active ON master.subscription_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_company_id ON master.company_subscriptions(company_id);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_plan_id ON master.company_subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_status ON master.company_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_payment_method ON master.company_subscriptions(payment_method);
CREATE INDEX IF NOT EXISTS idx_proteamcare_invoices_company_id ON master.proteamcare_invoices(company_id);
CREATE INDEX IF NOT EXISTS idx_proteamcare_invoices_subscription_id ON master.proteamcare_invoices(subscription_id);
CREATE INDEX IF NOT EXISTS idx_proteamcare_invoices_status ON master.proteamcare_invoices(status);
CREATE INDEX IF NOT EXISTS idx_proteamcare_invoices_due_date ON master.proteamcare_invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_proteamcare_invoices_invoice_number ON master.proteamcare_invoices(invoice_number);

-- Insert default subscription plans (apenas se não existirem)
INSERT INTO master.subscription_plans (name, description, monthly_price, features, max_users, max_establishments)
SELECT 'Básico', 'Plano ideal para clínicas pequenas', 299.00, '{"reports": "basic", "support": "email", "integrations": "limited"}', 5, 1
WHERE NOT EXISTS (SELECT 1 FROM master.subscription_plans WHERE name = 'Básico');

INSERT INTO master.subscription_plans (name, description, monthly_price, features, max_users, max_establishments)
SELECT 'Premium', 'Para clínicas de médio porte', 599.00, '{"reports": "advanced", "support": "priority", "integrations": "full", "analytics": true}', 15, 3
WHERE NOT EXISTS (SELECT 1 FROM master.subscription_plans WHERE name = 'Premium');

INSERT INTO master.subscription_plans (name, description, monthly_price, features, max_users, max_establishments)
SELECT 'Enterprise', 'Solução completa para grandes redes', 1200.00, '{"reports": "premium", "support": "dedicated", "integrations": "unlimited", "analytics": true, "custom_features": true}', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM master.subscription_plans WHERE name = 'Enterprise');

-- Verificar tabelas criadas
SELECT
    'Tabelas B2B criadas:' AS status,
    COUNT(*) AS total_tables
FROM information_schema.tables
WHERE table_schema = 'master'
AND table_name IN ('subscription_plans', 'company_subscriptions', 'proteamcare_invoices');

-- Verificar planos inseridos
SELECT
    'Planos disponíveis:' AS status,
    id,
    name,
    monthly_price,
    max_users,
    max_establishments,
    is_active
FROM master.subscription_plans
ORDER BY monthly_price;

COMMIT;

-- Mensagem de sucesso
SELECT
    '🎉 Migração B2B executada com sucesso!' AS resultado,
    'Tabelas criadas: subscription_plans, company_subscriptions, proteamcare_invoices' AS detalhes,
    '3 planos padrão inseridos: Básico, Premium, Enterprise' AS planos;
