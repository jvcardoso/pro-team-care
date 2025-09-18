/**
 * Testes para hooks/useCompanyForm.ts
 * Hook complexo de 620 linhas - Crítico conforme auditoria frontend
 * Convertido para JS para resolver problemas de TypeScript
 */

import { renderHook, act } from "@testing-library/react";

// Mocks configurados antes dos imports
jest.mock("../../services/api", () => ({
  companiesService: {
    getById: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
  },
}));

jest.mock("../../services/cnpjService", () => ({
  consultarCNPJ: jest.fn(),
}));

jest.mock("../../services/addressEnrichmentService", () => ({
  default: {
    enrichAddress: jest.fn(),
  },
}));

jest.mock("../../utils/notifications", () => ({
  notify: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
  },
}));

// Imports após mocks
import { useCompanyForm } from "../../hooks/useCompanyForm";
import { companiesService } from "../../services/api";
import { consultarCNPJ } from "../../services/cnpjService";
import { notify } from "../../utils/notifications";

describe("useCompanyForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Hook Initialization", () => {
    test("should initialize hook successfully", () => {
      const { result } = renderHook(() => useCompanyForm({}));

      // Verifica que o hook foi inicializado corretamente
      expect(result.current).toBeDefined();
      expect(result.current.formData).toBeDefined();
      expect(result.current.loading).toBeDefined();
      expect(result.current.error).toBeDefined();
    });

    test("should have form data structure", () => {
      const { result } = renderHook(() => useCompanyForm({}));

      // Verifica estrutura básica do formData
      expect(result.current.formData).toHaveProperty("people");
      expect(result.current.formData.people).toHaveProperty("person_type");
      expect(result.current.formData.people.person_type).toBe("PJ");

      // Verifica arrays básicos
      expect(Array.isArray(result.current.formData.phones)).toBe(true);
      expect(Array.isArray(result.current.formData.emails)).toBe(true);
      expect(Array.isArray(result.current.formData.addresses)).toBe(true);
    });
  });

  describe("Hook State", () => {
    test("should have initial state values", () => {
      const { result } = renderHook(() => useCompanyForm({}));

      expect(typeof result.current.loading).toBe("boolean");
      expect(
        result.current.error === null ||
          typeof result.current.error === "string"
      ).toBe(true);
    });
  });

  describe("Data Structure Validation", () => {
    test("should have phones array with valid structure", () => {
      const { result } = renderHook(() => useCompanyForm({}));

      const phones = result.current.formData.phones;
      expect(Array.isArray(phones)).toBe(true);

      // Se há telefones, verifica estrutura
      if (phones.length > 0) {
        expect(phones[0]).toHaveProperty("country_code");
        expect(phones[0]).toHaveProperty("number");
        expect(phones[0]).toHaveProperty("type");
      }
    });

    test("should have emails array with valid structure", () => {
      const { result } = renderHook(() => useCompanyForm({}));

      const emails = result.current.formData.emails;
      expect(Array.isArray(emails)).toBe(true);

      // Se há emails, verifica estrutura
      if (emails.length > 0) {
        expect(emails[0]).toHaveProperty("email_address");
        expect(emails[0]).toHaveProperty("type");
      }
    });

    test("should have addresses array with valid structure", () => {
      const { result } = renderHook(() => useCompanyForm({}));

      const addresses = result.current.formData.addresses;
      expect(Array.isArray(addresses)).toBe(true);

      // Se há endereços, verifica estrutura
      if (addresses.length > 0) {
        expect(addresses[0]).toHaveProperty("street");
        expect(addresses[0]).toHaveProperty("city");
        expect(addresses[0]).toHaveProperty("country");
        expect(addresses[0]).toHaveProperty("type");
      }
    });
  });

  describe("Hook Functionality", () => {
    test("should provide basic hook interface", () => {
      const { result } = renderHook(() => useCompanyForm({}));

      // Verifica que as propriedades esperadas estão presentes
      const hookResult = result.current;
      expect(hookResult).toHaveProperty("formData");
      expect(hookResult).toHaveProperty("loading");
      expect(hookResult).toHaveProperty("error");

      // Verifica que o hook foi inicializado com sucesso
      expect(hookResult.formData).toBeTruthy();
      expect(typeof hookResult.loading).toBe("boolean");
    });
  });
});
