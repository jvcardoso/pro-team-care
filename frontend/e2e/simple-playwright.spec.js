/**
 * Teste simples do Playwright para verificar funcionalidade básica
 * Este teste pode ser executado independentemente do backend
 */

const { test, expect } = require("@playwright/test");

test.describe("Playwright Simple Test", () => {
  test("should load a basic page and check title", async ({ page }) => {
    // Navega para uma página simples (exemplo.com como fallback)
    await page.goto("https://example.com");

    // Verifica se o título contém "Example"
    await expect(page).toHaveTitle(/Example/);

    // Verifica se a página carregou
    const heading = page.locator("h1");
    await expect(heading).toBeVisible();
  });

  test("should handle basic interactions", async ({ page }) => {
    // Cria uma página HTML simples no momento
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head><title>Test Page</title></head>
        <body>
          <h1 id="title">Test Title</h1>
          <button id="test-btn">Click Me</button>
          <div id="result" style="display: none;">Clicked!</div>
          <script>
            document.getElementById('test-btn').addEventListener('click', () => {
              document.getElementById('result').style.display = 'block';
            });
          </script>
        </body>
      </html>
    `);

    // Verifica elementos
    await expect(page.locator("#title")).toHaveText("Test Title");

    // Testa interação
    await page.click("#test-btn");
    await expect(page.locator("#result")).toBeVisible();
    await expect(page.locator("#result")).toHaveText("Clicked!");
  });

  test("should handle form inputs", async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <form id="test-form">
            <input type="text" id="name" placeholder="Enter name" />
            <input type="email" id="email" placeholder="Enter email" />
            <button type="submit">Submit</button>
          </form>
          <div id="output"></div>
          <script>
            document.getElementById('test-form').addEventListener('submit', (e) => {
              e.preventDefault();
              const name = document.getElementById('name').value;
              const email = document.getElementById('email').value;
              document.getElementById('output').textContent = \`Name: \${name}, Email: \${email}\`;
            });
          </script>
        </body>
      </html>
    `);

    // Preenche formulário
    await page.fill("#name", "João Silva");
    await page.fill("#email", "joao@example.com");
    await page.click("button[type=submit]");

    // Verifica resultado
    await expect(page.locator("#output")).toHaveText(
      "Name: João Silva, Email: joao@example.com"
    );
  });
});
