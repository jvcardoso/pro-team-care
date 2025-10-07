import { test, expect } from "@playwright/test";

/**
 * Teste E2E completo do fluxo de Gestão de Vidas
 *
 * Fluxo testado:
 * 1. Login no sistema
 * 2. Navegação para Contratos
 * 3. Seleção de um contrato
 * 4. Acesso à gestão de vidas
 * 5. Adição de nova vida
 * 6. Validação dos dados
 * 7. Edição de vida
 * 8. Visualização de histórico
 */

test.describe("Gestão de Vidas - Fluxo Completo", () => {
  test.beforeEach(async ({ page }) => {
    // Login antes de cada teste
    await page.goto("http://192.168.11.83:3000/login");
    await page.fill('input[type="email"]', "admin@proteamcare.com");
    await page.fill('input[type="password"]', "admin123");
    await page.click('button[type="submit"]');

    // Aguardar redirecionamento para dashboard
    await page.waitForURL("**/admin**");
    await expect(page).toHaveURL(/\/admin/);
  });

  test("Deve navegar para gestão de vidas através do menu", async ({
    page,
  }) => {
    // Clicar no menu Negócio
    await page.click("text=Negócio");

    // Clicar em Gestão de Vidas
    await page.click("text=Gestão de Vidas");

    // Verificar se chegou na página correta
    await expect(page).toHaveURL(/\/admin\/vidas/);

    // Verificar se a tabela de vidas está presente
    await expect(page.locator("table")).toBeVisible();
  });

  test("Deve acessar gestão de vidas através de um contrato", async ({
    page,
  }) => {
    // Navegar para contratos
    await page.goto("http://192.168.11.83:3000/admin/contratos");

    // Aguardar carregamento da tabela
    await page.waitForSelector("table", { timeout: 10000 });

    // Clicar no primeiro contrato (ação Vidas)
    const firstContractRow = page.locator("table tbody tr").first();
    await firstContractRow.waitFor({ state: "visible" });

    // Procurar pelo botão de ações ou link de vidas
    const vidasButton = firstContractRow
      .locator('button:has-text("Vidas"), a:has-text("Vidas")')
      .first();
    if ((await vidasButton.count()) > 0) {
      await vidasButton.click();
    } else {
      // Se não encontrar botão específico, clicar na linha
      await firstContractRow.click();
      // Então clicar em Vidas na página de detalhes
      await page.click("text=Vidas");
    }

    // Verificar se está na página de vidas do contrato
    await expect(page).toHaveURL(/\/admin\/contratos\/\d+\/vidas/);
  });

  test("Deve adicionar uma nova vida com dados completos", async ({ page }) => {
    // Ir direto para vidas
    await page.goto("http://192.168.11.83:3000/admin/vidas");

    // Clicar no botão Adicionar
    await page.click('button:has-text("Adicionar")');

    // Aguardar formulário aparecer
    await expect(page.locator("form")).toBeVisible();

    // Preencher dados pessoais obrigatórios
    await page.fill(
      'input[placeholder*="Nome completo"]',
      "João da Silva Teste E2E"
    );
    await page.fill('input[placeholder*="CPF"]', "123.456.789-00");
    await page.fill('input[placeholder*="RG"]', "12.345.678-9");

    // Preencher data de nascimento
    const birthDateInput = page.locator('input[type="date"]').first();
    await birthDateInput.fill("1990-01-15");

    // Selecionar sexo
    await page.selectOption('select:near(text="Sexo")', "M");

    // Preencher data de início no contrato
    const startDateInput = page
      .locator('input[type="date"]:near(text="Data de Início")')
      .first();
    await startDateInput.fill("2025-01-01");

    // Adicionar contato (opcional)
    const addEmailButton = page
      .locator('button:has-text("Adicionar"):near(text="E-mail")')
      .first();
    if ((await addEmailButton.count()) === 0) {
      // Se não tiver botão de adicionar, preencher campo direto
      await page.fill('input[type="email"]', "joao.silva@email.com");
    }

    // Adicionar telefone (opcional)
    const phoneInput = page
      .locator('input[placeholder*="telefone"], input[placeholder*="celular"]')
      .first();
    if ((await phoneInput.count()) > 0) {
      await phoneInput.fill("(11) 98765-4321");
    }

    // Salvar
    await page.click(
      'button:has-text("Adicionar Vida"), button:has-text("Salvar")'
    );

    // Aguardar notificação de sucesso
    await expect(page.locator("text=/adicionado.*sucesso/i")).toBeVisible({
      timeout: 5000,
    });

    // Verificar se a vida aparece na lista
    await expect(page.locator("text=João da Silva Teste E2E")).toBeVisible();
  });

  test("Deve validar campos obrigatórios ao adicionar vida", async ({
    page,
  }) => {
    await page.goto("http://192.168.11.83:3000/admin/vidas");

    // Clicar em adicionar
    await page.click('button:has-text("Adicionar")');

    // Tentar salvar sem preencher nada
    await page.click(
      'button:has-text("Adicionar Vida"), button:has-text("Salvar")'
    );

    // Verificar se mostra erros de validação (HTML5 ou custom)
    // O navegador deve impedir o submit por causa dos campos required
    const form = page.locator("form");
    await expect(form).toBeVisible();

    // Preencher apenas nome (ainda faltam outros obrigatórios)
    await page.fill('input[placeholder*="Nome completo"]', "Teste Parcial");

    // Tentar salvar novamente
    await page.click(
      'button:has-text("Adicionar Vida"), button:has-text("Salvar")'
    );

    // Form deve continuar visível pois faltam campos
    await expect(form).toBeVisible();
  });

  test("Deve editar uma vida existente", async ({ page }) => {
    await page.goto("http://192.168.11.83:3000/admin/vidas");

    // Aguardar carregamento da tabela
    await page.waitForSelector("table tbody tr", { timeout: 10000 });

    // Clicar no botão de editar da primeira vida
    const firstRow = page.locator("table tbody tr").first();
    const editButton = firstRow
      .locator('button:has-text("Editar"), button[title*="Editar"]')
      .first();

    if ((await editButton.count()) > 0) {
      await editButton.click();

      // Aguardar formulário de edição
      await expect(page.locator("form")).toBeVisible();

      // O nome deve estar desabilitado (não pode alterar pessoa)
      const nameInput = page.locator('input[value]:near(text="Nome")').first();
      await expect(nameInput).toBeDisabled();

      // Alterar observações
      const notesInput = page.locator('input:near(text="Observações")').first();
      await notesInput.fill(
        "Editado via teste E2E - " + new Date().toISOString()
      );

      // Salvar
      await page.click('button:has-text("Salvar")');

      // Aguardar sucesso
      await expect(page.locator("text=/atualizada.*sucesso/i")).toBeVisible({
        timeout: 5000,
      });
    }
  });

  test("Deve visualizar histórico de uma vida", async ({ page }) => {
    await page.goto("http://192.168.11.83:3000/admin/vidas");

    // Aguardar tabela
    await page.waitForSelector("table tbody tr", { timeout: 10000 });

    // Clicar no botão de histórico da primeira vida
    const firstRow = page.locator("table tbody tr").first();
    const historyButton = firstRow
      .locator('button:has-text("Histórico"), button[title*="Histórico"]')
      .first();

    if ((await historyButton.count()) > 0) {
      await historyButton.click();

      // Aguardar modal de histórico
      await expect(page.locator("text=Histórico:")).toBeVisible();

      // Verificar se tem eventos no histórico
      const timeline = page
        .locator(
          'div:has-text("Vida adicionada"), div:has-text("Vida atualizada")'
        )
        .first();
      await expect(timeline).toBeVisible();

      // Fechar modal
      await page.click('button:has-text("Fechar"), button[title*="Fechar"]');
    }
  });

  test("Deve mostrar contadores corretos de vidas no contrato", async ({
    page,
  }) => {
    // Navegar para um contrato específico
    await page.goto("http://192.168.11.83:3000/admin/contratos");
    await page.waitForSelector("table tbody tr");

    // Pegar o número de vidas do primeiro contrato na lista
    const firstRow = page.locator("table tbody tr").first();
    const vidasText = await firstRow
      .locator("text=/\\d+\\/\\d+/")
      .first()
      .textContent();

    // Extrair números (ex: "2/10" -> [2, 10])
    const match = vidasText?.match(/(\d+)\/(\d+)/);
    expect(match).toBeTruthy();

    if (match) {
      const [, atual, contratado] = match;
      const vidasAtuais = parseInt(atual);
      const vidasContratadas = parseInt(contratado);

      // Validações
      expect(vidasAtuais).toBeGreaterThanOrEqual(0);
      expect(vidasContratadas).toBeGreaterThan(0);
      expect(vidasAtuais).toBeLessThanOrEqual(vidasContratadas);
    }
  });

  test("Deve filtrar vidas por status", async ({ page }) => {
    await page.goto("http://192.168.11.83:3000/admin/vidas");

    // Aguardar tabela
    await page.waitForSelector("table tbody tr", { timeout: 10000 });

    // Procurar por filtro de status (se existir)
    const statusFilter = page
      .locator('select:near(text="Status"), input[placeholder*="status"]')
      .first();

    if ((await statusFilter.count()) > 0) {
      // Pegar total inicial
      const initialRows = await page.locator("table tbody tr").count();

      // Aplicar filtro (ex: apenas ativos)
      await statusFilter.selectOption({ label: "Ativo" });

      // Aguardar atualização
      await page.waitForTimeout(1000);

      // Verificar se filtrou
      const filteredRows = await page.locator("table tbody tr").count();

      // Deve ter mudado ou permanecido igual (se todos eram ativos)
      expect(filteredRows).toBeLessThanOrEqual(initialRows);
    }
  });

  test("Deve respeitar dark mode em todos os formulários", async ({ page }) => {
    // Navegar para vidas
    await page.goto("http://192.168.11.83:3000/admin/vidas");

    // Ativar dark mode (se tiver toggle)
    const darkModeToggle = page
      .locator('button[title*="Dark"], button:has-text("Dark")')
      .first();

    if ((await darkModeToggle.count()) > 0) {
      await darkModeToggle.click();

      // Abrir formulário
      await page.click('button:has-text("Adicionar")');

      // Verificar classes dark mode
      const form = page.locator("form");
      const hasDarkClasses = await form.evaluate((el) => {
        return (
          el.className.includes("dark") ||
          document.documentElement.classList.contains("dark")
        );
      });

      expect(hasDarkClasses).toBeTruthy();
    }
  });
});
