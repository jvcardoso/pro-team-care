-- Script para criar assinatura de teste para Empresa Teste LTDA
-- Executa: PGPASSWORD=Jvc@1702 psql -h 192.168.11.62 -U postgres -d pro_team_care_11 -f create_test_subscription.sql

BEGIN;

-- Criar assinatura de teste para a Empresa Teste LTDA (ID: 57)
INSERT INTO master.company_subscriptions (
    company_id,
    plan_id,
    status,
    start_date,
    billing_day,
    payment_method,
    auto_renew,
    created_at
) VALUES (
    57,                     -- company_id (Empresa Teste LTDA)
    2,                      -- plan_id (Premium)
    'active',               -- status
    CURRENT_DATE,           -- start_date
    5,                      -- billing_day (dia 5)
    'manual',               -- payment_method
    true,                   -- auto_renew
    CURRENT_TIMESTAMP       -- created_at
);

-- Criar uma fatura de exemplo (atual)
WITH subscription AS (
    SELECT id FROM master.company_subscriptions WHERE company_id = 57 LIMIT 1
),
invoice_number AS (
    SELECT 'PTC-' || EXTRACT(YEAR FROM CURRENT_DATE) || '-' ||
           LPAD(EXTRACT(MONTH FROM CURRENT_DATE)::text, 2, '0') || '-' ||
           LPAD('57', 4, '0') || '-001' AS number
)
INSERT INTO master.proteamcare_invoices (
    company_id,
    subscription_id,
    invoice_number,
    amount,
    billing_period_start,
    billing_period_end,
    due_date,
    status,
    payment_method,
    created_at
)
SELECT
    57,
    subscription.id,
    invoice_number.number,
    599.00,                                    -- valor do plano Premium
    DATE_TRUNC('month', CURRENT_DATE),         -- início do período
    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day', -- fim do período
    CURRENT_DATE + INTERVAL '10 days',        -- vencimento em 10 dias
    'pending',                                 -- status
    'manual',                                  -- payment_method
    CURRENT_TIMESTAMP
FROM subscription, invoice_number;

-- Criar uma fatura vencida (para teste de alertas)
WITH subscription AS (
    SELECT id FROM master.company_subscriptions WHERE company_id = 57 LIMIT 1
),
invoice_number AS (
    SELECT 'PTC-' || EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 month') || '-' ||
           LPAD(EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month')::text, 2, '0') || '-' ||
           LPAD('57', 4, '0') || '-001' AS number
)
INSERT INTO master.proteamcare_invoices (
    company_id,
    subscription_id,
    invoice_number,
    amount,
    billing_period_start,
    billing_period_end,
    due_date,
    status,
    payment_method,
    created_at
)
SELECT
    57,
    subscription.id,
    invoice_number.number,
    599.00,                                    -- valor do plano Premium
    DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month'), -- mês passado
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 day',   -- fim do mês passado
    CURRENT_DATE - INTERVAL '5 days',         -- venceu há 5 dias
    'pending',                                 -- status (vencida)
    'manual',                                  -- payment_method
    CURRENT_TIMESTAMP
FROM subscription, invoice_number
WHERE NOT EXISTS (
    SELECT 1 FROM master.proteamcare_invoices WHERE invoice_number = invoice_number.number
);

-- Verificar resultado
SELECT
    'Assinatura criada com sucesso!' AS resultado,
    c.id AS company_id,
    p.name AS company_name,
    cs.id AS subscription_id,
    sp.name AS plan_name,
    sp.monthly_price,
    cs.status,
    cs.start_date,
    cs.billing_day
FROM master.company_subscriptions cs
JOIN master.companies c ON cs.company_id = c.id
JOIN master.people p ON c.person_id = p.id
JOIN master.subscription_plans sp ON cs.plan_id = sp.id
WHERE cs.company_id = 57;

-- Verificar faturas criadas
SELECT
    'Faturas de teste:' AS tipo,
    invoice_number,
    amount,
    due_date,
    status,
    CASE
        WHEN due_date < CURRENT_DATE AND status = 'pending' THEN 'VENCIDA'
        WHEN due_date >= CURRENT_DATE AND status = 'pending' THEN 'PENDENTE'
        ELSE status
    END AS situacao
FROM master.proteamcare_invoices
WHERE company_id = 57
ORDER BY due_date;

COMMIT;

-- Mensagem final
SELECT
    '🎉 Dados de teste criados com sucesso!' AS resultado,
    'Empresa Teste LTDA agora tem uma assinatura Premium ativa' AS detalhes,
    'Verifique a aba Faturamento na página da empresa' AS instrucao;