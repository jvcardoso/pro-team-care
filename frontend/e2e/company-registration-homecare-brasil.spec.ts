import { test, expect } from "@playwright/test";

// ✅ Função para criar token JWT válido para testes
const createValidMockToken = () => {
  const header = Buffer.from(
    JSON.stringify({ alg: "HS256", typ: "JWT" })
  ).toString("base64");
  const payload = Buffer.from(
    JSON.stringify({
      sub: "admin@example.com",
      exp: Math.floor(Date.now() / 1000) + 3600, // Expira em 1 hora
      iat: Math.floor(Date.now() / 1000),
      is_system_admin: true,
    })
  ).toString("base64");
  const signature = "mock-signature-valid";
  return `${header}.${payload}.${signature}`;
};

test.describe("Cadastro de Empresa - HOME CARE BRASIL SERVICOS LTDA", () => {
  test("cadastro completo com CNPJ da Receita Federal - HOME CARE BRASIL", async ({
    page,
    context,
  }) => {
    // Limpar estado anterior
    await context.clearCookies();
    await context.clearPermissions();

    // ✅ Mock completo de autenticação que bypassa validação backend
    await page.addInitScript(() => {
      // Mock do AuthContext para sempre retornar autenticado
      window.__MOCK_AUTH__ = {
        isAuthenticated: true,
        user: {
          id: 1,
          email: "admin@example.com",
          name: "Admin Teste",
          is_system_admin: true,
          person_type: "PF",
          context_type: "system",
        },
        token: "mock-token-valid",
        loading: false,
      };

      // Override do AuthContext
      if (window.AuthContext) {
        window.AuthContext._currentValue = window.__MOCK_AUTH__;
      }

      // Simular localStorage
      localStorage.setItem("access_token", "mock-token-valid");
      localStorage.setItem("user", JSON.stringify(window.__MOCK_AUTH__.user));
    });

    // Mockar chamadas de API para evitar validação backend
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          email: "admin@example.com",
          name: "Admin Teste",
          is_system_admin: true,
          person_type: "PF",
        }),
      });
    });

    // Mockar consulta CNPJ da Receita Federal
    await page.route(
      "**/receitaws.com.br/v1/cnpj/48189995000107",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            abertura: "05/10/2022",
            situacao: "ATIVA",
            tipo: "MATRIZ",
            nome: "HOME CARE BRASIL SERVICOS LTDA",
            fantasia: "HOME CARE BRASIL",
            porte: "MICRO EMPRESA",
            natureza_juridica: "206-2 - Sociedade Empresária Limitada",
            atividade_principal: [
              {
                code: "87.12-3-00",
                text: "Atividades de fornecimento de infra-estrutura de apoio e assistência a paciente no domicílio",
              },
            ],
            logradouro: "RUA 10",
            numero: "718",
            complemento: "QUADRAF-6 LOTE 29E APT 1203 COND ITANHANGA PALACE",
            municipio: "GOIANIA",
            bairro: "SET OESTE",
            uf: "GO",
            cep: "74.120-020",
            email: "legitimuscontabilidade@hotmail.com",
            telefone: "(62) 8241-0043",
            data_situacao: "05/10/2022",
            cnpj: "48.189.995/0001-07",
            status: "OK",
          }),
        });
      }
    );

    // Navegar diretamente para o formulário
    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");

    // Aguardar carregamento
    await page.waitForTimeout(3000);

    // ✅ VALIDAÇÃO: Verificar se não está mais na tela de "Verificando autenticação"
    const authLoadingText = page.getByText("Verificando autenticação");
    await expect(authLoadingText).not.toBeVisible();

    // ✅ VALIDAÇÃO: Verificar se o formulário carregou
    const formTitle = page.getByText("Nova Empresa");
    await expect(formTitle).toBeVisible({ timeout: 10000 });

    // ✅ VALIDAÇÃO: Verificar se campo CNPJ está disponível
    const cnpjInput = page.getByLabel("CNPJ");
    await expect(cnpjInput).toBeVisible({ timeout: 5000 });

    // Capturar screenshot para confirmar que formulário carregou
    await page.screenshot({
      path: "test-results/homecare-brasil-form-loaded.png",
      fullPage: true,
    });

    console.log("✅ Formulário carregado com sucesso!");

    // === PREENCHIMENTO DO FORMULÁRIO ===

    // Preencher CNPJ
    await cnpjInput.fill("48.189.995/0001-07");

    // Clicar em "Consultar" para buscar dados da Receita Federal
    const consultarButton = page.getByRole("button", { name: /consultar/i });
    await expect(consultarButton).toBeVisible();
    await consultarButton.click();

    // Aguardar carregamento dos dados da Receita Federal
    await page.waitForTimeout(2000);

    // Verificar se os campos foram auto-preenchidos
    const razaoSocialInput = page.getByLabel("Razão Social");
    await expect(razaoSocialInput).toHaveValue(
      "HOME CARE BRASIL SERVICOS LTDA"
    );

    const fantasiaInput = page.getByLabel("Nome Fantasia");
    await expect(fantasiaInput).toHaveValue("HOME CARE BRASIL");

    // Verificar seção de informações da Receita Federal apareceu
    await expect(
      page.getByText("Informações da Receita Federal")
    ).toBeVisible();

    console.log("✅ Dados da Receita Federal carregados automaticamente!");

    // === SEÇÃO: TELEFONES ===

    // Preencher telefone principal (do Receita Federal)
    const phoneNumberInput = page
      .locator('input[placeholder*="telefone"]')
      .first();
    await phoneNumberInput.fill("6282410043");

    const phoneTypeSelect = page
      .locator("select")
      .filter({ hasText: "Tipo" })
      .first();
    await phoneTypeSelect.selectOption("commercial");

    const phonePrincipalCheckbox = page
      .locator('input[type="checkbox"]')
      .first();
    await phonePrincipalCheckbox.check();

    console.log("✅ Telefone preenchido!");

    // === SEÇÃO: EMAILS ===

    // Preencher email principal (do Receita Federal)
    const mainEmailInput = page.locator('input[type="email"]').first();
    await mainEmailInput.fill("legitimuscontabilidade@hotmail.com");

    const emailTypeSelect = page
      .locator("select")
      .filter({ hasText: "Tipo" })
      .nth(1);
    await emailTypeSelect.selectOption("work");

    const emailPrincipalCheckbox = page
      .locator('input[type="checkbox"]')
      .nth(1);
    await emailPrincipalCheckbox.check();

    console.log("✅ Email preenchido!");

    // === SEÇÃO: ENDEREÇOS ===

    // Preencher endereço principal (já pré-adicionado)
    // Preencher CEP para auto-preenchimento ViaCEP
    const cepInput = page.locator('input[placeholder*="CEP"]').first();
    await cepInput.fill("74120020");

    // Aguardar auto-preenchimento
    await page.waitForTimeout(1500);

    // Verificar se logradouro foi preenchido
    const streetInput = page
      .locator('input[placeholder*="logradouro"]')
      .first();
    await expect(streetInput).toHaveValue("RUA 10");

    // Preencher número
    const numberInput = page.locator('input[placeholder*="número"]').first();
    await numberInput.fill("718");

    // Preencher complemento
    const detailsInput = page
      .locator('input[placeholder*="complemento"]')
      .first();
    await detailsInput.fill(
      "QUADRAF-6 LOTE 29E APT 1203 COND ITANHANGA PALACE"
    );

    const addressTypeSelect = page
      .locator("select")
      .filter({ hasText: "Tipo" })
      .nth(2);
    await addressTypeSelect.selectOption("commercial");

    const addressPrincipalCheckbox = page
      .locator('input[type="checkbox"]')
      .nth(2);
    await addressPrincipalCheckbox.check();

    console.log("✅ Endereço preenchido!");

    // === SEÇÃO: CONVITE PARA GESTOR ===

    // Preencher email do gestor (fictício baseado no domínio)
    const managerEmailInput = page.locator('input[type="email"]').nth(1); // Segundo email input (gestor)
    await managerEmailInput.fill("gestor@homecarebrasil.com.br");

    console.log("✅ Email do gestor preenchido!");

    // === SUBMISSÃO DO FORMULÁRIO ===

    // Clicar em "Salvar"
    const saveButton = page.getByRole("button", { name: /salvar/i });
    await expect(saveButton).toBeVisible();
    await saveButton.click();

    // Aguardar processamento
    await page.waitForTimeout(3000);

    // Verificar sucesso - deve redirecionar ou mostrar mensagem
    await expect(
      page.getByText("Empresa cadastrada com sucesso")
    ).toBeVisible();

    // Verificar se convite foi enviado
    await expect(page.getByText(/convite enviado/i)).toBeVisible();

    // Capturar screenshot do resultado
    await page.screenshot({
      path: "test-results/homecare-brasil-submission-result.png",
      fullPage: true,
    });

    console.log("✅ Cadastro de HOME CARE BRASIL concluído com sucesso!");
  });

  test("validação de CNPJ duplicado - HOME CARE BRASIL", async ({
    page,
    context,
  }) => {
    // Teste para verificar erro ao tentar cadastrar CNPJ já existente
    await context.clearCookies();

    // Mock de autenticação
    await page.addInitScript(() => {
      window.__MOCK_AUTH__ = {
        isAuthenticated: true,
        user: { id: 1, email: "admin@teste.com", is_system_admin: true },
        token: "mock-token-valid",
        loading: false,
      };
      localStorage.setItem("access_token", "mock-token-valid");
      localStorage.setItem("user", JSON.stringify(window.__MOCK_AUTH__.user));
    });

    // Mock API auth
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          is_system_admin: true,
        }),
      });
    });

    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    // Aguardar autenticação
    await page.waitForFunction(() => {
      const bodyText = document.body.textContent || "";
      return !bodyText.includes("Verificando autenticação");
    });

    // Preencher CNPJ já cadastrado
    const cnpjInput = page.getByLabel("CNPJ");
    await cnpjInput.fill("48.189.995/0001-07");

    // Preencher outros campos obrigatórios rapidamente
    const nameInput = page.getByLabel("Razão Social");
    await nameInput.fill("Empresa Teste");

    // Preencher telefone (já pré-adicionado)
    const phoneInput = page.locator('input[placeholder*="telefone"]').first();
    await phoneInput.fill("11999999999");

    // Preencher email (já pré-adicionado)
    const testEmailInput = page.locator('input[type="email"]').first();
    await testEmailInput.fill("teste@empresa.com");

    // Preencher endereço (já pré-adicionado)
    const streetInput = page
      .locator('input[placeholder*="logradouro"]')
      .first();
    await streetInput.fill("Rua Teste");
    const cityInput = page.locator('input[placeholder*="cidade"]').first();
    await cityInput.fill("São Paulo");
    const stateInput = page
      .locator("select")
      .filter({ hasText: "Estado" })
      .first();
    await stateInput.selectOption("SP");

    // Tentar salvar
    const saveButton = page.getByRole("button", { name: /salvar/i });
    await saveButton.click();

    // Verificar erro de CNPJ duplicado
    await expect(page.getByText(/CNPJ já existe/i)).toBeVisible();
  });

  test("validação de endereço sem número - HOME CARE BRASIL", async ({
    page,
    context,
  }) => {
    await context.clearCookies();

    // Mock de autenticação
    await page.addInitScript(() => {
      window.__MOCK_AUTH__ = {
        isAuthenticated: true,
        user: { id: 1, email: "admin@teste.com", is_system_admin: true },
        token: "mock-token-valid",
        loading: false,
      };
      localStorage.setItem("access_token", "mock-token-valid");
      localStorage.setItem("user", JSON.stringify(window.__MOCK_AUTH__.user));
    });

    // Mock API auth
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          is_system_admin: true,
        }),
      });
    });

    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    // Aguardar autenticação
    await page.waitForFunction(() => {
      const bodyText = document.body.textContent || "";
      return !bodyText.includes("Verificando autenticação");
    });

    // Preencher CNPJ e nome
    const cnpjInput = page.getByLabel("CNPJ");
    await cnpjInput.fill("12.345.678/0001-90"); // CNPJ fictício

    const nameInput = page.getByLabel("Razão Social");
    await nameInput.fill("Empresa Sem Número");

    // Preencher telefone (já pré-adicionado)
    const phoneInput = page.locator('input[placeholder*="telefone"]').first();
    await phoneInput.fill("11999999999");

    // Preencher email (já pré-adicionado)
    const testEmailInput2 = page.locator('input[type="email"]').first();
    await testEmailInput2.fill("teste@empresa.com");

    // Preencher endereço SEM número (já pré-adicionado)
    const streetInput = page
      .locator('input[placeholder*="logradouro"]')
      .first();
    await streetInput.fill("Rua Sem Número");
    const cityInput = page.locator('input[placeholder*="cidade"]').first();
    await cityInput.fill("São Paulo");
    const stateInput = page
      .locator("select")
      .filter({ hasText: "Estado" })
      .first();
    await stateInput.selectOption("SP");

    // Tentar salvar
    const saveButton = page.getByRole("button", { name: /salvar/i });
    await saveButton.click();

    // Verificar modal de confirmação
    await expect(page.getByText(/endereços sem número/i)).toBeVisible();

    // Confirmar no modal
    const confirmButton = page.getByRole("button", { name: /confirmar/i });
    await confirmButton.click();

    // Verificar sucesso
    await expect(
      page.getByText("Empresa cadastrada com sucesso")
    ).toBeVisible();
  });

  test("debug - HOME CARE BRASIL estrutura e validações", async ({
    page,
    context,
  }) => {
    await context.clearCookies();

    // Mock de autenticação
    await page.addInitScript(() => {
      window.__MOCK_AUTH__ = {
        isAuthenticated: true,
        user: { id: 1, email: "admin@teste.com", is_system_admin: true },
        token: "mock-token-valid",
        loading: false,
      };
      localStorage.setItem("access_token", "mock-token-valid");
      localStorage.setItem("user", JSON.stringify(window.__MOCK_AUTH__.user));
    });

    // Mock API auth
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          is_system_admin: true,
        }),
      });
    });

    // Página principal de empresas
    await page.goto("/admin/empresas");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    // Aguardar autenticação
    await page.waitForFunction(() => {
      const bodyText = document.body.textContent || "";
      return !bodyText.includes("Verificando autenticação");
    });

    // Capturar screenshot da página principal
    await page.screenshot({
      path: "test-results/homecare-brasil-empresas-page.png",
      fullPage: true,
    });

    // Verificar se botão "Nova empresa" existe
    const newCompanyButton = page.getByText("Nova empresa");
    const buttonExists = await newCompanyButton.isVisible();
    console.log("Botão 'Nova empresa' visível:", buttonExists);

    if (buttonExists) {
      await newCompanyButton.click();
      await page.waitForURL("**/empresas?view=create");

      // Aguardar autenticação no formulário
      await page.waitForFunction(() => {
        const bodyText = document.body.textContent || "";
        return !bodyText.includes("Verificando autenticação");
      });

      // Capturar screenshot do formulário
      await page.screenshot({
        path: "test-results/homecare-brasil-form-page.png",
        fullPage: true,
      });

      // Verificar elementos do formulário
      const formVisible = await page.getByText("Nova Empresa").isVisible();
      const cnpjVisible = await page.getByLabel("CNPJ").isVisible();
      const inputCount = await page.locator("input").count();

      console.log("📋 Formulário visível:", formVisible);
      console.log("🆔 Campo CNPJ visível:", cnpjVisible);
      console.log("📝 Total de inputs:", inputCount);

      // Capturar screenshot final
      await page.screenshot({
        path: "test-results/homecare-brasil-debug-final.png",
        fullPage: true,
      });

      // ✅ VALIDAÇÃO FINAL
      expect(formVisible).toBe(true);
      expect(cnpjVisible).toBe(true);
      expect(inputCount).toBeGreaterThan(10);

      console.log("✅ DEBUG HOME CARE BRASIL - Todas as validações passaram!");
    } else {
      console.log("❌ Botão 'Nova empresa' não encontrado");
      // Capturar screenshot de erro
      await page.screenshot({
        path: "test-results/homecare-brasil-debug-error.png",
        fullPage: true,
      });
      expect(buttonExists).toBe(true);
    }
  });
});
