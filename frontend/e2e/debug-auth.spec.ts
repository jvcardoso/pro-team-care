import { test, expect } from "@playwright/test";

test.describe("Debug Authentication", () => {
  test("debug auth state and page flow", async ({ page }) => {
    console.log("🔍 Iniciando debug de autenticação...");

    // Configurar localStorage antes de navegar
    await page.goto("http://192.168.11.83:3000");

    // Adicionar dados de autenticação
    await page.evaluate(() => {
      localStorage.setItem("access_token", "fake-token-for-debug");
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: 1,
          email: "admin@example.com",
          name: "Admin Teste",
        })
      );
      localStorage.setItem("useDynamicMenus", "true");
      localStorage.setItem("testAsRoot", "false");
    });

    // Navegar para dashboard
    console.log("🏠 Navegando para /admin/dashboard...");
    await page.goto("http://192.168.11.83:3000/admin/dashboard");

    // Aguardar carregamento
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    // Debug estado atual
    const url = page.url();
    const title = await page.title();
    console.log("📄 URL atual:", url);
    console.log("📄 Título:", title);

    // Verificar localStorage
    const authState = await page.evaluate(() => ({
      hasToken: !!localStorage.getItem("access_token"),
      hasUser: !!localStorage.getItem("user"),
      useDynamicMenus: localStorage.getItem("useDynamicMenus"),
      token: localStorage.getItem("access_token"),
    }));
    console.log("🔐 Estado Auth:", authState);

    // Verificar elementos na página
    const pageElements = await page.evaluate(() => {
      const elements = {
        hasSidebar: !!document.querySelector('[role="navigation"]'),
        hasDynamicSidebar: !!document.querySelector(
          '[data-testid="dynamic-sidebar"]'
        ),
        hasStaticSidebar: !!document.querySelector(
          '[data-testid="static-sidebar"]'
        ),
        hasMenuItems: document.querySelectorAll('[data-testid="menu-item"]')
          .length,
        hasSpinner: !!document.querySelector('[data-testid="loading-spinner"]'),
        hasError: !!document.querySelector('[data-testid="error-message"]'),
        hasDevControls: !!document.querySelector(".bg-yellow-100"),
        bodyHTML: document.body.innerHTML.substring(0, 500),
      };

      return elements;
    });

    console.log("🔧 Elementos da página:", pageElements);

    // Screenshot para debug
    await page.screenshot({ path: "debug-auth-state.png", fullPage: true });

    // Se estamos na página de login, tentar fazer login
    if (url.includes("/login")) {
      console.log("🔑 Página de login detectada, tentando fazer login...");

      await page.fill(
        'input[name="email"], input[type="email"]',
        "admin@example.com"
      );
      await page.fill(
        'input[name="password"], input[type="password"]',
        "password"
      );
      await page.click('button[type="submit"]');

      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(2000);

      const newUrl = page.url();
      console.log("📄 Nova URL após login:", newUrl);

      // Screenshot após login
      await page.screenshot({ path: "debug-after-login.png", fullPage: true });
    }
  });
});
