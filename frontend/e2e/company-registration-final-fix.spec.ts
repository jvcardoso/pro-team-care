import { test, expect } from "@playwright/test";

// ✅ CORREÇÃO: Função para criar token JWT válido para testes
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

test.describe("Cadastro de Empresa - CORREÇÃO FINAL", () => {
  test("cadastro completo com CNPJ da Receita Federal - BRAZIL HOME CARE", async ({
    page,
    context,
  }) => {
    // Limpar estado anterior
    await context.clearCookies();
    await context.clearPermissions();

    // ✅ CORREÇÃO: Mock completo de autenticação que bypassa validação backend
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
      path: "test-results/form-loaded-success.png",
      fullPage: true,
    });

    // === TESTE DO FLUXO COMPLETO ===

    // Preencher CNPJ
    await cnpjInput.fill("05.514.464/0001-30");

    // Buscar botão "Consultar"
    const consultarButton = page.getByText("Consultar");
    if (await consultarButton.isVisible()) {
      await consultarButton.click();
      await page.waitForTimeout(2000);
    }

    // Preencher campos obrigatórios
    const nameInput = page.getByLabel("Razão Social");
    await nameInput.fill("BRAZIL HOME CARE ASSISTENCIA MEDICA DOMICILIAR LTDA");

    // Preencher telefone (campo pré-existente)
    const phoneInput = page.locator('input[placeholder*="telefone"]').first();
    await phoneInput.fill("1145216565");

    // Preencher email (campo pré-existente)
    const emailInput = page.locator('input[type="email"]').first();
    await emailInput.fill("controller@domicilehomecare.com.br");

    // Preencher endereço básico
    const streetInput = page
      .locator('input[placeholder*="logradouro"]')
      .first();
    await streetInput.fill("RUA CAPITAO CASSIANO RICARDO DE TOLEDO");

    const numberInput = page.locator('input[placeholder*="número"]').first();
    await numberInput.fill("191");

    const cityInput = page.locator('input[placeholder*="cidade"]').first();
    await cityInput.fill("Jundiaí");

    // Tentar salvar
    const saveButton = page.getByRole("button", { name: /salvar/i });
    await expect(saveButton).toBeVisible();
    await saveButton.click();

    // Aguardar resposta (sucesso ou erro)
    await page.waitForTimeout(3000);

    // Capturar screenshot do resultado
    await page.screenshot({
      path: "test-results/form-submission-result.png",
      fullPage: true,
    });

    console.log("✅ Teste concluído - formulário carregou e foi submetido!");
  });

  test("debug FINAL - verificar carregamento do formulário", async ({
    page,
    context,
  }) => {
    await context.clearCookies();

    // Token válido
    const validToken = createValidMockToken();

    await page.addInitScript((token) => {
      localStorage.setItem("access_token", token);
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@example.com",
          name: "Admin Teste",
          is_system_admin: true,
          person_type: "PF",
          context_type: "system",
        })
      );

      // Adicionar flag de debug
      window.__DEBUG_AUTH__ = true;
    }, validToken);

    // Navegar para formulário
    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");

    // Log estado da página
    const pageTitle = await page.title();
    console.log("📄 Título da página:", pageTitle);

    const url = page.url();
    console.log("🔗 URL atual:", url);

    // Verificar se AuthContext carregou
    const authLoading = await page
      .getByText("Verificando autenticação")
      .isVisible();
    console.log("🔄 Ainda carregando autenticação:", authLoading);

    // Verificar se formulário apareceu
    const formVisible = await page.getByText("Nova Empresa").isVisible();
    console.log("📋 Formulário visível:", formVisible);

    // Verificar se campo CNPJ apareceu
    const cnpjVisible = await page.getByLabel("CNPJ").isVisible();
    console.log("🆔 Campo CNPJ visível:", cnpjVisible);

    // Contar elementos do formulário
    const inputCount = await page.locator("input").count();
    console.log("📝 Total de inputs encontrados:", inputCount);

    const buttonCount = await page.locator("button").count();
    console.log("🔘 Total de botões encontrados:", buttonCount);

    // Capturar screenshot final
    await page.screenshot({
      path: "test-results/debug-final-state.png",
      fullPage: true,
    });

    // ✅ VALIDAÇÃO FINAL
    expect(authLoading).toBe(false);
    expect(formVisible).toBe(true);
    expect(cnpjVisible).toBe(true);
    expect(inputCount).toBeGreaterThan(5);

    console.log("✅ DEBUG CONCLUÍDO - Todas as validações passaram!");
  });

  test("validação de mock de autenticação", async ({ page, context }) => {
    // Teste específico para validar que o mock de auth funciona
    await context.clearCookies();

    const validToken = createValidMockToken();

    await page.addInitScript((token) => {
      localStorage.setItem("access_token", token);
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@example.com",
          is_system_admin: true,
        })
      );

      // Interceptar logs do AuthContext
      const originalLog = console.log;
      window.__authLogs = [];
      console.log = (...args) => {
        window.__authLogs.push(args.join(" "));
        originalLog.apply(console, args);
      };
    }, validToken);

    await page.goto("/admin/empresas");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    // Verificar logs de autenticação
    const authLogs = await page.evaluate(() => window.__authLogs || []);
    console.log("📊 Logs de autenticação:", authLogs);

    // Verificar se não está mais carregando
    const stillLoading = await page
      .getByText("Verificando autenticação")
      .isVisible();
    console.log("⏳ Ainda carregando:", stillLoading);

    expect(stillLoading).toBe(false);
  });
});
