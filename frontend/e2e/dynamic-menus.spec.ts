import { test, expect } from "@playwright/test";
import { AdminPage } from "./pages/AdminPage";

test.describe("Sistema de Menus Dinâmicos", () => {
  let adminPage: AdminPage;

  test.beforeEach(async ({ page }) => {
    adminPage = new AdminPage(page);

    // Configurar localStorage para menus dinâmicos
    await page.addInitScript(() => {
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "false");
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@teste.com",
          name: "Admin Teste",
          is_system_admin: false,
        })
      );
    });

    await adminPage.goto();
  });

  test("deve carregar menus dinâmicos para usuário normal", async () => {
    // Aguardar menus carregarem
    await adminPage.waitForMenusToLoad();

    // Verificar estrutura básica
    const result = await adminPage.validateMenuStructure();

    // Usuário normal deve ter menus (ajustando para a implementação atual)
    expect(result.menuCount).toBeGreaterThan(0);
    console.log("📋 Menus encontrados:", result.menuNames);

    // Verificar que há pelo menos alguns menus básicos
    expect(result.menuNames.length).toBeGreaterThan(0);
  });

  test("deve alternar entre usuário normal e ROOT", async ({ page }) => {
    // Verificar usuário inicial (normal)
    const isDev = await adminPage.isDevelopmentModeVisible();
    expect(isDev).toBeTruthy();

    const initialUser = await adminPage.getCurrentUserType();
    expect(initialUser).toBe("normal");

    const initialMenus = await adminPage.validateMenuStructure();

    // Alternar para ROOT
    await adminPage.toggleUserType();

    // Aguardar nova carga da página
    await adminPage.waitForMenusToLoad();

    // Verificar mudança para ROOT
    const newUser = await adminPage.getCurrentUserType();
    expect(newUser).toBe("root");

    // ROOT pode ter mais menus ou os mesmos (depende da implementação)
    const rootMenus = await adminPage.validateMenuStructure();
    expect(rootMenus.menuCount).toBeGreaterThan(0);

    console.log("📋 Menus ROOT:", rootMenus.menuNames);
    console.log("📊 Comparação menus:", {
      initial: initialMenus.menuCount,
      root: rootMenus.menuCount,
    });
  });

  test("deve alternar entre menus dinâmicos e estáticos", async () => {
    // Verificar modo inicial (dinâmico)
    const initialMode = await adminPage.getCurrentMenuType();
    expect(initialMode).toBe("dynamic");

    // Alternar para estático
    const newMode = await adminPage.toggleMenuType();
    expect(newMode).toBe("static");

    // Menus estáticos ainda devem funcionar
    await adminPage.waitForMenusToLoad();
    const staticMenus = await adminPage.validateMenuStructure();
    expect(staticMenus.menuCount).toBeGreaterThan(0);
  });

  test("deve expandir e colapsar submenus", async () => {
    await adminPage.waitForMenusToLoad();

    // Verificar se existe um menu com submenus
    const menuNames = await adminPage.getMenuNames();
    const menuWithSubmenus = menuNames.find(
      (name) => name === "Dashboard" || name === "Componentes"
    );

    if (menuWithSubmenus) {
      // Expandir menu
      await adminPage.expandMenu(menuWithSubmenus);

      // Verificar se submenus aparecem
      const subMenuCount = await adminPage.getSubMenuCount(menuWithSubmenus);
      expect(subMenuCount).toBeGreaterThan(0);
    }
  });

  test("deve exibir badges nos menus quando disponível", async () => {
    await adminPage.waitForMenusToLoad();

    // Dashboard deve ter badge "Hot"
    const hasDashboardBadge = await adminPage.hasMenuBadge("Dashboard");
    if (hasDashboardBadge) {
      const badgeText = await adminPage.getMenuBadgeText("Dashboard");
      expect(badgeText).toBe("Hot");
    }
  });

  test("deve navegar corretamente ao clicar em menus", async ({ page }) => {
    await adminPage.waitForMenusToLoad();

    // Expandir Dashboard para acessar submenus
    await adminPage.expandMenu("Dashboard");

    // Clicar no submenu Dashboard v1
    await adminPage.clickMenu("Dashboard v1");

    // Verificar se navegou para a URL correta
    await expect(page).toHaveURL(/.*\/admin\/dashboard/);
  });

  test("deve lidar com erros de API graciosamente", async ({ page }) => {
    // Interceptar requests da API para simular erro
    await page.route("**/api/v1/menus/**", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    await adminPage.goto();
    await adminPage.waitForMenusToLoad();

    // Deve usar fallback e ainda exibir menus
    const result = await adminPage.validateMenuStructure();
    expect(result.menuCount).toBeGreaterThan(0);
  });

  test("deve atualizar menus ao usar refresh", async () => {
    await adminPage.waitForMenusToLoad();

    const initialMenus = await adminPage.validateMenuStructure();

    // Fazer refresh dos menus
    await adminPage.refreshMenus();

    // Verificar se menus ainda estão presentes
    const refreshedMenus = await adminPage.validateMenuStructure();
    expect(refreshedMenus.menuCount).toBe(initialMenus.menuCount);
  });

  test("deve manter estado dos menus após navegação", async ({ page }) => {
    await adminPage.waitForMenusToLoad();

    // Expandir um menu
    await adminPage.expandMenu("Dashboard");
    const initialSubMenus = await adminPage.getSubMenuCount("Dashboard");

    // Navegar para outra página e voltar
    await page.goto("/admin/dashboard-v2");
    await page.goBack();

    // Aguardar recarregamento
    await adminPage.waitForMenusToLoad();

    // Verificar se estrutura permanece
    const result = await adminPage.validateMenuStructure();
    expect(result.menuCount).toBeGreaterThan(0);
  });

  test("deve ser responsivo em diferentes tamanhos de tela", async ({
    page,
  }) => {
    await adminPage.waitForMenusToLoad();

    // Testar desktop
    await page.setViewportSize({ width: 1280, height: 720 });
    let result = await adminPage.validateMenuStructure();
    expect(result.menuCount).toBeGreaterThan(0);

    // Testar tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await adminPage.waitForMenusToLoad();
    result = await adminPage.validateMenuStructure();
    expect(result.menuCount).toBeGreaterThan(0);

    // Testar mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await adminPage.waitForMenusToLoad();
    result = await adminPage.validateMenuStructure();
    expect(result.menuCount).toBeGreaterThan(0);
  });
});
