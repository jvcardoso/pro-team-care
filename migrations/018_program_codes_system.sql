-- =====================================================
-- MIGRATION 018: Sistema de Códigos de Programas
-- =====================================================
-- Implementa sistema de navegação rápida estilo Datasul
-- Permite acesso via códigos curtos (ex: em0001, ct0001)
-- Suporta busca híbrida: código exato + busca por nome
-- =====================================================

-- Habilitar extensão para busca de similaridade
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- 1. ADICIONAR CAMPOS NA TABELA MENUS
-- =====================================================

ALTER TABLE master.menus
ADD COLUMN IF NOT EXISTS shortcode VARCHAR(10),
ADD COLUMN IF NOT EXISTS module_code VARCHAR(2),
ADD COLUMN IF NOT EXISTS program_type VARCHAR(2),
ADD COLUMN IF NOT EXISTS search_tokens TEXT[],
ADD COLUMN IF NOT EXISTS aliases JSONB DEFAULT '{}'::jsonb;

-- =====================================================
-- 2. CRIAR TABELA PROGRAM_CODES (Controle Centralizado)
-- =====================================================

CREATE TABLE IF NOT EXISTS master.program_codes (
    id SERIAL PRIMARY KEY,

    -- Identificação
    shortcode VARCHAR(10) UNIQUE NOT NULL,
    module_code VARCHAR(2) NOT NULL,
    program_type VARCHAR(2) NOT NULL,

    -- Relacionamento
    menu_id INTEGER REFERENCES master.menus(id) ON DELETE SET NULL,

    -- Informações
    label VARCHAR(100) NOT NULL,
    description TEXT,
    route VARCHAR(255) NOT NULL,
    icon VARCHAR(50),

    -- Busca
    search_tokens TEXT[] NOT NULL DEFAULT '{}',
    aliases JSONB DEFAULT '{}'::jsonb,

    -- Analytics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES master.users(id),
    is_active BOOLEAN DEFAULT TRUE,

    -- Permissões (opcional - para cache)
    required_permission VARCHAR(100)
);

-- =====================================================
-- 3. ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índice único para códigos
CREATE UNIQUE INDEX IF NOT EXISTS idx_program_codes_shortcode
ON master.program_codes(shortcode)
WHERE is_active = TRUE;

-- Índice para módulo
CREATE INDEX IF NOT EXISTS idx_program_codes_module
ON master.program_codes(module_code);

-- Índice para tipo
CREATE INDEX IF NOT EXISTS idx_program_codes_type
ON master.program_codes(program_type);

-- Índice para rota
CREATE INDEX IF NOT EXISTS idx_program_codes_route
ON master.program_codes(route);

-- Índice GIN para search_tokens (busca em arrays)
CREATE INDEX IF NOT EXISTS idx_program_codes_tokens
ON master.program_codes USING gin(search_tokens);

-- Índice GIN para busca de similaridade no label
CREATE INDEX IF NOT EXISTS idx_program_codes_label_trgm
ON master.program_codes USING gin(label gin_trgm_ops);

-- Índice para menu_id
CREATE INDEX IF NOT EXISTS idx_program_codes_menu_id
ON master.program_codes(menu_id);

-- Índice para usage analytics
CREATE INDEX IF NOT EXISTS idx_program_codes_usage
ON master.program_codes(usage_count DESC, last_used_at DESC);

-- =====================================================
-- 4. COMENTÁRIOS
-- =====================================================

COMMENT ON TABLE master.program_codes IS 'Códigos de programas estilo Datasul para navegação rápida via Ctrl+Alt+X';
COMMENT ON COLUMN master.program_codes.shortcode IS 'Código curto único (ex: em0001, ct0001) - lowercase obrigatório';
COMMENT ON COLUMN master.program_codes.module_code IS 'Sigla do módulo (2 chars): EM, ES, US, CL, CT, etc';
COMMENT ON COLUMN master.program_codes.program_type IS 'Tipo de programa (2 digits): 00=cadastro, 20=consulta, 50=relatório, etc';
COMMENT ON COLUMN master.program_codes.search_tokens IS 'Tokens para busca: [empresa, company, cadastro, firmas]';
COMMENT ON COLUMN master.program_codes.aliases IS 'Aliases JSON: {"old_code": "cad001", "datasul_eq": "EST001"}';
COMMENT ON COLUMN master.program_codes.usage_count IS 'Contador de acessos para analytics';
COMMENT ON COLUMN master.program_codes.required_permission IS 'Permissão necessária (cache de validação)';

-- Comentários nos índices
COMMENT ON INDEX idx_program_codes_shortcode IS 'Busca rápida por código exato (O(log n))';
COMMENT ON INDEX idx_program_codes_tokens IS 'Busca em tokens via GIN array operator';
COMMENT ON INDEX idx_program_codes_label_trgm IS 'Busca fuzzy por similaridade usando pg_trgm';

-- =====================================================
-- 5. FUNÇÃO DE ATUALIZAÇÃO DE TIMESTAMP
-- =====================================================

CREATE OR REPLACE FUNCTION update_program_codes_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_program_codes_timestamp
BEFORE UPDATE ON master.program_codes
FOR EACH ROW
EXECUTE FUNCTION update_program_codes_timestamp();

-- =====================================================
-- 6. FUNÇÃO PARA REGISTRAR USO
-- =====================================================

CREATE OR REPLACE FUNCTION register_program_usage(p_shortcode VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE master.program_codes
    SET
        usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE shortcode = p_shortcode;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION register_program_usage IS 'Incrementa contador de uso e atualiza timestamp de último acesso';

-- =====================================================
-- 7. VIEW PARA CÓDIGOS MAIS UTILIZADOS
-- =====================================================

CREATE OR REPLACE VIEW master.v_program_codes_top_used AS
SELECT
    shortcode,
    label,
    module_code,
    route,
    usage_count,
    last_used_at,
    CASE
        WHEN last_used_at > NOW() - INTERVAL '1 day' THEN 'today'
        WHEN last_used_at > NOW() - INTERVAL '7 days' THEN 'week'
        WHEN last_used_at > NOW() - INTERVAL '30 days' THEN 'month'
        ELSE 'older'
    END as recency
FROM master.program_codes
WHERE is_active = TRUE
ORDER BY usage_count DESC, last_used_at DESC
LIMIT 20;

COMMENT ON VIEW master.v_program_codes_top_used IS 'Top 20 códigos mais utilizados para cache e sugestões';

-- =====================================================
-- 8. POPULAR DADOS INICIAIS
-- =====================================================

-- Cadastros Base (EM, ES, US, PE)
INSERT INTO master.program_codes (shortcode, module_code, program_type, label, description, route, icon, search_tokens, aliases) VALUES

-- EMPRESAS (EM)
('em0001', 'EM', '00', 'Cadastro de Empresas', 'Manutenção cadastral de empresas', '/admin/empresas', 'Building2',
 ARRAY['empresa', 'company', 'cadastro empresa', 'firmas', 'organização', 'companhia'],
 '{"datasul_eq": "EST001", "common_typos": ["empres", "empressa"]}'::jsonb),

('em0011', 'EM', '01', 'Detalhes da Empresa', 'Visualização detalhada de empresa', '/admin/empresas/:id', 'Building2',
 ARRAY['empresa', 'detalhes', 'visualizar empresa', 'ficha empresa'],
 '{}'::jsonb),

('em0020', 'EM', '02', 'Consulta de Empresas', 'Consulta e filtros de empresas', '/admin/empresas', 'Search',
 ARRAY['consulta empresa', 'buscar empresa', 'pesquisar empresa', 'filtro empresa'],
 '{}'::jsonb),

('em0070', 'EM', '07', 'Ativação de Empresa', 'Processo de ativação e onboarding de empresa', '/admin/company-activation', 'CheckCircle',
 ARRAY['ativar empresa', 'onboarding', 'ativação empresa', 'habilitar empresa'],
 '{}'::jsonb),

-- ESTABELECIMENTOS (ES)
('es0001', 'ES', '00', 'Cadastro de Estabelecimentos', 'Manutenção cadastral de estabelecimentos', '/admin/estabelecimentos', 'Building',
 ARRAY['estabelecimento', 'filial', 'unidade', 'loja', 'matriz', 'cadastro estabelecimento'],
 '{"datasul_eq": "FIL001"}'::jsonb),

('es0011', 'ES', '01', 'Detalhes do Estabelecimento', 'Visualização detalhada de estabelecimento', '/admin/estabelecimentos/:id', 'Building',
 ARRAY['estabelecimento', 'detalhes', 'visualizar estabelecimento', 'ficha estabelecimento'],
 '{}'::jsonb),

('es0020', 'ES', '02', 'Consulta de Estabelecimentos', 'Consulta e filtros de estabelecimentos', '/admin/estabelecimentos', 'Search',
 ARRAY['consulta estabelecimento', 'buscar filial', 'pesquisar unidade'],
 '{}'::jsonb),

-- USUÁRIOS (US)
('us0001', 'US', '00', 'Cadastro de Usuários', 'Manutenção de usuários do sistema', '/admin/usuarios', 'Users',
 ARRAY['usuario', 'user', 'cadastro usuario', 'pessoas', 'colaborador'],
 '{"datasul_eq": "USU001"}'::jsonb),

('us0011', 'US', '01', 'Detalhes do Usuário', 'Perfil completo do usuário', '/admin/usuarios/:id', 'User',
 ARRAY['usuario', 'perfil', 'detalhes usuario', 'ficha usuario'],
 '{}'::jsonb),

('us0020', 'US', '02', 'Consulta de Usuários', 'Consulta e filtros de usuários', '/admin/usuarios', 'Search',
 ARRAY['consulta usuario', 'buscar usuario', 'pesquisar usuario'],
 '{}'::jsonb),

('us0070', 'US', '07', 'Ativação de Usuário', 'Processo de ativação de usuário', '/admin/user-activation', 'UserCheck',
 ARRAY['ativar usuario', 'ativação usuario', 'habilitar usuario'],
 '{}'::jsonb),

-- PERFIS (PE)
('pe0001', 'PE', '00', 'Cadastro de Perfis', 'Gestão de perfis e permissões', '/admin/perfis', 'Shield',
 ARRAY['perfil', 'role', 'permissão', 'acesso', 'cadastro perfil', 'permissões'],
 '{"datasul_eq": "PER001"}'::jsonb),

('pe0020', 'PE', '02', 'Consulta de Perfis', 'Consulta de perfis e roles', '/admin/perfis', 'Search',
 ARRAY['consulta perfil', 'buscar role', 'pesquisar permissão'],
 '{}'::jsonb),

-- CLIENTES (CL)
('cl0001', 'CL', '00', 'Cadastro de Clientes', 'Manutenção de clientes/pacientes', '/admin/clientes', 'Users',
 ARRAY['cliente', 'paciente', 'beneficiário', 'cadastro cliente', 'cadastro paciente'],
 '{"datasul_eq": "CLI001", "common_names": ["paciente", "beneficiário"]}'::jsonb),

('cl0011', 'CL', '01', 'Detalhes do Cliente', 'Ficha completa do cliente', '/admin/clientes/:id', 'User',
 ARRAY['cliente', 'paciente', 'detalhes cliente', 'ficha paciente'],
 '{}'::jsonb),

('cl0020', 'CL', '02', 'Consulta de Clientes', 'Consulta e filtros de clientes', '/admin/clientes', 'Search',
 ARRAY['consulta cliente', 'buscar paciente', 'pesquisar beneficiário'],
 '{}'::jsonb),

-- PROFISSIONAIS (PR)
('pr0001', 'PR', '00', 'Cadastro de Profissionais', 'Manutenção de profissionais de saúde', '/admin/profissionais', 'UserCog',
 ARRAY['profissional', 'médico', 'enfermeiro', 'técnico', 'cadastro profissional'],
 '{"datasul_eq": "PRO001"}'::jsonb),

('pr0020', 'PR', '02', 'Consulta de Profissionais', 'Consulta de profissionais', '/admin/profissionais', 'Search',
 ARRAY['consulta profissional', 'buscar médico', 'pesquisar enfermeiro'],
 '{}'::jsonb),

-- CONTRATOS (CT)
('ct0001', 'CT', '00', 'Cadastro de Contratos', 'Manutenção de contratos home care', '/admin/contratos', 'FileText',
 ARRAY['contrato', 'contract', 'cadastro contrato', 'home care'],
 '{"datasul_eq": "CON001"}'::jsonb),

('ct0011', 'CT', '01', 'Detalhes do Contrato', 'Visualização completa do contrato', '/admin/contratos/:id', 'FileText',
 ARRAY['contrato', 'detalhes contrato', 'visualizar contrato', 'ficha contrato'],
 '{}'::jsonb),

('ct0012', 'CT', '01', 'Gestão de Vidas', 'Controle de vidas do contrato', '/admin/contratos/:id/vidas', 'Users',
 ARRAY['vidas', 'beneficiários', 'dependentes', 'cadastro vidas'],
 '{}'::jsonb),

('ct0020', 'CT', '02', 'Consulta de Contratos', 'Consulta e filtros de contratos', '/admin/contratos', 'Search',
 ARRAY['consulta contrato', 'buscar contrato', 'pesquisar contrato'],
 '{}'::jsonb),

('ct0080', 'CT', '08', 'Dashboard Contratos', 'Painel gerencial de contratos', '/admin/contract-dashboard', 'BarChart3',
 ARRAY['dashboard', 'painel', 'contratos', 'indicadores contrato'],
 '{}'::jsonb),

-- AUTORIZAÇÕES MÉDICAS (AM)
('am0001', 'AM', '00', 'Autorizações Médicas', 'Gestão de autorizações e solicitações', '/admin/autorizacoes', 'FileCheck',
 ARRAY['autorização', 'authorization', 'médica', 'solicitação', 'pedido médico'],
 '{"datasul_eq": "AUT001"}'::jsonb),

('am0020', 'AM', '02', 'Consulta de Autorizações', 'Consulta de autorizações médicas', '/admin/autorizacoes', 'Search',
 ARRAY['consulta autorização', 'buscar autorização', 'pesquisar solicitação'],
 '{}'::jsonb),

-- CONTROLE DE LIMITES (LM)
('lm0001', 'LM', '00', 'Controle de Limites', 'Gestão de limites e utilização', '/admin/limites', 'Activity',
 ARRAY['limites', 'controle', 'utilização', 'consumo', 'saldo'],
 '{"datasul_eq": "LIM001"}'::jsonb),

('lm0020', 'LM', '02', 'Consulta de Limites', 'Consulta de limites por contrato', '/admin/limites', 'Search',
 ARRAY['consulta limites', 'buscar saldo', 'verificar consumo'],
 '{}'::jsonb),

-- CATÁLOGO DE SERVIÇOS (CS)
('cs0001', 'CS', '00', 'Catálogo de Serviços', 'Manutenção de serviços e procedimentos', '/admin/servicos', 'List',
 ARRAY['serviço', 'procedimento', 'catálogo', 'tabela serviços'],
 '{"datasul_eq": "SER001"}'::jsonb),

('cs0020', 'CS', '02', 'Consulta de Serviços', 'Consulta de serviços disponíveis', '/admin/servicos', 'Search',
 ARRAY['consulta serviço', 'buscar procedimento', 'pesquisar serviço'],
 '{}'::jsonb),

-- FATURAMENTO SAAS (FS)
('fs0001', 'FS', '00', 'Faturamento SaaS', 'Cobrança de assinaturas', '/admin/saas-billing', 'CreditCard',
 ARRAY['faturamento', 'billing', 'assinatura', 'cobrança', 'mensalidade'],
 '{"datasul_eq": "FAT001"}'::jsonb),

('fs0020', 'FS', '02', 'Consulta Faturas SaaS', 'Consulta de faturas de assinatura', '/admin/saas-billing/invoices', 'Receipt',
 ARRAY['fatura', 'invoice', 'consulta fatura', 'nota fiscal'],
 '{}'::jsonb),

('fs0080', 'FS', '08', 'Dashboard Financeiro', 'Painel financeiro e KPIs', '/admin/billing-dashboard', 'DollarSign',
 ARRAY['dashboard', 'financeiro', 'faturamento', 'receita', 'kpi'],
 '{}'::jsonb),

-- FATURAMENTO B2B (FB)
('fb0001', 'FB', '00', 'Faturamento B2B', 'Faturamento de contratos home care', '/admin/b2b-billing', 'FileText',
 ARRAY['faturamento', 'b2b', 'contrato', 'cobrança contrato'],
 '{"datasul_eq": "FATB2B"}'::jsonb),

('fb0020', 'FB', '02', 'Consulta Faturas B2B', 'Consulta de faturas B2B', '/admin/b2b-billing/invoices', 'Receipt',
 ARRAY['fatura b2b', 'consulta fatura', 'invoice b2b'],
 '{}'::jsonb),

-- PLANOS DE ASSINATURA (PA)
('pa0001', 'PA', '00', 'Planos de Assinatura', 'Manutenção de planos SaaS', '/admin/subscription-plans', 'Package',
 ARRAY['plano', 'assinatura', 'subscription', 'pacote'],
 '{"datasul_eq": "PLA001"}'::jsonb),

('pa0020', 'PA', '02', 'Consulta de Planos', 'Consulta de planos disponíveis', '/admin/subscription-plans', 'Search',
 ARRAY['consulta plano', 'buscar assinatura', 'pesquisar pacote'],
 '{}'::jsonb),

-- DASHBOARD (DS)
('ds0001', 'DS', '00', 'Dashboard Principal', 'Painel principal do sistema', '/admin/dashboard', 'LayoutDashboard',
 ARRAY['dashboard', 'painel', 'home', 'principal', 'início'],
 '{}'::jsonb),

('ds0002', 'DS', '00', 'Dashboard Contratos', 'Painel de contratos', '/admin/contract-dashboard', 'BarChart3',
 ARRAY['dashboard', 'contratos', 'painel contratos'],
 '{}'::jsonb),

('ds0003', 'DS', '00', 'Dashboard Financeiro', 'Painel financeiro', '/admin/billing-dashboard', 'DollarSign',
 ARRAY['dashboard', 'financeiro', 'painel financeiro'],
 '{}'::jsonb),

-- RELATÓRIOS (RE)
('re0001', 'RE', '00', 'Central de Relatórios', 'Acesso a todos os relatórios', '/admin/relatorios', 'FileText',
 ARRAY['relatório', 'report', 'central relatórios'],
 '{"datasul_eq": "REL001"}'::jsonb),

('re0050', 'RE', '05', 'Relatório de Empresas', 'Relatório detalhado de empresas', '/admin/relatorios/empresas', 'FileText',
 ARRAY['relatório empresa', 'report company'],
 '{}'::jsonb),

('re0051', 'RE', '05', 'Relatório de Contratos', 'Relatório detalhado de contratos', '/admin/relatorios/contratos', 'FileText',
 ARRAY['relatório contrato', 'report contract'],
 '{}'::jsonb),

('re0052', 'RE', '05', 'Relatório Financeiro', 'Relatório de faturamento e receitas', '/admin/relatorios/faturamento', 'FileText',
 ARRAY['relatório financeiro', 'receita', 'faturamento'],
 '{}'::jsonb),

-- CONFIGURAÇÕES (CF)
('cf0001', 'CF', '00', 'Configurações Sistema', 'Configurações gerais do sistema', '/admin/configuracoes', 'Settings',
 ARRAY['configuração', 'settings', 'parâmetros', 'config'],
 '{"datasul_eq": "CFG001"}'::jsonb),

('cf0010', 'CF', '01', 'Configurações Email', 'Configuração de email SMTP', '/admin/configuracoes/email', 'Mail',
 ARRAY['email', 'smtp', 'configuração email'],
 '{}'::jsonb),

('cf0011', 'CF', '01', 'Configurações Integração', 'Configuração de APIs e integrações', '/admin/configuracoes/integracao', 'Plug',
 ARRAY['integração', 'api', 'configuração api'],
 '{}'::jsonb),

-- MENUS (MN)
('mn0001', 'MN', '00', 'Gestão de Menus', 'Manutenção de menus do sistema', '/admin/menus', 'Menu',
 ARRAY['menu', 'navegação', 'cadastro menu'],
 '{"datasul_eq": "MEN001"}'::jsonb),

('mn0020', 'MN', '02', 'Consulta de Menus', 'Consulta de menus cadastrados', '/admin/menus', 'Search',
 ARRAY['consulta menu', 'buscar menu'],
 '{}'::jsonb),

-- NOTIFICAÇÕES (NT)
('nt0001', 'NT', '00', 'Central de Notificações', 'Gestão de notificações', '/admin/notificacoes', 'Bell',
 ARRAY['notificação', 'aviso', 'alerta', 'mensagem'],
 '{"datasul_eq": "NOT001"}'::jsonb),

('nt0020', 'NT', '02', 'Consulta de Notificações', 'Histórico de notificações', '/admin/notificacoes', 'Search',
 ARRAY['consulta notificação', 'histórico avisos'],
 '{}'::jsonb),

-- AUDITORIA (AU)
('au0001', 'AU', '00', 'Logs de Auditoria', 'Visualização de logs do sistema', '/admin/auditoria', 'FileSearch',
 ARRAY['auditoria', 'log', 'histórico', 'rastreamento'],
 '{"datasul_eq": "AUD001"}'::jsonb),

('au0020', 'AU', '02', 'Consulta de Auditoria', 'Busca em logs de auditoria', '/admin/auditoria', 'Search',
 ARRAY['consulta log', 'buscar auditoria', 'pesquisar histórico'],
 '{}'::jsonb)

ON CONFLICT (shortcode) DO NOTHING;

-- =====================================================
-- 9. ESTATÍSTICAS
-- =====================================================

DO $$
DECLARE
    total_codes INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_codes FROM master.program_codes;
    RAISE NOTICE '✅ Sistema de códigos criado com sucesso!';
    RAISE NOTICE '📊 Total de códigos cadastrados: %', total_codes;
    RAISE NOTICE '🔍 Índices criados: 8';
    RAISE NOTICE '🚀 Sistema pronto para uso via Ctrl+Alt+X';
END $$;
