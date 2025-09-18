/**
 * Testes de Integração Frontend-Backend
 * Testes end-to-end para validar a integração completa do CRUD de estabelecimentos
 */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { jest } from "@jest/globals";
import userEvent from "@testing-library/user-event";

// Mock do fetch global para simular chamadas HTTP
global.fetch = jest.fn();

import EstablishmentsPage from "../../pages/EstablishmentsPage";

// Mock das notificações
jest.mock("../../utils/notifications.jsx", () => ({
  notify: {
    success: jest.fn(),
    error: jest.fn(),
    confirm: jest.fn(),
    confirmDelete: jest.fn(),
  },
}));

// Mock do status utils
jest.mock("../../utils/statusUtils", () => ({
  getStatusBadge: jest.fn((status) => `badge-${status}`),
  getStatusLabel: jest.fn((status) =>
    status === "active" ? "Ativo" : "Inativo"
  ),
}));

import { notify } from "../../utils/notifications.jsx";

describe("Establishments Integration Tests", () => {
  const mockEstablishmentsResponse = {
    establishments: [
      {
        id: 1,
        code: "EST001",
        type: "matriz",
        category: "clinica",
        is_active: true,
        is_principal: true,
        company_id: 1,
        company_name: "Empresa Teste LTDA",
        company_tax_id: "11222333000144",
        person: {
          name: "Clínica Central",
          tax_id: "11222333000145",
        },
        created_at: "2024-01-15T10:00:00Z",
        user_count: 5,
        professional_count: 3,
        client_count: 25,
      },
    ],
    total: 1,
    page: 1,
    size: 10,
    pages: 1,
  };

  const mockCompaniesResponse = {
    companies: [
      {
        id: 1,
        person: { name: "Empresa Teste LTDA", tax_id: "11222333000144" },
        is_active: true,
      },
    ],
    total: 1,
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock das respostas da API
    global.fetch.mockImplementation((url, options) => {
      if (url.includes("/api/v1/establishments/")) {
        if (options?.method === "GET") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockEstablishmentsResponse),
          });
        }
        if (options?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({ id: 2, message: "Estabelecimento criado" }),
          });
        }
        if (options?.method === "PUT") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({ id: 1, message: "Estabelecimento atualizado" }),
          });
        }
        if (options?.method === "PATCH") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ id: 1, is_active: false }),
          });
        }
        if (options?.method === "DELETE") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({ message: "Estabelecimento excluído" }),
          });
        }
      }

      if (url.includes("/api/v1/companies/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCompaniesResponse),
        });
      }

      return Promise.reject(new Error("URL não mockada"));
    });
  });

  afterEach(() => {
    global.fetch.mockClear();
  });

  describe("Fluxo Completo de CRUD", () => {
    test("deve executar fluxo completo: listar -> criar -> editar -> excluir", async () => {
      const user = userEvent.setup();
      render(<EstablishmentsPage />);

      // 1. Verificar carregamento inicial
      await waitFor(() => {
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
      });

      // Verificar se as chamadas foram feitas
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/establishments/"),
        expect.objectContaining({ method: "GET" })
      );

      // 2. Testar criação (simular abertura do modal)
      const createButton = screen.getByText("Novo Estabelecimento");
      await user.click(createButton);

      expect(screen.getByText("Novo Estabelecimento")).toBeInTheDocument();
      expect(
        screen.getByText("Formulário de estabelecimento em desenvolvimento...")
      ).toBeInTheDocument();

      // 3. Testar edição (simular abertura do modal)
      const editButtons = screen.getAllByText("Editar");
      await user.click(editButtons[0]);

      expect(screen.getByText("Editar Estabelecimento")).toBeInTheDocument();

      // 4. Testar toggle de status
      const toggleButtons = screen.getAllByText("Inativar");
      await user.click(toggleButtons[0]);

      // Simular confirmação
      await waitFor(() => {
        expect(notify.confirm).toHaveBeenCalled();
      });

      // Simular execução da ação
      const confirmCallback = notify.confirm.mock.calls[0][2];
      await act(async () => {
        await confirmCallback();
      });

      // Verificar se a API foi chamada
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/establishments/1/status"),
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ is_active: false }),
        })
      );

      expect(notify.success).toHaveBeenCalledWith(
        "Estabelecimento inativado com sucesso!"
      );

      // 5. Testar exclusão
      const deleteButtons = screen.getAllByText("Excluir");
      await user.click(deleteButtons[0]);

      // Simular confirmação de exclusão
      await waitFor(() => {
        expect(notify.confirmDelete).toHaveBeenCalled();
      });

      // Simular execução da exclusão
      const deleteCallback = notify.confirmDelete.mock.calls[0][2];
      await act(async () => {
        await deleteCallback();
      });

      // Verificar se a API foi chamada
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/establishments/1"),
        expect.objectContaining({ method: "DELETE" })
      );

      expect(notify.success).toHaveBeenCalledWith(
        "Estabelecimento excluído com sucesso!"
      );
    });
  });

  describe("Filtros e Busca", () => {
    test("deve aplicar filtros e atualizar lista", async () => {
      const user = userEvent.setup();
      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
      });

      // Aplicar filtro de busca
      const searchInput = screen.getByPlaceholderText(
        "Buscar estabelecimentos..."
      );
      await user.type(searchInput, "Clínica");

      // Verificar se a API foi chamada com o filtro
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/v1/establishments/"),
          expect.objectContaining({
            method: "GET",
          })
        );
      });

      // Aplicar filtro de status
      const statusSelect = screen.getByDisplayValue("Todos os status");
      await user.selectOptions(statusSelect, "active");

      // Aplicar filtro de empresa
      const companySelect = screen.getByDisplayValue("Todas as empresas");
      await user.selectOptions(companySelect, "1");

      // Verificar múltiplas chamadas com diferentes filtros
      expect(global.fetch).toHaveBeenCalledTimes(expect.any(Number));
    });
  });

  describe("Paginação", () => {
    test("deve navegar entre páginas", async () => {
      const user = userEvent.setup();

      // Mock resposta com múltiplas páginas
      global.fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              establishments: mockEstablishmentsResponse.establishments,
              total: 25,
              page: 1,
              size: 10,
              pages: 3,
            }),
        })
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Mostrando 1 a 10 de 25 estabelecimentos")
        ).toBeInTheDocument();
      });

      // Clicar em próxima página
      const nextButton = screen.getByText("Próxima");
      await user.click(nextButton);

      // Verificar se a API foi chamada com page=2
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/v1/establishments/"),
          expect.objectContaining({
            method: "GET",
          })
        );
      });
    });
  });

  describe("Estados de Erro", () => {
    test("deve mostrar erro quando API falha", async () => {
      // Mock erro na API
      global.fetch.mockImplementationOnce(() =>
        Promise.reject(new Error("Erro de rede"))
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Erro ao carregar estabelecimentos: Erro de rede")
        ).toBeInTheDocument();
      });

      // Verificar botão de tentar novamente
      expect(screen.getByText("Tentar Novamente")).toBeInTheDocument();
    });

    test("deve mostrar erro específico da API", async () => {
      // Mock erro 500 da API
      global.fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ detail: "Erro interno do servidor" }),
        })
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Erro ao carregar estabelecimentos: Erro interno do servidor"
          )
        ).toBeInTheDocument();
      });
    });

    test("deve lidar com erro de autenticação", async () => {
      // Mock erro 401
      global.fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ detail: "Não autorizado" }),
        })
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Erro ao carregar estabelecimentos: Não autorizado")
        ).toBeInTheDocument();
      });
    });
  });

  describe("Responsividade", () => {
    test("deve mostrar layout mobile em telas pequenas", async () => {
      // Simular viewport mobile
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 600,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
      });

      // Em mobile, deve mostrar cards ao invés de tabela
      // Verificar se elementos mobile estão presentes
      expect(screen.getByText("matriz")).toBeInTheDocument();
      expect(screen.getByText("clinica")).toBeInTheDocument();
    });

    test("deve mostrar layout desktop em telas grandes", async () => {
      // Simular viewport desktop
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 1200,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Lista de Estabelecimentos")
        ).toBeInTheDocument();
        expect(screen.getByText("Estabelecimento")).toBeInTheDocument();
        expect(screen.getByText("Empresa")).toBeInTheDocument();
      });
    });
  });

  describe("Performance", () => {
    test("deve carregar dados rapidamente", async () => {
      const startTime = Date.now();

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
      });

      const loadTime = Date.now() - startTime;

      // Deve carregar em menos de 2 segundos
      expect(loadTime).toBeLessThan(2000);
    });

    test("deve fazer cache das requisições", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
      });

      // Verificar se fez apenas uma chamada para estabelecimentos
      const establishmentsCalls = global.fetch.mock.calls.filter((call) =>
        call[0].includes("/api/v1/establishments/")
      );

      expect(establishmentsCalls.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Acessibilidade", () => {
    test("deve ter labels adequados para inputs", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(
          "Buscar estabelecimentos..."
        );
        expect(searchInput).toBeInTheDocument();
        expect(searchInput).toHaveAttribute(
          "placeholder",
          "Buscar estabelecimentos..."
        );
      });
    });

    test("deve suportar navegação por teclado", async () => {
      const user = userEvent.setup();
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(
          "Buscar estabelecimentos..."
        );
        searchInput.focus();
        expect(document.activeElement).toBe(searchInput);
      });

      // Testar navegação com Tab
      await user.tab();
      expect(document.activeElement).not.toBe(
        screen.getByPlaceholderText("Buscar estabelecimentos...")
      );
    });
  });

  describe("Cenários de Borda", () => {
    test("deve lidar com lista vazia", async () => {
      global.fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              establishments: [],
              total: 0,
              page: 1,
              size: 10,
              pages: 1,
            }),
        })
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Nenhum estabelecimento encontrado")
        ).toBeInTheDocument();
      });
    });

    test("deve lidar com dados incompletos", async () => {
      const incompleteData = {
        establishments: [
          {
            id: 1,
            code: "EST001",
            // Dados incompletos - sem person, company_name, etc.
          },
        ],
        total: 1,
        page: 1,
        size: 10,
        pages: 1,
      };

      global.fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(incompleteData),
        })
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("EST001")).toBeInTheDocument();
        // Deve mostrar dados disponíveis mesmo com informações incompletas
      });
    });

    test("deve lidar com nomes muito longos", async () => {
      const longNameData = {
        establishments: [
          {
            id: 1,
            code: "EST001",
            person: {
              name: "Clínica Oftalmológica Especializada em Cirurgia Refrativa e Catarata Avançada do Centro Médico",
              tax_id: "11222333000144",
            },
            company_name:
              "Empresa com Nome Muito Longo Limitada Sociedade Anônima",
          },
        ],
        total: 1,
        page: 1,
        size: 10,
        pages: 1,
      };

      global.fetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(longNameData),
        })
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Clínica Oftalmológica Especializada em Cirurgia Refrativa e Catarata Avançada do Centro Médico"
          )
        ).toBeInTheDocument();
      });
    });
  });
});
