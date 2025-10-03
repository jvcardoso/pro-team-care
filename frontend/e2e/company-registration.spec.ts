import { test, expect } from "@playwright/test";
import { AdminPage } from "./pages/AdminPage";

test.describe("Cadastro de Empresa", () => {
  test("cadastro completo com CNPJ da Receita Federal - BRAZIL HOME CARE", async ({
    page,
    context,
  }) => {
    // Limpar estado anterior
    await context.clearCookies();
    await context.clearPermissions();

    // Fazer login primeiro (como no complete-flow.spec.ts)
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    // Preencher formulário de login
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill("admin@example.com");
    await passwordInput.fill("password");
    await submitButton.click();

    // Aguardar redirecionamento para admin
    await page.waitForURL("**/admin**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");

    // Configurar permissões para empresa
    await page.addInitScript(() => {
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "true"); // Para ter permissões admin
    });

    // Navegar diretamente para o formulário de criação (evitando problemas com botão)
    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");

    // Verificar se estamos na página correta
    console.log("URL atual:", page.url());
    await page.waitForTimeout(3000); // Dar mais tempo para carregar

    // Verificar se há algum conteúdo na página
    const pageContent = await page.textContent("body");
    console.log(
      "Conteúdo da página (primeiros 500 chars):",
      pageContent?.substring(0, 500)
    );

    // Tentar encontrar qualquer indicador de que estamos no formulário
    const hasForm = (await page.locator("form").count()) > 0;
    console.log("Formulário encontrado:", hasForm);

    // Verificar se há elementos específicos do CompanyForm
    const hasCNPJLabel = await page
      .getByLabel("CNPJ")
      .isVisible()
      .catch(() => false);
    console.log("Label CNPJ encontrado:", hasCNPJLabel);

    // Capturar screenshot para debug
    await page.screenshot({
      path: "test-results/form-page-debug.png",
      fullPage: true,
    });

    // Se não encontrou elementos básicos, falhar o teste
    if (!hasForm || !hasCNPJLabel) {
      throw new Error(
        "❌ Formulário de empresa não carregou corretamente. Verificar permissões ou implementação."
      );
    }

    // === SEÇÃO: DADOS BÁSICOS DA EMPRESA ===

    // Preencher CNPJ
    const cnpjInput = page.getByLabel("CNPJ");
    await cnpjInput.fill("05.514.464/0001-30");

    // Clicar em "Consultar" para buscar dados da Receita Federal
    const consultarButton = page.getByRole("button", { name: /consultar/i });
    await expect(consultarButton).toBeVisible();
    await consultarButton.click();

    // Aguardar carregamento dos dados da Receita Federal
    await page.waitForTimeout(2000); // Ajustar conforme necessário

    // Verificar se os campos foram auto-preenchidos
    const razaoSocialInput = page.getByLabel("Razão Social");
    await expect(razaoSocialInput).toHaveValue(
      "BRAZIL HOME CARE ASSISTENCIA MEDICA DOMICILIAR LTDA"
    );

    const fantasiaInput = page.getByLabel("Nome Fantasia");
    await expect(fantasiaInput).toHaveValue("DOMICILE HOME CARE");

    // Verificar seção de informações da Receita Federal apareceu
    await expect(
      page.getByText("Informações da Receita Federal")
    ).toBeVisible();

    // === SEÇÃO: TELEFONES ===

    // Preencher telefone principal (já pré-adicionado)
    const phoneNumberInput = page
      .locator('input[placeholder*="telefone"]')
      .first();
    await phoneNumberInput.fill("1145216565");

    const phoneTypeSelect = page
      .locator("select")
      .filter({ hasText: "Tipo" })
      .first();
    await phoneTypeSelect.selectOption("commercial");

    const phonePrincipalCheckbox = page
      .locator('input[type="checkbox"]')
      .first();
    await phonePrincipalCheckbox.check();

    // === SEÇÃO: EMAILS ===

    // Preencher email principal (já pré-adicionado)
    const mainEmailInput = page.locator('input[type="email"]').first();
    await mainEmailInput.fill("controller@domicilehomecare.com.br");

    const emailTypeSelect = page
      .locator("select")
      .filter({ hasText: "Tipo" })
      .nth(1);
    await emailTypeSelect.selectOption("work");

    const emailPrincipalCheckbox = page
      .locator('input[type="checkbox"]')
      .nth(1);
    await emailPrincipalCheckbox.check();

    // === SEÇÃO: ENDEREÇOS ===

    // Preencher endereço principal (já pré-adicionado)
    // Preencher CEP para auto-preenchimento ViaCEP
    const cepInput = page.locator('input[placeholder*="CEP"]').first();
    await cepInput.fill("13201840");

    // Aguardar auto-preenchimento
    await page.waitForTimeout(1500);

    // Verificar se logradouro foi preenchido
    const streetInput = page
      .locator('input[placeholder*="logradouro"]')
      .first();
    await expect(streetInput).toHaveValue(
      "RUA CAPITAO CASSIANO RICARDO DE TOLEDO"
    );

    // Preencher número
    const numberInput = page.locator('input[placeholder*="número"]').first();
    await numberInput.fill("191");

    // Preencher complemento
    const detailsInput = page
      .locator('input[placeholder*="complemento"]')
      .first();
    await detailsInput.fill("SALA 1508 ANDAR 15");

    const addressTypeSelect = page
      .locator("select")
      .filter({ hasText: "Tipo" })
      .nth(2);
    await addressTypeSelect.selectOption("commercial");

    const addressPrincipalCheckbox = page
      .locator('input[type="checkbox"]')
      .nth(2);
    await addressPrincipalCheckbox.check();

    // === SEÇÃO: CONVITE PARA GESTOR ===

    // Preencher email do gestor (fictício baseado no domínio)
    const managerEmailInput = page.locator('input[type="email"]').nth(1); // Segundo email input (gestor)
    await managerEmailInput.fill("gestor@domicilehomecare.com.br");

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

    // Verificar se redirecionou para lista ou detalhes
    await page.waitForURL("**/empresas**", { timeout: 10000 });

    console.log("✅ Cadastro de empresa concluído com sucesso!");
  });

  test("validação de CNPJ duplicado", async ({ page, context }) => {
    // Teste para verificar erro ao tentar cadastrar CNPJ já existente
    await context.clearCookies();

    // Fazer login
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill("admin@example.com");
    await passwordInput.fill("password");
    await submitButton.click();

    await page.waitForURL("**/admin**", { timeout: 10000 });

    // Configurar permissões
    await page.addInitScript(() => {
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "true");
    });

    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");

    // Preencher CNPJ já cadastrado
    const cnpjInput = page.getByLabel("CNPJ");
    await cnpjInput.fill("05.514.464/0001-30");

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

  test("validação de endereço sem número - modal de confirmação", async ({
    page,
    context,
  }) => {
    await context.clearCookies();

    // Fazer login
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill("admin@example.com");
    await passwordInput.fill("password");
    await submitButton.click();

    await page.waitForURL("**/admin**", { timeout: 10000 });

    // Configurar permissões
    await page.addInitScript(() => {
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "true");
    });

    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");

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

  test("debug - verificar estrutura da página", async ({ page, context }) => {
    // Limpar estado
    await context.clearCookies();

    // Fazer login
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await emailInput.fill("admin@example.com");
    await passwordInput.fill("password");
    await submitButton.click();

    await page.waitForURL("**/admin**", { timeout: 10000 });

    // Configurar permissões
    await page.addInitScript(() => {
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "true");
    });

    // Página principal de empresas
    await page.goto("/admin/empresas");
    await page.waitForLoadState("networkidle");

    // Capturar screenshot da página principal
    await page.screenshot({
      path: "test-results/debug-empresas-page.png",
      fullPage: true,
    });

    // Capturar screenshot da página principal
    await page.screenshot({
      path: "test-results/debug-empresas-page.png",
      fullPage: true,
    });

    // Capturar screenshot da página principal
    await page.screenshot({
      path: "test-results/debug-empresas-page.png",
      fullPage: true,
    });

    // Listar botões disponíveis
    const buttons = await page.locator("button").allTextContents();
    console.log("Botões encontrados:", buttons);

    // Verificar se botão "Nova empresa" existe
    const newCompanyButton = page.getByText("Nova empresa");
    const buttonExists = await newCompanyButton.isVisible();
    console.log("Botão 'Nova empresa' visível:", buttonExists);

    if (buttonExists) {
      await newCompanyButton.click();
      await page.waitForURL("**/empresas?view=create");

      // Capturar screenshot do formulário
      await page.screenshot({
        path: "test-results/debug-form-page.png",
        fullPage: true,
      });

      // Listar labels disponíveis
      const labels = await page.locator("label").allTextContents();
      console.log("Labels encontrados:", labels);

      // Listar inputs disponíveis
      const inputs = await page.locator("input").all();
      console.log("Número de inputs:", inputs.length);

      for (let i = 0; i < Math.min(inputs.length, 5); i++) {
        const input = inputs[i];
        const placeholder = await input.getAttribute("placeholder");
        const type = await input.getAttribute("type");
        console.log(`Input ${i}: type=${type}, placeholder=${placeholder}`);
      }
    }
  });
});
