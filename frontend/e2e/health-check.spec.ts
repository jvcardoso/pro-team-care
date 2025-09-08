import { test, expect } from "@playwright/test";

test.describe("Health Check E2E", () => {
  test("deve verificar que backend está funcionando", async ({ page }) => {
    // Teste simples de conectividade
    const response = await page.request.get(
      "http://192.168.11.83:8000/api/v1/health"
    );
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.status).toBe("healthy");
  });

  test("deve acessar o frontend", async ({ page }) => {
    // Teste simples do frontend
    await page.goto("/");

    // Verificar se a página carregou
    await expect(page).toHaveTitle(/Pro Team Care/);

    // Verificar se contém React
    const content = await page.content();
    expect(content).toContain("vite");
  });
});
