import { chromium, FullConfig } from "@playwright/test";

async function globalSetup(config: FullConfig) {
  console.log("🚀 Iniciando setup global dos testes E2E...");

  // Verificar se o backend está rodando
  const backendUrl = "http://192.168.11.83:8000";

  try {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    // Verificar health do backend
    console.log("🔍 Verificando backend...");
    const response = await page.request.get(`${backendUrl}/api/v1/health`);

    if (!response.ok()) {
      throw new Error(`Backend não está respondendo: ${response.status()}`);
    }

    console.log("✅ Backend está funcionando");

    // Fazer login e salvar auth state
    console.log("🔐 Preparando autenticação...");

    // Navegar para o frontend primeiro
    await page.goto("http://192.168.11.83:3000");

    const loginResponse = await page.request.post(
      `${backendUrl}/api/v1/auth/login`,
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        data: "username=admin@example.com&password=password",
      }
    );

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();

      // Salvar token para usar nos testes
      const authState = {
        access_token: loginData.access_token,
        user: {
          id: 1,
          email: "admin@example.com",
          name: "Admin Teste",
        },
      };

      // Adicionar localStorage com dados necessários
      await page.addInitScript((authData) => {
        localStorage.setItem("access_token", authData.access_token);
        localStorage.setItem("user", JSON.stringify(authData.user));
        localStorage.setItem("useDynamicMenus", "true");
        localStorage.setItem("testAsRoot", "false");
      }, authState);

      // Configurar localStorage diretamente na página
      await page.evaluate((authData) => {
        localStorage.setItem("access_token", authData.access_token);
        localStorage.setItem("user", JSON.stringify(authData.user));
        localStorage.setItem("useDynamicMenus", "true");
        localStorage.setItem("testAsRoot", "false");
      }, authState);

      // Salvar estado de auth para uso nos testes
      await page
        .context()
        .storageState({ path: "e2e/fixtures/auth-state.json" });

      console.log("✅ Autenticação preparada");
    }

    await browser.close();
  } catch (error) {
    console.error("❌ Erro no setup global:", error);
    throw error;
  }

  console.log("🎯 Setup global concluído");
}

export default globalSetup;
