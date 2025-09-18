/**
 * Testes para establishmentsService
 * Testes abrangentes para validar a integração frontend-backend do CRUD de estabelecimentos
 */

import { jest } from "@jest/globals";

// Mock do módulo api
jest.mock("../../services/api", () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
  httpCache: {
    invalidatePattern: jest.fn(),
  },
}));

import { establishmentsService } from "../../services/establishmentsService";
import { api, httpCache } from "../../services/api";

describe("establishmentsService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("getEstablishments", () => {
    test("deve chamar API corretamente com parâmetros", async () => {
      const mockResponse = {
        data: {
          establishments: [{ id: 1, code: "EST001", type: "matriz" }],
          total: 1,
          page: 1,
          size: 10,
          pages: 1,
        },
      };

      api.get.mockResolvedValue(mockResponse);

      const params = { page: 1, size: 10, search: "teste" };
      const result = await establishmentsService.getEstablishments(params);

      expect(api.get).toHaveBeenCalledWith("/api/v1/establishments/", {
        params,
      });
      expect(result).toEqual(mockResponse.data);
    });

    test("deve lidar com resposta vazia", async () => {
      const mockResponse = { data: null };
      api.get.mockResolvedValue(mockResponse);

      const result = await establishmentsService.getEstablishments();

      expect(result).toEqual([]);
    });

    test("deve lidar com erro da API", async () => {
      const error = new Error("API Error");
      api.get.mockRejectedValue(error);

      await expect(establishmentsService.getEstablishments()).rejects.toThrow(
        "API Error"
      );
    });
  });

  describe("getEstablishment", () => {
    test("deve obter estabelecimento por ID", async () => {
      const mockEstablishment = {
        id: 1,
        code: "EST001",
        type: "matriz",
        person: { name: "Clínica Teste" },
      };
      const mockResponse = { data: mockEstablishment };

      api.get.mockResolvedValue(mockResponse);

      const result = await establishmentsService.getEstablishment(1);

      expect(api.get).toHaveBeenCalledWith("/api/v1/establishments/1");
      expect(result).toEqual(mockEstablishment);
    });
  });

  describe("getEstablishmentsByCompany", () => {
    test("deve obter estabelecimentos por empresa", async () => {
      const mockEstablishments = [
        { id: 1, code: "EST001" },
        { id: 2, code: "EST002" },
      ];
      const mockResponse = { data: mockEstablishments };

      api.get.mockResolvedValue(mockResponse);

      const result = await establishmentsService.getEstablishmentsByCompany(1, {
        is_active: true,
      });

      expect(api.get).toHaveBeenCalledWith("/api/v1/establishments/company/1", {
        params: { is_active: true },
      });
      expect(result).toEqual(mockEstablishments);
    });
  });

  describe("createEstablishment", () => {
    test("deve criar estabelecimento com sucesso", async () => {
      const establishmentData = {
        company_id: 1,
        code: "EST001",
        type: "matriz",
        category: "clinica",
        person: {
          name: "Clínica Teste",
          tax_id: "11222333000144",
        },
      };

      const mockResponse = { data: { id: 1, ...establishmentData } };
      api.post.mockResolvedValue(mockResponse);

      const result = await establishmentsService.createEstablishment(
        establishmentData
      );

      expect(api.post).toHaveBeenCalledWith(
        "/api/v1/establishments/",
        establishmentData
      );
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );
      expect(result).toEqual({ id: 1, ...establishmentData });
    });

    test("deve invalidar cache após criação", async () => {
      const establishmentData = { company_id: 1, code: "EST001" };
      const mockResponse = { data: { id: 1 } };

      api.post.mockResolvedValue(mockResponse);

      await establishmentsService.createEstablishment(establishmentData);

      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );
    });
  });

  describe("updateEstablishment", () => {
    test("deve atualizar estabelecimento", async () => {
      const updateData = {
        code: "EST002",
        type: "filial",
        person: { name: "Clínica Atualizada" },
      };

      const mockResponse = { data: { id: 1, ...updateData } };
      api.put.mockResolvedValue(mockResponse);

      const result = await establishmentsService.updateEstablishment(
        1,
        updateData
      );

      expect(api.put).toHaveBeenCalledWith(
        "/api/v1/establishments/1",
        updateData
      );
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );
      expect(result).toEqual({ id: 1, ...updateData });
    });
  });

  describe("toggleEstablishmentStatus", () => {
    test("deve alternar status para ativo", async () => {
      const mockResponse = { data: { id: 1, is_active: true } };
      api.patch.mockResolvedValue(mockResponse);

      const result = await establishmentsService.toggleEstablishmentStatus(
        1,
        true
      );

      expect(api.patch).toHaveBeenCalledWith(
        "/api/v1/establishments/1/status",
        {
          is_active: true,
        }
      );
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );
      expect(result).toEqual({ id: 1, is_active: true });
    });

    test("deve alternar status para inativo", async () => {
      const mockResponse = { data: { id: 1, is_active: false } };
      api.patch.mockResolvedValue(mockResponse);

      const result = await establishmentsService.toggleEstablishmentStatus(
        1,
        false
      );

      expect(api.patch).toHaveBeenCalledWith(
        "/api/v1/establishments/1/status",
        {
          is_active: false,
        }
      );
      expect(result).toEqual({ id: 1, is_active: false });
    });
  });

  describe("deleteEstablishment", () => {
    test("deve excluir estabelecimento", async () => {
      const mockResponse = { data: {} };
      api.delete.mockResolvedValue(mockResponse);

      const result = await establishmentsService.deleteEstablishment(1);

      expect(api.delete).toHaveBeenCalledWith("/api/v1/establishments/1");
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );
      expect(result).toEqual({});
    });
  });

  describe("reorderEstablishments", () => {
    test("deve reordenar estabelecimentos", async () => {
      const companyId = 1;
      const establishmentOrders = [
        { id: 1, order: 1 },
        { id: 2, order: 2 },
      ];

      const mockResponse = { data: { message: "Reordenado com sucesso" } };
      api.post.mockResolvedValue(mockResponse);

      const result = await establishmentsService.reorderEstablishments(
        companyId,
        establishmentOrders
      );

      expect(api.post).toHaveBeenCalledWith("/api/v1/establishments/reorder", {
        company_id: companyId,
        establishment_orders: establishmentOrders,
      });
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );
      expect(result).toEqual({ message: "Reordenado com sucesso" });
    });
  });

  describe("validateEstablishmentCreation", () => {
    test("deve validar criação de estabelecimento", async () => {
      const mockResponse = { data: { is_valid: true, error_message: "" } };
      api.post.mockResolvedValue(mockResponse);

      const result = await establishmentsService.validateEstablishmentCreation(
        1,
        "EST001",
        false
      );

      expect(api.post).toHaveBeenCalledWith(
        "/api/v1/establishments/validate",
        null,
        {
          params: {
            company_id: 1,
            code: "EST001",
            is_principal: false,
          },
        }
      );
      expect(result).toEqual({ is_valid: true, error_message: "" });
    });

    test("deve validar estabelecimento principal", async () => {
      const mockResponse = { data: { is_valid: true, error_message: "" } };
      api.post.mockResolvedValue(mockResponse);

      const result = await establishmentsService.validateEstablishmentCreation(
        1,
        "EST001",
        true
      );

      expect(api.post).toHaveBeenCalledWith(
        "/api/v1/establishments/validate",
        null,
        {
          params: {
            company_id: 1,
            code: "EST001",
            is_principal: true,
          },
        }
      );
      expect(result).toEqual({ is_valid: true, error_message: "" });
    });
  });

  describe("countEstablishments", () => {
    test("deve contar estabelecimentos", async () => {
      const mockResponse = {
        data: {
          establishments: [],
          total: 25,
        },
      };
      api.get.mockResolvedValue(mockResponse);

      const result = await establishmentsService.countEstablishments({
        company_id: 1,
      });

      expect(api.get).toHaveBeenCalledWith("/api/v1/establishments/", {
        params: { company_id: 1, page: 1, size: 1 },
      });
      expect(result).toEqual({ total: 25 });
    });

    test("deve retornar zero quando não há estabelecimentos", async () => {
      const mockResponse = { data: null };
      api.get.mockResolvedValue(mockResponse);

      const result = await establishmentsService.countEstablishments();

      expect(result).toEqual({ total: 0 });
    });
  });

  describe("Tratamento de Erros", () => {
    test("deve propagar erro da API em getEstablishments", async () => {
      const error = new Error("Network Error");
      api.get.mockRejectedValue(error);

      await expect(establishmentsService.getEstablishments()).rejects.toThrow(
        "Network Error"
      );
    });

    test("deve propagar erro da API em createEstablishment", async () => {
      const error = new Error("Validation Error");
      api.post.mockRejectedValue(error);

      const establishmentData = { company_id: 1, code: "EST001" };

      await expect(
        establishmentsService.createEstablishment(establishmentData)
      ).rejects.toThrow("Validation Error");
    });

    test("deve propagar erro da API em updateEstablishment", async () => {
      const error = new Error("Not Found");
      api.put.mockRejectedValue(error);

      await expect(
        establishmentsService.updateEstablishment(1, {})
      ).rejects.toThrow("Not Found");
    });

    test("deve propagar erro da API em deleteEstablishment", async () => {
      const error = new Error("Forbidden");
      api.delete.mockRejectedValue(error);

      await expect(
        establishmentsService.deleteEstablishment(1)
      ).rejects.toThrow("Forbidden");
    });
  });

  describe("Cache Management", () => {
    test("deve invalidar cache após operações de escrita", async () => {
      const mockResponse = { data: {} };

      // Test create
      api.post.mockResolvedValue(mockResponse);
      await establishmentsService.createEstablishment({
        company_id: 1,
        code: "EST001",
      });
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );

      // Reset mock
      httpCache.invalidatePattern.mockClear();

      // Test update
      api.put.mockResolvedValue(mockResponse);
      await establishmentsService.updateEstablishment(1, { code: "EST002" });
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );

      // Reset mock
      httpCache.invalidatePattern.mockClear();

      // Test toggle status
      api.patch.mockResolvedValue(mockResponse);
      await establishmentsService.toggleEstablishmentStatus(1, false);
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );

      // Reset mock
      httpCache.invalidatePattern.mockClear();

      // Test delete
      api.delete.mockResolvedValue(mockResponse);
      await establishmentsService.deleteEstablishment(1);
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );

      // Reset mock
      httpCache.invalidatePattern.mockClear();

      // Test reorder
      api.post.mockResolvedValue(mockResponse);
      await establishmentsService.reorderEstablishments(1, [
        { id: 1, order: 1 },
      ]);
      expect(httpCache.invalidatePattern).toHaveBeenCalledWith(
        "/api/v1/establishments"
      );
    });

    test("não deve invalidar cache em operações de leitura", async () => {
      const mockResponse = { data: [] };

      api.get.mockResolvedValue(mockResponse);

      await establishmentsService.getEstablishments();
      await establishmentsService.getEstablishment(1);
      await establishmentsService.getEstablishmentsByCompany(1);
      await establishmentsService.countEstablishments();

      expect(httpCache.invalidatePattern).not.toHaveBeenCalled();
    });
  });
});
