/**
 * Testes para EstablishmentsPage.jsx
 * Testes abrangentes para validar o frontend do CRUD de estabelecimentos
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
import EstablishmentsPage from "../../pages/EstablishmentsPage";

// Mock dos serviços
jest.mock("../../services/api", () => ({
  establishmentsService: {
    getEstablishments: jest.fn(),
    countEstablishments: jest.fn(),
    toggleEstablishmentStatus: jest.fn(),
    deleteEstablishment: jest.fn(),
  },
  companiesService: {
    getCompanies: jest.fn(),
  },
}));

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

import { establishmentsService, companiesService } from "../../services/api";
import { notify } from "../../utils/notifications.jsx";

describe("EstablishmentsPage", () => {
  const mockEstablishments = [
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
    {
      id: 2,
      code: "EST002",
      type: "filial",
      category: "laboratorio",
      is_active: false,
      is_principal: false,
      company_id: 1,
      company_name: "Empresa Teste LTDA",
      person: {
        name: "Laboratório Filial",
        tax_id: "11222333000146",
      },
      created_at: "2024-01-20T10:00:00Z",
    },
  ];

  const mockCompanies = [
    {
      id: 1,
      person: { name: "Empresa Teste LTDA", tax_id: "11222333000144" },
      is_active: true,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mocks
    establishmentsService.getEstablishments.mockResolvedValue({
      establishments: mockEstablishments,
      total: 2,
      page: 1,
      size: 10,
      pages: 1,
    });

    establishmentsService.countEstablishments.mockResolvedValue({ total: 2 });
    companiesService.getCompanies.mockResolvedValue({
      companies: mockCompanies,
      total: 1,
    });
  });

  describe("Renderização Inicial", () => {
    test("deve renderizar o componente corretamente", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Estabelecimentos")).toBeInTheDocument();
        expect(
          screen.getByText(
            "Gerencie os estabelecimentos cadastrados no sistema"
          )
        ).toBeInTheDocument();
      });
    });

    test("deve mostrar loading inicial", () => {
      render(<EstablishmentsPage />);

      expect(
        screen.getByText("Carregando estabelecimentos...")
      ).toBeInTheDocument();
    });

    test("deve carregar estabelecimentos na montagem", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledWith({
          page: 1,
          size: 10,
        });
        expect(companiesService.getCompanies).toHaveBeenCalledWith({
          is_active: true,
          page: 1,
          size: 100,
        });
      });
    });
  });

  describe("Listagem de Estabelecimentos", () => {
    test("deve exibir lista de estabelecimentos", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
        expect(screen.getByText("Laboratório Filial")).toBeInTheDocument();
        expect(screen.getByText("EST001")).toBeInTheDocument();
        expect(screen.getByText("EST002")).toBeInTheDocument();
      });
    });

    test("deve exibir estatísticas corretas", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument(); // Total
        expect(screen.getByText("1")).toBeInTheDocument(); // Ativos
        expect(screen.getByText("1")).toBeInTheDocument(); // Inativos
        expect(screen.getByText("1")).toBeInTheDocument(); // Principais
      });
    });

    test("deve exibir informações do estabelecimento na tabela", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Empresa Teste LTDA")).toBeInTheDocument();
        expect(screen.getByText("matriz")).toBeInTheDocument();
        expect(screen.getByText("filial")).toBeInTheDocument();
        expect(screen.getByText("clinica")).toBeInTheDocument();
        expect(screen.getByText("laboratorio")).toBeInTheDocument();
      });
    });
  });

  describe("Filtros e Busca", () => {
    test("deve aplicar filtro de busca", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(
          "Buscar estabelecimentos..."
        );
        fireEvent.change(searchInput, { target: { value: "Clínica" } });
      });

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledWith(
          expect.objectContaining({ search: "Clínica" })
        );
      });
    });

    test("deve aplicar filtro de status", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const statusSelect = screen.getByDisplayValue("Todos os status");
        fireEvent.change(statusSelect, { target: { value: "active" } });
      });

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledWith(
          expect.objectContaining({ is_active: true })
        );
      });
    });

    test("deve aplicar filtro de empresa", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const companySelect = screen.getByDisplayValue("Todas as empresas");
        fireEvent.change(companySelect, { target: { value: "1" } });
      });

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledWith(
          expect.objectContaining({ company_id: 1 })
        );
      });
    });

    test("deve aplicar filtro de tipo", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const typeSelect = screen.getByDisplayValue("Todos os tipos");
        fireEvent.change(typeSelect, { target: { value: "matriz" } });
      });

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledWith(
          expect.objectContaining({ type: "matriz" })
        );
      });
    });

    test("deve aplicar filtro de categoria", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const categorySelect = screen.getByDisplayValue("Todas as categorias");
        fireEvent.change(categorySelect, { target: { value: "clinica" } });
      });

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledWith(
          expect.objectContaining({ category: "clinica" })
        );
      });
    });
  });

  describe("Ações CRUD", () => {
    test("deve abrir modal de criação ao clicar em 'Novo Estabelecimento'", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const newButton = screen.getByText("Novo Estabelecimento");
        fireEvent.click(newButton);
      });

      expect(screen.getByText("Novo Estabelecimento")).toBeInTheDocument();
      expect(
        screen.getByText("Formulário de estabelecimento em desenvolvimento...")
      ).toBeInTheDocument();
    });

    test("deve abrir modal de edição ao clicar em 'Editar'", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const editButtons = screen.getAllByText("Editar");
        fireEvent.click(editButtons[0]);
      });

      expect(screen.getByText("Editar Estabelecimento")).toBeInTheDocument();
      expect(
        screen.getByText("Formulário de estabelecimento em desenvolvimento...")
      ).toBeInTheDocument();
    });

    test("deve abrir modal de detalhes ao clicar em 'Ver Detalhes'", async () => {
      render(<EstablishmentsPage />);

      await waitFor(() => {
        const viewButtons = screen.getAllByText("Ver Detalhes");
        fireEvent.click(viewButtons[0]);
      });

      expect(
        screen.getByText("Detalhes do Estabelecimento")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Detalhes do estabelecimento em desenvolvimento...")
      ).toBeInTheDocument();
    });

    test("deve alternar status do estabelecimento", async () => {
      establishmentsService.toggleEstablishmentStatus.mockResolvedValue({
        id: 1,
        is_active: false,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        const toggleButtons = screen.getAllByText("Inativar");
        fireEvent.click(toggleButtons[0]);
      });

      // Simular confirmação
      await waitFor(() => {
        expect(notify.confirm).toHaveBeenCalledWith(
          "Inativar Estabelecimento",
          expect.stringContaining("Tem certeza que deseja inativar"),
          expect.any(Function)
        );
      });

      // Simular execução da ação
      const confirmCallback = notify.confirm.mock.calls[0][2];
      await act(async () => {
        await confirmCallback();
      });

      expect(
        establishmentsService.toggleEstablishmentStatus
      ).toHaveBeenCalledWith(1, false);
      expect(notify.success).toHaveBeenCalledWith(
        "Estabelecimento inativado com sucesso!"
      );
    });

    test("deve excluir estabelecimento", async () => {
      establishmentsService.deleteEstablishment.mockResolvedValue({});

      render(<EstablishmentsPage />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByText("Excluir");
        fireEvent.click(deleteButtons[0]);
      });

      // Simular confirmação de exclusão
      await waitFor(() => {
        expect(notify.confirmDelete).toHaveBeenCalledWith(
          "Excluir Estabelecimento",
          expect.stringContaining("Tem certeza que deseja excluir"),
          expect.any(Function)
        );
      });

      // Simular execução da exclusão
      const confirmCallback = notify.confirmDelete.mock.calls[0][2];
      await act(async () => {
        await confirmCallback();
      });

      expect(establishmentsService.deleteEstablishment).toHaveBeenCalledWith(1);
      expect(notify.success).toHaveBeenCalledWith(
        "Estabelecimento excluído com sucesso!"
      );
    });
  });

  describe("Paginação", () => {
    test("deve mostrar controles de paginação quando há múltiplas páginas", async () => {
      establishmentsService.getEstablishments.mockResolvedValue({
        establishments: mockEstablishments,
        total: 25,
        page: 1,
        size: 10,
        pages: 3,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(screen.getByText("Anterior")).toBeInTheDocument();
        expect(screen.getByText("Próxima")).toBeInTheDocument();
        expect(
          screen.getByText("Mostrando 1 a 10 de 25 estabelecimentos")
        ).toBeInTheDocument();
      });
    });

    test("deve navegar para próxima página", async () => {
      establishmentsService.getEstablishments.mockResolvedValue({
        establishments: mockEstablishments,
        total: 25,
        page: 1,
        size: 10,
        pages: 3,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        const nextButton = screen.getByText("Próxima");
        fireEvent.click(nextButton);
      });

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledWith(
          expect.objectContaining({ page: 2 })
        );
      });
    });
  });

  describe("Estados de Erro", () => {
    test("deve mostrar erro quando falha ao carregar estabelecimentos", async () => {
      const errorMessage = "Erro ao carregar estabelecimentos";
      establishmentsService.getEstablishments.mockRejectedValue(
        new Error(errorMessage)
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText(`Erro ao carregar estabelecimentos: ${errorMessage}`)
        ).toBeInTheDocument();
        expect(screen.getByText("Tentar Novamente")).toBeInTheDocument();
      });
    });

    test("deve tentar recarregar ao clicar em 'Tentar Novamente'", async () => {
      establishmentsService.getEstablishments
        .mockRejectedValueOnce(new Error("Erro inicial"))
        .mockResolvedValueOnce({
          establishments: mockEstablishments,
          total: 2,
          page: 1,
          size: 10,
          pages: 1,
        });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        const retryButton = screen.getByText("Tentar Novamente");
        fireEvent.click(retryButton);
      });

      await waitFor(() => {
        expect(establishmentsService.getEstablishments).toHaveBeenCalledTimes(
          2
        );
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
      });
    });

    test("deve mostrar erro ao falhar toggle de status", async () => {
      const errorMessage = "Erro ao alterar status";
      establishmentsService.toggleEstablishmentStatus.mockRejectedValue(
        new Error(errorMessage)
      );

      render(<EstablishmentsPage />);

      await waitFor(() => {
        const toggleButtons = screen.getAllByText("Inativar");
        fireEvent.click(toggleButtons[0]);
      });

      // Simular execução da ação que falha
      const confirmCallback = notify.confirm.mock.calls[0][2];
      await act(async () => {
        await confirmCallback();
      });

      expect(notify.error).toHaveBeenCalledWith(
        "Erro ao inativar estabelecimento"
      );
    });

    test("deve mostrar erro ao falhar exclusão", async () => {
      const errorMessage = "Erro interno do servidor";
      establishmentsService.deleteEstablishment.mockRejectedValue({
        response: { data: { detail: errorMessage } },
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByText("Excluir");
        fireEvent.click(deleteButtons[0]);
      });

      // Simular execução da exclusão que falha
      const confirmCallback = notify.confirmDelete.mock.calls[0][2];
      await act(async () => {
        await confirmCallback();
      });

      expect(notify.error).toHaveBeenCalledWith(
        `Erro ao excluir estabelecimento: ${errorMessage}`
      );
    });
  });

  describe("Responsividade", () => {
    test("deve mostrar cards em dispositivos móveis", async () => {
      // Mock viewport pequeno
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 600,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        // Em mobile, deve mostrar cards ao invés de tabela
        expect(screen.getByText("Clínica Central")).toBeInTheDocument();
        expect(screen.getByText("Laboratório Filial")).toBeInTheDocument();
      });
    });

    test("deve mostrar tabela em desktop", async () => {
      // Mock viewport grande
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 1200,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        // Em desktop, deve mostrar tabela
        expect(
          screen.getByText("Lista de Estabelecimentos")
        ).toBeInTheDocument();
        expect(screen.getByText("Estabelecimento")).toBeInTheDocument();
        expect(screen.getByText("Empresa")).toBeInTheDocument();
        expect(screen.getByText("Tipo/Categoria")).toBeInTheDocument();
      });
    });
  });

  describe("Estados Vazios", () => {
    test("deve mostrar mensagem quando não há estabelecimentos", async () => {
      establishmentsService.getEstablishments.mockResolvedValue({
        establishments: [],
        total: 0,
        page: 1,
        size: 10,
        pages: 1,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Nenhum estabelecimento encontrado")
        ).toBeInTheDocument();
      });
    });

    test("deve mostrar mensagem quando filtro não retorna resultados", async () => {
      establishmentsService.getEstablishments.mockResolvedValue({
        establishments: [],
        total: 0,
        page: 1,
        size: 10,
        pages: 1,
      });

      render(<EstablishmentsPage />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(
          "Buscar estabelecimentos..."
        );
        fireEvent.change(searchInput, { target: { value: "inexistente" } });
      });

      await waitFor(() => {
        expect(
          screen.getByText("Nenhum estabelecimento encontrado")
        ).toBeInTheDocument();
      });
    });
  });
});
