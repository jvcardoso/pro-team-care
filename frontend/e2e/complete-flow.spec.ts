import { test, expect } from "@playwright/test";
import { AdminPage } from "./pages/AdminPage";

test.describe("Fluxo Completo E2E", () => {
  test("fluxo completo: login → menus dinâmicos → navegação → alteração de usuário", async ({
    page,
    context,
  }) => {
    // Limpar qualquer estado anterior
    await context.clearCookies();
    await context.clearPermissions();

    // 1. FASE: Verificação de conectividade
    console.log("🔍 Verificando conectividade...");

    // Verificar se backend está acessível
    const healthResponse = await page.request.get(
      "http://192.168.11.83:8000/api/v1/health"
    );
    expect(healthResponse.status()).toBe(200);

    // Verificar se frontend está acessível
    await page.goto("/");
    await expect(page).toHaveTitle(/Pro Team Care/);

    console.log("✅ Conectividade OK");

    // 2. FASE: Simulação de Login
    console.log("🔐 Simulando processo de login...");

    // Configurar estado de autenticação
    await page.addInitScript(() => {
      // Simular token JWT válido
      const mockToken =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6OTk5OTk5OTk5OX0.mock-signature";

      localStorage.setItem("access_token", mockToken);
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          name: "Admin Teste",
          is_system_admin: false,
          person_type: "PF",
        })
      );
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "false");
    });

    console.log("✅ Autenticação configurada");

    // 3. FASE: Navegação para área administrativa
    console.log("🏠 Navegando para área administrativa...");

    const adminPage = new AdminPage(page);
    await adminPage.goto();

    // Verificar se chegamos na área correta
    await expect(page).toHaveURL(/.*\/admin\/dashboard/);
    console.log("✅ Área administrativa acessada");

    // 4. FASE: Validação de menus dinâmicos - Usuário Normal
    console.log("📋 Testando menus dinâmicos para usuário normal...");

    await adminPage.waitForMenusToLoad();

    // Verificar controles de desenvolvimento
    const isDevMode = await adminPage.isDevelopmentModeVisible();
    expect(isDevMode).toBeTruthy();

    // Verificar usuário inicial
    const userType = await adminPage.getCurrentUserType();
    expect(userType).toBe("normal");

    // Verificar modo de menu
    const menuType = await adminPage.getCurrentMenuType();
    expect(menuType).toBe("dynamic");

    // Validar estrutura de menus para usuário normal
    const normalMenus = await adminPage.validateMenuStructure();
    expect(normalMenus.menuCount).toBeGreaterThan(0);
    expect(normalMenus.menuCount).toBeLessThanOrEqual(8); // Usuário normal tem menos menus

    console.log(`✅ Usuário normal: ${normalMenus.menuCount} menus carregados`);

    // 5. FASE: Navegação e interação com menus
    console.log("🧭 Testando navegação nos menus...");

    // Expandir menu Dashboard
    await adminPage.expandMenu("Dashboard");
    const dashboardSubmenus = await adminPage.getSubMenuCount("Dashboard");
    expect(dashboardSubmenus).toBeGreaterThan(0);

    // Navegar para Dashboard v2
    await adminPage.clickMenu("Dashboard v2");
    await expect(page).toHaveURL(/.*\/admin\/dashboard-v2/);

    console.log("✅ Navegação funcionando");

    // 6. FASE: Alternância para usuário ROOT
    console.log("👑 Alternando para usuário ROOT...");

    // Voltar para área principal
    await adminPage.goto();

    // Alternar para ROOT
    await adminPage.toggleUserType();

    // Aguardar recarregamento
    await adminPage.waitForMenusToLoad();

    // Verificar mudança para ROOT
    const rootUserType = await adminPage.getCurrentUserType();
    expect(rootUserType).toBe("root");

    // Validar menus do ROOT (deve ter mais menus)
    const rootMenus = await adminPage.validateMenuStructure();
    expect(rootMenus.menuCount).toBeGreaterThan(normalMenus.menuCount);

    // Verificar menus específicos do ROOT
    expect(rootMenus.menuNames).toContain("Administração");

    console.log(
      `✅ ROOT: ${rootMenus.menuCount} menus carregados (${
        rootMenus.menuCount - normalMenus.menuCount
      } a mais)`
    );

    // 7. FASE: Teste de alternância de modo de menu
    console.log("🔧 Testando alternância de modos de menu...");

    // Alternar para menus estáticos
    const staticMode = await adminPage.toggleMenuType();
    expect(staticMode).toBe("static");

    // Validar menus estáticos
    await adminPage.waitForMenusToLoad();
    const staticMenus = await adminPage.validateMenuStructure();
    expect(staticMenus.menuCount).toBeGreaterThan(0);

    // Voltar para dinâmicos
    const dynamicMode = await adminPage.toggleMenuType();
    expect(dynamicMode).toBe("dynamic");

    console.log("✅ Alternância de modos funcionando");

    // 8. FASE: Teste de responsividade
    console.log("📱 Testando responsividade...");

    // Desktop
    await page.setViewportSize({ width: 1280, height: 720 });
    await adminPage.waitForMenusToLoad();
    let responsiveMenus = await adminPage.validateMenuStructure();
    expect(responsiveMenus.menuCount).toBeGreaterThan(0);

    // Tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await adminPage.waitForMenusToLoad();
    responsiveMenus = await adminPage.validateMenuStructure();
    expect(responsiveMenus.menuCount).toBeGreaterThan(0);

    // Mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await adminPage.waitForMenusToLoad();
    responsiveMenus = await adminPage.validateMenuStructure();
    expect(responsiveMenus.menuCount).toBeGreaterThan(0);

    console.log("✅ Responsividade validada");

    // 9. FASE: Teste de performance
    console.log("⚡ Verificando performance...");

    // Voltar para desktop
    await page.setViewportSize({ width: 1280, height: 720 });

    // Medir tempo de carregamento dos menus
    const startTime = Date.now();
    await adminPage.goto();
    await adminPage.waitForMenusToLoad();
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(5000); // Menus devem carregar em menos de 5s
    console.log(`✅ Menus carregaram em ${loadTime}ms`);

    // 10. FASE: Validação final
    console.log("🎯 Validação final do sistema...");

    // Verificar que não há erros na página
    const hasErrors = await adminPage.hasErrorMessage();
    expect(hasErrors).toBeFalsy();

    // Verificar que sidebar está visível e funcional
    const sidebarVisible = await adminPage.sidebar.isVisible();
    expect(sidebarVisible).toBeTruthy();

    // Teste final: navegar por diferentes seções
    const testNavigations = [
      { menu: "Dashboard v1", expectedUrl: /.*\/admin\/dashboard/ },
      { menu: "Charts", expectedUrl: /.*\/admin\/charts/ },
      { menu: "Widgets", expectedUrl: /.*\/admin\/widgets/ },
    ];

    for (const nav of testNavigations) {
      await adminPage.clickMenu(nav.menu);
      await expect(page).toHaveURL(nav.expectedUrl);

      // Verificar que menus permanecem carregados após navegação
      const menuCount = await adminPage.getVisibleMenuCount();
      expect(menuCount).toBeGreaterThan(0);
    }

    console.log("🎉 FLUXO COMPLETO E2E FINALIZADO COM SUCESSO!");

    // Relatório final
    const finalReport = {
      normalUserMenus: normalMenus.menuCount,
      rootUserMenus: rootMenus.menuCount,
      loadTime: `${loadTime}ms`,
      responsiveTested: "✅",
      navigationTested: "✅",
      performanceOK: loadTime < 5000 ? "✅" : "❌",
    };

    console.log("📊 RELATÓRIO FINAL:", JSON.stringify(finalReport, null, 2));
  });

  test("fluxo de recuperação de erro", async ({ page }) => {
    console.log("🚨 Testando fluxo de recuperação de erros...");

    // Configurar interceptação para simular erro na API
    await page.route("**/api/v1/menus/**", (route) => {
      // Simular erro 500 na primeira chamada
      if (!route.request().url().includes("retry=true")) {
        route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Simulated server error" }),
        });
      } else {
        route.continue();
      }
    });

    // Configurar autenticação
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem("user", JSON.stringify({ id: 1, name: "Test" }));
      localStorage.setItem("useDynamicMenus", "true");
    });

    const adminPage = new AdminPage(page);
    await adminPage.goto();

    // Deve usar fallback e ainda funcionar
    await adminPage.waitForMenusToLoad();
    const result = await adminPage.validateMenuStructure();

    expect(result.menuCount).toBeGreaterThan(0);
    console.log("✅ Sistema se recuperou do erro graciosamente");
  });
});
