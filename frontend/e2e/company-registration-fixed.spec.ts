import { test, expect } from "@playwright/test";
import { AdminPage } from "./pages/AdminPage";

test.describe("Cadastro de Empresa - Testes Corrigidos", () => {
  test("cadastro completo com CNPJ da Receita Federal - BRAZIL HOME CARE", async ({
    page,
    context,
  }) => {
    // Limpar estado anterior
    await context.clearCookies();
    await context.clearPermissions();

    // Configurar autenticação mockada
    await page.addInitScript(() => {
      const mockToken =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6OTk5OTk5OTk5OX0.mock-signature";

      localStorage.setItem("access_token", mockToken);
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          name: "Admin Teste",
          is_system_admin: true, // Para ter permissões de criar empresa
          person_type: "PF",
        })
      );
    });

    // Navegar para página de empresas
    await page.goto("/admin/empresas");
    await page.waitForLoadState("networkidle");

    // CORREÇÃO: Botão tem texto "Nova empresa" (não "Nova empresa")
    const newCompanyButton = page.getByText("Nova empresa");
    await expect(newCompanyButton).toBeVisible();
    await newCompanyButton.click();

    // Aguardar navegação para formulário de criação
    await page.waitForURL("**/empresas?view=create");
    await page.waitForLoadState("networkidle");

    // Verificar título do formulário
    await expect(page.getByText("Nova Empresa")).toBeVisible();

    // === SEÇÃO: DADOS BÁSICOS DA EMPRESA ===

    // CORREÇÃO: CNPJ não tem atributo name, usar por label
    const cnpjInput = page.getByLabel("CNPJ");
    await cnpjInput.fill("05.514.464/0001-30");

    // Clicar em "Consultar" para buscar dados da Receita Federal
    const consultarButton = page.getByText("Consultar");
    await expect(consultarButton).toBeVisible();
    await consultarButton.click();

    // Aguardar carregamento dos dados da Receita Federal
    await page.waitForTimeout(2000);

    // CORREÇÃO: Usar getByLabel ao invés de name attributes
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

    // CORREÇÃO: Componente PhoneInputGroup já vem com um telefone inicial
    // Preencher o telefone existente ao invés de adicionar
    const phoneNumberInput = page
      .locator('input[placeholder*="telefone"], input[placeholder*="número"]')
      .first();
    await phoneNumberInput.fill("1145216565");

    // === SEÇÃO: EMAILS ===

    // CORREÇÃO: Componente EmailInputGroup já vem com um email inicial
    const emailInput = page
      .locator('input[placeholder*="email"], input[type="email"]')
      .first();
    await emailInput.fill("controller@domicilehomecare.com.br");

    // === SEÇÃO: ENDEREÇOS ===

    // CORREÇÃO: Componente AddressInputGroup já vem com um endereço inicial
    // Preencher CEP para auto-preenchimento ViaCEP
    const cepInput = page
      .locator('input[placeholder*="CEP"], input[placeholder*="00000-000"]')
      .first();
    await cepInput.fill("13201840");

    // Aguardar auto-preenchimento
    await page.waitForTimeout(1500);

    // Verificar se logradouro foi preenchido
    const streetInput = page.getByLabel(/logradouro|rua|endereço/i);
    await expect(streetInput).toHaveValue(
      "RUA CAPITAO CASSIANO RICARDO DE TOLEDO"
    );

    // Preencher número
    const numberInput = page.getByLabel(/número|num/i);
    await numberInput.fill("191");

    // Preencher complemento
    const detailsInput = page.getByLabel(/complemento|detalhes/i);
    await detailsInput.fill("SALA 1508 ANDAR 15");

    // === SEÇÃO: CONVITE PARA GESTOR ===

    // CORREÇÃO: Campo específico para gestor no final do formulário
    const managerEmailInput = page.locator('input[placeholder*="gestor"]');
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
      page.getByText(/empresa.*sucesso|sucesso.*empresa/i)
    ).toBeVisible();

    // Verificar se convite foi enviado
    await expect(
      page.getByText(/convite.*enviado|enviado.*convite/i)
    ).toBeVisible();

    // Verificar se redirecionou para lista ou detalhes
    await page.waitForURL("**/empresas**", { timeout: 10000 });

    console.log("✅ Cadastro de empresa concluído com sucesso!");
  });

  test("validação de CNPJ duplicado", async ({ page, context }) => {
    await context.clearCookies();

    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          is_system_admin: true,
        })
      );
    });

    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");

    // CORREÇÃO: Usar getByLabel para CNPJ
    const cnpjInput = page.getByLabel("CNPJ");
    await cnpjInput.fill("05.514.464/0001-30");

    // CORREÇÃO: Usar getByLabel para outros campos
    const nameInput = page.getByLabel("Razão Social");
    await nameInput.fill("Empresa Teste");

    // Preencher campos obrigatórios mínimos
    const phoneInput = page.locator('input[placeholder*="telefone"]').first();
    await phoneInput.fill("11999999999");

    const emailInput = page.locator('input[type="email"]').first();
    await emailInput.fill("teste@empresa.com");

    const streetInput = page.getByLabel(/logradouro|rua/i);
    await streetInput.fill("Rua Teste");

    const cityInput = page.getByLabel(/cidade/i);
    await cityInput.fill("São Paulo");

    const numberInput = page.getByLabel(/número/i);
    await numberInput.fill("123");

    // Tentar salvar
    const saveButton = page.getByRole("button", { name: /salvar/i });
    await saveButton.click();

    // Verificar erro de CNPJ duplicado
    await expect(
      page.getByText(/CNPJ.*já.*existe|já.*existe.*CNPJ/i)
    ).toBeVisible();
  });

  test("validação de endereço sem número - modal de confirmação", async ({
    page,
    context,
  }) => {
    await context.clearCookies();

    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          is_system_admin: true,
        })
      );
    });

    await page.goto("/admin/empresas?view=create");
    await page.waitForLoadState("networkidle");

    // Preencher CNPJ e nome
    const cnpjInput = page.getByLabel("CNPJ");
    await cnpjInput.fill("12.345.678/0001-90"); // CNPJ fictício

    const nameInput = page.getByLabel("Razão Social");
    await nameInput.fill("Empresa Sem Número");

    // Preencher telefone
    const phoneInput = page.locator('input[placeholder*="telefone"]').first();
    await phoneInput.fill("11999999999");

    // Preencher email
    const emailInput = page.locator('input[type="email"]').first();
    await emailInput.fill("teste@empresa.com");

    // Preencher endereço SEM número
    const streetInput = page.getByLabel(/logradouro|rua/i);
    await streetInput.fill("Rua Sem Número");

    const cityInput = page.getByLabel(/cidade/i);
    await cityInput.fill("São Paulo");

    // Deixar número vazio propositalmente para testar modal

    // Tentar salvar
    const saveButton = page.getByRole("button", { name: /salvar/i });
    await saveButton.click();

    // Verificar modal de confirmação
    await expect(
      page.getByText(/endereço.*sem.*número|número.*endereço/i)
    ).toBeVisible();

    // Confirmar no modal
    const confirmButton = page.getByRole("button", {
      name: /confirmar|continuar|sim/i,
    });
    await confirmButton.click();

    // Verificar sucesso
    await expect(
      page.getByText(/empresa.*sucesso|sucesso.*empresa/i)
    ).toBeVisible();
  });

  test("debug - verificar estrutura da página", async ({ page, context }) => {
    // Teste para debugar elementos disponíveis
    await context.clearCookies();

    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          is_system_admin: true,
        })
      );
    });

    await page.goto("/admin/empresas");
    await page.waitForLoadState("networkidle");

    // Capturar screenshot da página inicial
    await page.screenshot({ path: "debug-empresas-page.png", fullPage: true });

    // Listar todos os botões disponíveis
    const buttons = await page.locator("button").allTextContents();
    console.log("Botões encontrados:", buttons);

    // Tentar encontrar botão de nova empresa
    const newButton = page.locator(
      'button:has-text("Nova"), button:has-text("Adicionar"), button:has-text("Criar")'
    );
    const newButtonCount = await newButton.count();
    console.log(
      "Botões de 'Nova/Adicionar/Criar' encontrados:",
      newButtonCount
    );

    if (newButtonCount > 0) {
      const newButtonText = await newButton.first().textContent();
      console.log("Texto do primeiro botão:", newButtonText);

      await newButton.first().click();
      await page.waitForLoadState("networkidle");

      // Capturar screenshot do formulário
      await page.screenshot({ path: "debug-form-page.png", fullPage: true });

      // Listar todos os inputs disponíveis
      const inputs = await page.locator("input").count();
      console.log("Total de inputs encontrados:", inputs);

      // Listar labels disponíveis
      const labels = await page.locator("label").allTextContents();
      console.log("Labels encontrados:", labels);
    }
  });
});
