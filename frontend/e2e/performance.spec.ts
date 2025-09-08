import { test, expect } from "@playwright/test";
import { AdminPage } from "./pages/AdminPage";

test.describe("Testes de Performance", () => {
  test("deve carregar menus dinâmicos dentro do tempo limite", async ({
    page,
  }) => {
    // Configurar autenticação
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({ id: 1, name: "Test User" })
      );
      localStorage.setItem("useDynamicMenus", "true");
    });

    const adminPage = new AdminPage(page);

    // Medir tempo de carregamento
    const startTime = Date.now();
    await adminPage.goto();
    await adminPage.waitForMenusToLoad();
    const endTime = Date.now();

    const loadTime = endTime - startTime;

    // Menus devem carregar em menos de 3 segundos
    expect(loadTime).toBeLessThan(3000);

    console.log(`✅ Menus carregaram em ${loadTime}ms`);
  });

  test("deve manter performance ao alternar entre usuários múltiplas vezes", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({ id: 1, name: "Test User" })
      );
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "false");
    });

    const adminPage = new AdminPage(page);
    await adminPage.goto();

    const iterations = 3;
    const times: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const startTime = Date.now();

      // Alternar usuário
      await adminPage.toggleUserType();
      await adminPage.waitForMenusToLoad();

      const endTime = Date.now();
      const switchTime = endTime - startTime;
      times.push(switchTime);

      console.log(`Alternância ${i + 1}: ${switchTime}ms`);
    }

    // Calcular média
    const avgTime = times.reduce((a, b) => a + b) / times.length;

    // Performance deve se manter consistente (< 5s por alternância)
    expect(avgTime).toBeLessThan(5000);

    console.log(`✅ Tempo médio de alternância: ${avgTime.toFixed(2)}ms`);
  });

  test("deve ser eficiente em múltiplas navegações", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({ id: 2, is_system_admin: true })
      );
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "true");
    });

    const adminPage = new AdminPage(page);
    await adminPage.goto();
    await adminPage.waitForMenusToLoad();

    // Testar navegação rápida entre múltiplas páginas
    const routes = [
      "/admin/dashboard",
      "/admin/dashboard-v2",
      "/admin/charts",
      "/admin/widgets",
    ];

    const navigationTimes: number[] = [];

    for (const route of routes) {
      const startTime = Date.now();
      await page.goto(route);
      await page.waitForLoadState("networkidle");
      const endTime = Date.now();

      const navTime = endTime - startTime;
      navigationTimes.push(navTime);

      // Verificar se menus ainda estão carregados
      const menuCount = await adminPage.getVisibleMenuCount();
      expect(menuCount).toBeGreaterThan(0);
    }

    // Navegação média deve ser rápida
    const avgNavTime =
      navigationTimes.reduce((a, b) => a + b) / navigationTimes.length;
    expect(avgNavTime).toBeLessThan(2000);

    console.log(`✅ Tempo médio de navegação: ${avgNavTime.toFixed(2)}ms`);
  });

  test("deve ter boa performance em diferentes tamanhos de tela", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({ id: 2, is_system_admin: true })
      );
      localStorage.setItem("useDynamicMenus", "true");
    });

    const adminPage = new AdminPage(page);

    const viewports = [
      { width: 1920, height: 1080, name: "Desktop HD" },
      { width: 1280, height: 720, name: "Desktop" },
      { width: 768, height: 1024, name: "Tablet" },
      { width: 375, height: 667, name: "Mobile" },
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });

      const startTime = Date.now();
      await adminPage.goto();
      await adminPage.waitForMenusToLoad();
      const endTime = Date.now();

      const loadTime = endTime - startTime;

      // Performance deve ser boa em todas as resoluções
      expect(loadTime).toBeLessThan(4000);

      // Verificar se menus estão visíveis
      const menuCount = await adminPage.getVisibleMenuCount();
      expect(menuCount).toBeGreaterThan(0);

      console.log(
        `✅ ${viewport.name} (${viewport.width}x${viewport.height}): ${loadTime}ms`
      );
    }
  });

  test("deve lidar eficientemente com cache de menus", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock-token");
      localStorage.setItem(
        "user",
        JSON.stringify({ id: 1, name: "Test User" })
      );
      localStorage.setItem("useDynamicMenus", "true");
    });

    const adminPage = new AdminPage(page);

    // Primeira carga (sem cache)
    let startTime = Date.now();
    await adminPage.goto();
    await adminPage.waitForMenusToLoad();
    let endTime = Date.now();
    const firstLoadTime = endTime - startTime;

    // Segunda carga (com cache)
    startTime = Date.now();
    await page.reload();
    await adminPage.waitForMenusToLoad();
    endTime = Date.now();
    const cachedLoadTime = endTime - startTime;

    // Cache deve melhorar performance
    expect(cachedLoadTime).toBeLessThanOrEqual(firstLoadTime + 1000); // Margem de tolerância

    console.log(
      `✅ Primeira carga: ${firstLoadTime}ms, Com cache: ${cachedLoadTime}ms`
    );
  });
});
