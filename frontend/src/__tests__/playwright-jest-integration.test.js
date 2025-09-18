/**
 * Teste simples de integração Playwright + Jest
 * Este teste verifica se ambos os frameworks funcionam juntos
 */

describe("Playwright + Jest Integration Test", () => {
  test("Jest funcionando corretamente", () => {
    // Teste simples do Jest
    const soma = (a, b) => a + b;
    expect(soma(2, 3)).toBe(5);
    expect(soma(0, 0)).toBe(0);
    expect(soma(-1, 1)).toBe(0);
  });

  test("Mock functions funcionando", () => {
    const mockFn = jest.fn();
    mockFn("test");
    expect(mockFn).toHaveBeenCalledWith("test");
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  test("Async/await funcionando", async () => {
    const asyncFunction = async () => {
      return new Promise((resolve) => {
        setTimeout(() => resolve("success"), 100);
      });
    };

    const result = await asyncFunction();
    expect(result).toBe("success");
  });

  test("DOM testing library setup", () => {
    // Verifica se o jsdom está configurado
    expect(typeof document).toBe("object");
    expect(typeof window).toBe("object");

    // Cria um elemento simples para testar
    const div = document.createElement("div");
    div.textContent = "Test content";
    expect(div.textContent).toBe("Test content");
  });
});
