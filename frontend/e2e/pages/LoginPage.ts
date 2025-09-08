import { Page, Locator } from "@playwright/test";

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('input[name="email"], input[type="email"]');
    this.passwordInput = page.locator(
      'input[name="password"], input[type="password"]'
    );
    this.submitButton = page.locator('button[type="submit"]');
  }

  async goto() {
    await this.page.goto("/login");
    await this.page.waitForLoadState("networkidle");
  }

  async login(
    email: string = "admin@example.com",
    password: string = "password"
  ) {
    await this.goto();

    // Aguardar formulário aparecer
    await this.emailInput.waitFor({ state: "visible" });

    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();

    // Aguardar redirecionamento para dashboard
    await this.page.waitForURL("**/admin*", { timeout: 10000 });
    await this.page.waitForLoadState("networkidle");

    // Aguardar um pouco para estabilizar
    await this.page.waitForTimeout(1000);
  }

  async isOnLoginPage(): Promise<boolean> {
    return this.page.url().includes("/login");
  }
}
