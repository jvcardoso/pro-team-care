import { Page, Locator, expect } from "@playwright/test";
import { LoginPage } from "./LoginPage";

export class AdminPage {
  readonly page: Page;
  readonly loginPage: LoginPage;
  readonly sidebar: Locator;
  readonly dynamicSidebar: Locator;
  readonly staticSidebar: Locator;
  readonly developmentControls: Locator;
  readonly toggleMenuButton: Locator;
  readonly toggleUserButton: Locator;
  readonly menuItems: Locator;
  readonly loadingSpinner: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.loginPage = new LoginPage(page);
    this.sidebar = page.locator(
      '[role="navigation"][aria-label="Menu principal"]'
    );
    this.dynamicSidebar = page.locator('[data-testid="dynamic-sidebar"]');
    this.staticSidebar = page.locator('[data-testid="static-sidebar"]');
    this.developmentControls = page.locator(".bg-yellow-100");
    this.toggleMenuButton = page.getByText("Alternar Menus");
    this.toggleUserButton = page.getByText("Alternar Usuário");
    this.menuItems = page.locator(
      '[data-testid="menu-item"], .group.flex.items-center.px-2.py-2'
    );
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  async goto() {
    await this.page.goto("/admin/dashboard");
    await this.page.waitForLoadState("networkidle");

    // Verificar se foi redirecionado para login
    if (await this.loginPage.isOnLoginPage()) {
      console.log(
        "🔐 Redirecionado para login, fazendo login automaticamente..."
      );
      await this.loginPage.login();
    }

    // Aguardar um pouco para estabilizar após possível login
    await this.page.waitForTimeout(1000);
  }

  async waitForMenusToLoad() {
    // Aguardar até que os menus carreguem ou que haja um erro
    try {
      // Primeiro aguardar que o spinner apareça e desapareça
      await this.page.waitForSelector('[data-testid="loading-spinner"]', {
        timeout: 2000,
      });
      await this.page.waitForSelector('[data-testid="loading-spinner"]', {
        state: "hidden",
        timeout: 10000,
      });
    } catch {
      // Se não encontrou spinner, continua
    }

    // Aguardar que os menus apareçam ou que haja mensagem de erro
    await this.page.waitForFunction(
      () => {
        // Procurar por menus dinâmicos ou estáticos
        const dynamicMenus = document.querySelectorAll(
          '[data-testid="menu-item"]'
        );
        const staticMenus = document.querySelectorAll(
          ".group.flex.items-center.px-2.py-2"
        );
        const errorMsg = document.querySelector(
          '[data-testid="error-message"]'
        );
        const totalMenus = dynamicMenus.length + staticMenus.length;

        console.log("Debugando menus:", {
          dynamicMenus: dynamicMenus.length,
          staticMenus: staticMenus.length,
          totalMenus,
          hasError: !!errorMsg,
        });

        return totalMenus > 0 || errorMsg !== null;
      },
      { timeout: 20000 }
    );

    // Pequena pausa para estabilizar
    await this.page.waitForTimeout(500);
  }

  async isDevelopmentModeVisible() {
    return await this.developmentControls.isVisible();
  }

  async getCurrentMenuType(): Promise<string> {
    const text = await this.developmentControls.textContent();
    if (text?.includes("Dinâmicos (API)")) {
      return "dynamic";
    } else if (text?.includes("Estáticos (Mock)")) {
      return "static";
    }
    throw new Error("Não foi possível determinar o tipo de menu atual");
  }

  async getCurrentUserType(): Promise<string> {
    const text = await this.developmentControls.textContent();
    if (text?.includes("ROOT (ID: 2)")) {
      return "root";
    } else if (text?.includes("Normal (ID: 1)")) {
      return "normal";
    }
    throw new Error("Não foi possível determinar o tipo de usuário atual");
  }

  async toggleMenuType() {
    const currentType = await this.getCurrentMenuType();
    await this.toggleMenuButton.click();

    // Aguardar mudança
    await this.page.waitForTimeout(1000);

    const newType = await this.getCurrentMenuType();
    expect(newType).not.toBe(currentType);

    return newType;
  }

  async toggleUserType() {
    const currentType = await this.getCurrentUserType();
    await this.toggleUserButton.click();

    // Aguardar reload da página
    await this.page.waitForLoadState("networkidle");

    const newType = await this.getCurrentUserType();
    expect(newType).not.toBe(currentType);

    return newType;
  }

  async getVisibleMenuCount(): Promise<number> {
    await this.waitForMenusToLoad();
    return await this.menuItems.count();
  }

  async getMenuNames(): Promise<string[]> {
    await this.waitForMenusToLoad();
    const menuElements = await this.menuItems.all();
    const names: string[] = [];

    for (const menu of menuElements) {
      const name = await menu.getAttribute("data-menu-name");
      if (name) {
        names.push(name);
      }
    }

    return names;
  }

  async clickMenu(menuName: string) {
    const menu = this.page.locator(
      `[data-testid="menu-item"][data-menu-name="${menuName}"]`
    );
    await menu.click();
  }

  async expandMenu(menuName: string) {
    const menu = this.page.locator(
      `[data-testid="menu-item"][data-menu-name="${menuName}"]`
    );
    const expandButton = menu.locator('[data-testid="menu-expand-button"]');

    if (await expandButton.isVisible()) {
      await expandButton.click();

      // Aguardar expansão
      await this.page.waitForTimeout(300);
    }
  }

  async getSubMenuCount(parentMenuName: string): Promise<number> {
    const parentMenu = this.page.locator(
      `[data-testid="menu-item"][data-menu-name="${parentMenuName}"]`
    );
    const submenus = parentMenu.locator('[data-testid="submenu-item"]');
    return await submenus.count();
  }

  async hasMenuBadge(menuName: string): Promise<boolean> {
    const menu = this.page.locator(
      `[data-testid="menu-item"][data-menu-name="${menuName}"]`
    );
    const badge = menu.locator('[data-testid="menu-badge"]');
    return await badge.isVisible();
  }

  async getMenuBadgeText(menuName: string): Promise<string> {
    const menu = this.page.locator(
      `[data-testid="menu-item"][data-menu-name="${menuName}"]`
    );
    const badge = menu.locator('[data-testid="menu-badge"]');
    return (await badge.textContent()) || "";
  }

  async isMenuItemActive(menuName: string): Promise<boolean> {
    const menu = this.page.locator(
      `[data-testid="menu-item"][data-menu-name="${menuName}"]`
    );
    const classList = (await menu.getAttribute("class")) || "";
    return classList.includes("active") || classList.includes("bg-blue");
  }

  async hasErrorMessage(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  async getErrorMessage(): Promise<string> {
    return (await this.errorMessage.textContent()) || "";
  }

  async refreshMenus() {
    const refreshButton = this.page.locator(
      '[data-testid="refresh-menus-button"]'
    );
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await this.waitForMenusToLoad();
    }
  }

  async debugPageState() {
    const url = this.page.url();
    const title = await this.page.title();
    const hasAuth = await this.page.evaluate(() => {
      return {
        hasToken: !!localStorage.getItem("access_token"),
        hasUser: !!localStorage.getItem("user"),
        useDynamicMenus: localStorage.getItem("useDynamicMenus"),
        testAsRoot: localStorage.getItem("testAsRoot"),
      };
    });

    const sidebarVisible = await this.sidebar.isVisible();
    const dynamicSidebarVisible = await this.dynamicSidebar.isVisible();
    const staticSidebarVisible = await this.staticSidebar.isVisible();
    const hasSpinner = await this.loadingSpinner.isVisible();
    const hasError = await this.hasErrorMessage();
    const menuCount = await this.menuItems.count();

    console.log("🔍 Debug Estado da Página:", {
      url,
      title,
      auth: hasAuth,
      sidebar: { sidebarVisible, dynamicSidebarVisible, staticSidebarVisible },
      loading: hasSpinner,
      error: hasError,
      menuCount,
    });

    return {
      url,
      title,
      auth: hasAuth,
      sidebar: { sidebarVisible, dynamicSidebarVisible, staticSidebarVisible },
      loading: hasSpinner,
      error: hasError,
      menuCount,
    };
  }

  async validateMenuStructure() {
    await this.waitForMenusToLoad();

    // Debug do estado atual
    const debugInfo = await this.debugPageState();

    // Verificar se há pelo menos alguns menus
    const menuCount = await this.getVisibleMenuCount();

    if (menuCount === 0) {
      // Se não há menus, vamos debuggar mais
      const errorMsg = (await this.hasErrorMessage())
        ? await this.getErrorMessage()
        : "Nenhum erro visível";
      console.error("❌ Nenhum menu encontrado:", {
        menuCount,
        errorMsg,
        debugInfo,
      });
    }

    expect(menuCount).toBeGreaterThan(0);

    // Verificar se não há erros
    expect(await this.hasErrorMessage()).toBeFalsy();

    return {
      menuCount,
      menuNames: await this.getMenuNames(),
    };
  }
}
