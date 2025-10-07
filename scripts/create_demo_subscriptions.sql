-- Script para criar assinaturas de demonstração para outras empresas
-- Executa: PGPASSWORD=Jvc@1702 psql -h 192.168.11.62 -U postgres -d pro_team_care_11 -f create_demo_subscriptions.sql

BEGIN;

-- Empresa 58: FUNDACAO FACULDADE DE MEDICINA (Plano Enterprise)
INSERT INTO master.company_subscriptions (
    company_id, plan_id, status, start_date, billing_day, payment_method, auto_renew, created_at
) VALUES (
    58, 3, 'active', '2025-01-01', 1, 'manual', true, CURRENT_TIMESTAMP
);

-- Empresa 59: HOSPITAL ALBERT EINSTEIN (Plano Premium)
INSERT INTO master.company_subscriptions (
    company_id, plan_id, status, start_date, billing_day, payment_method, auto_renew, created_at
) VALUES (
    59, 2, 'active', '2025-02-15', 15, 'manual', true, CURRENT_TIMESTAMP
);

-- Empresa 60: FUND HCFMRPUSP (Plano Básico)
INSERT INTO master.company_subscriptions (
    company_id, plan_id, status, start_date, billing_day, payment_method, auto_renew, created_at
) VALUES (
    60, 1, 'active', '2025-03-01', 10, 'manual', true, CURRENT_TIMESTAMP
);

-- Empresa 61: UNICAMP (Plano Enterprise - SUSPENSA para demonstrar status)
INSERT INTO master.company_subscriptions (
    company_id, plan_id, status, start_date, billing_day, payment_method, auto_renew, created_at
) VALUES (
    61, 3, 'suspended', '2025-01-01', 20, 'manual', false, CURRENT_TIMESTAMP
);

-- Criar faturas diversas para demonstração

-- Hospital Einstein - Fatura paga
WITH subscription AS (SELECT id FROM master.company_subscriptions WHERE company_id = 59)
INSERT INTO master.proteamcare_invoices (
    company_id, subscription_id, invoice_number, amount,
    billing_period_start, billing_period_end, due_date,
    status, payment_method, paid_at, created_at
)
SELECT
    59, subscription.id, 'PTC-2025-09-0059-001', 599.00,
    '2025-09-01', '2025-09-30', '2025-09-15',
    'paid', 'manual', '2025-09-14 10:30:00', CURRENT_TIMESTAMP
FROM subscription;

-- HCFMRPUSP - Fatura pendente
WITH subscription AS (SELECT id FROM master.company_subscriptions WHERE company_id = 60)
INSERT INTO master.proteamcare_invoices (
    company_id, subscription_id, invoice_number, amount,
    billing_period_start, billing_period_end, due_date,
    status, payment_method, created_at
)
SELECT
    60, subscription.id, 'PTC-2025-09-0060-001', 299.00,
    '2025-09-01', '2025-09-30', CURRENT_DATE + INTERVAL '15 days',
    'pending', 'manual', CURRENT_TIMESTAMP
FROM subscription;

-- UNICAMP - Fatura vencida (por estar suspensa)
WITH subscription AS (SELECT id FROM master.company_subscriptions WHERE company_id = 61)
INSERT INTO master.proteamcare_invoices (
    company_id, subscription_id, invoice_number, amount,
    billing_period_start, billing_period_end, due_date,
    status, payment_method, created_at
)
SELECT
    61, subscription.id, 'PTC-2025-08-0061-001', 1200.00,
    '2025-08-01', '2025-08-31', '2025-08-20',
    'pending', 'manual', CURRENT_TIMESTAMP
FROM subscription;

-- Verificar resultado com resumo executivo
SELECT
    '📊 RESUMO EXECUTIVO B2B' AS tipo,
    COUNT(DISTINCT cs.company_id) AS total_empresas,
    SUM(sp.monthly_price) AS receita_mensal_total,
    COUNT(CASE WHEN cs.status = 'active' THEN 1 END) AS assinaturas_ativas,
    COUNT(CASE WHEN cs.status = 'suspended' THEN 1 END) AS assinaturas_suspensas
FROM master.company_subscriptions cs
JOIN master.subscription_plans sp ON cs.plan_id = sp.id;

-- Distribuição por planos
SELECT
    '📋 DISTRIBUIÇÃO POR PLANOS' AS tipo,
    sp.name AS plano,
    sp.monthly_price AS valor,
    COUNT(cs.id) AS total_assinaturas,
    COUNT(CASE WHEN cs.status = 'active' THEN 1 END) AS ativas
FROM master.subscription_plans sp
LEFT JOIN master.company_subscriptions cs ON sp.id = cs.plan_id
GROUP BY sp.id, sp.name, sp.monthly_price
ORDER BY sp.monthly_price;

-- Status de faturas
SELECT
    '💰 STATUS DE FATURAS' AS tipo,
    status,
    COUNT(*) AS quantidade,
    SUM(amount) AS valor_total
FROM master.proteamcare_invoices
GROUP BY status
ORDER BY status;

-- Empresas com suas assinaturas
SELECT
    '🏢 EMPRESAS CADASTRADAS' AS info,
    p.name AS empresa,
    sp.name AS plano,
    cs.status AS status_assinatura,
    sp.monthly_price AS valor_mensal,
    cs.billing_day AS dia_cobranca
FROM master.company_subscriptions cs
JOIN master.companies c ON cs.company_id = c.id
JOIN master.people p ON c.person_id = p.id
JOIN master.subscription_plans sp ON cs.plan_id = sp.id
ORDER BY sp.monthly_price DESC, p.name;

COMMIT;

-- Mensagem final
SELECT
    '🎉 Sistema B2B está pronto para demonstração!' AS resultado,
    '5 empresas com assinaturas configuradas' AS empresas,
    'Acesse: /admin/faturamento/b2b para o dashboard' AS dashboard,
    'Ou visite cada empresa individualmente na aba Faturamento' AS empresas_individuais;
