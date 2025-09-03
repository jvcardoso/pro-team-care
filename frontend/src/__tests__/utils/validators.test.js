/**
 * Testes para utils/validators.js
 * Implementação crítica conforme auditoria frontend - Prioridade 1
 */

import {
  removeNonNumeric,
  validateCPF,
  validateCNPJ,
  validateCEP,
  validateEmail,
  validatePhone,
  validateDDD,
  isRequired,
  minLength,
  maxLength,
  VALID_DDDS,
} from "../../utils/validators";

describe("removeNonNumeric", () => {
  test("should remove all non-numeric characters", () => {
    expect(removeNonNumeric("123.456.789-01")).toBe("12345678901");
    expect(removeNonNumeric("11.222.333/0001-81")).toBe("11222333000181");
    expect(removeNonNumeric("(11) 98765-4321")).toBe("11987654321");
  });

  test("should handle empty and null values", () => {
    expect(removeNonNumeric("")).toBe("");
    expect(removeNonNumeric(null)).toBe("");
    expect(removeNonNumeric(undefined)).toBe("");
  });

  test("should handle strings with only letters", () => {
    expect(removeNonNumeric("abcdef")).toBe("");
    expect(removeNonNumeric("ABC-XYZ")).toBe("");
  });
});

describe("validateCPF", () => {
  test("should validate correct CPF", () => {
    // CPFs válidos
    expect(validateCPF("11144477735")).toBe(true);
    expect(validateCPF("111.444.777-35")).toBe(true);
    expect(validateCPF("529.982.247-25")).toBe(true);
  });

  test("should reject invalid CPF", () => {
    // CPFs inválidos
    expect(validateCPF("11111111111")).toBe(false); // Todos iguais
    expect(validateCPF("12345678901")).toBe(false); // Dígito verificador errado
    expect(validateCPF("111.444.777-36")).toBe(false); // Dígito errado
  });

  test("should reject CPF with wrong length", () => {
    expect(validateCPF("1114447773")).toBe(false); // 10 dígitos
    expect(validateCPF("111444777355")).toBe(false); // 12 dígitos
    expect(validateCPF("")).toBe(false);
  });

  test("should handle formatted CPF", () => {
    expect(validateCPF("111.444.777-35")).toBe(true);
    expect(validateCPF("111-444-777-35")).toBe(true);
  });
});

describe("validateCNPJ", () => {
  test("should validate correct CNPJ", () => {
    // CNPJs válidos (usando CNPJs reais válidos)
    expect(validateCNPJ("11222333000181")).toBe(true);
    expect(validateCNPJ("11.222.333/0001-81")).toBe(true);
    // Usando CNPJ válido real
    expect(validateCNPJ("11444777000161")).toBe(true);
  });

  test("should reject invalid CNPJ", () => {
    // CNPJs inválidos
    expect(validateCNPJ("11111111111111")).toBe(false); // Todos iguais
    expect(validateCNPJ("12345678901234")).toBe(false); // Dígito verificador errado
    expect(validateCNPJ("11.222.333/0001-82")).toBe(false); // Dígito errado
  });

  test("should reject CNPJ with wrong length", () => {
    expect(validateCNPJ("1122233300018")).toBe(false); // 13 dígitos
    expect(validateCNPJ("112223330001811")).toBe(false); // 15 dígitos
    expect(validateCNPJ("")).toBe(false);
  });

  test("should handle formatted CNPJ", () => {
    expect(validateCNPJ("11.222.333/0001-81")).toBe(true);
    expect(validateCNPJ("11222333/0001-81")).toBe(true);
  });
});

describe("validateCEP", () => {
  test("should validate correct CEP", () => {
    expect(validateCEP("01310100")).toBe(true);
    expect(validateCEP("01310-100")).toBe(true);
    expect(validateCEP("12345678")).toBe(true);
  });

  test("should reject invalid CEP", () => {
    expect(validateCEP("0131010")).toBe(false); // 7 dígitos
    expect(validateCEP("013101000")).toBe(false); // 9 dígitos
    expect(validateCEP("abcdefgh")).toBe(false); // Letras
    expect(validateCEP("")).toBe(false);
  });

  test("should handle formatted CEP", () => {
    expect(validateCEP("01310-100")).toBe(true);
    expect(validateCEP("01.310-100")).toBe(true);
  });
});

describe("validateEmail", () => {
  test("should validate correct email", () => {
    expect(validateEmail("user@example.com")).toBe(true);
    expect(validateEmail("user.name@example.com")).toBe(true);
    expect(validateEmail("user+tag@example.com")).toBe(true);
    expect(validateEmail("user123@example123.com")).toBe(true);
    expect(validateEmail("test@subdomain.example.com")).toBe(true);
  });

  test("should reject invalid email", () => {
    expect(validateEmail("user@")).toBe(false);
    expect(validateEmail("@example.com")).toBe(false);
    expect(validateEmail("user.example.com")).toBe(false); // Sem @
    expect(validateEmail("user@@example.com")).toBe(false); // Duplo @
    expect(validateEmail("")).toBe(false);
  });

  test("should reject email with spaces", () => {
    expect(validateEmail("user name@example.com")).toBe(false);
    expect(validateEmail("user@exam ple.com")).toBe(false);
  });
});

describe("validatePhone", () => {
  test("should validate correct mobile phone", () => {
    expect(validatePhone("11987654321")).toBe(true); // Celular SP
    expect(validatePhone("21987654321")).toBe(true); // Celular RJ
    expect(validatePhone("(11) 98765-4321")).toBe(true); // Formatado
  });

  test("should validate correct landline phone", () => {
    expect(validatePhone("1133334444")).toBe(true); // Fixo SP
    expect(validatePhone("2133334444")).toBe(true); // Fixo RJ
    expect(validatePhone("(11) 3333-4444")).toBe(true); // Formatado
  });

  test("should reject invalid phone", () => {
    expect(validatePhone("119876543")).toBe(false); // 9 dígitos
    expect(validatePhone("119876543212")).toBe(false); // 12 dígitos
    expect(validatePhone("00987654321")).toBe(false); // DDD inválido
    expect(validatePhone("01987654321")).toBe(false); // DDD inválido
    expect(validatePhone("")).toBe(false);
  });

  test("should reject mobile without 9", () => {
    expect(validatePhone("11887654321")).toBe(false); // Não começa com 9
    expect(validatePhone("11787654321")).toBe(false); // Não começa com 9
  });

  test("should handle formatted phone", () => {
    expect(validatePhone("(11) 98765-4321")).toBe(true);
    expect(validatePhone("11 98765-4321")).toBe(true);
    expect(validatePhone("11-98765-4321")).toBe(true);
  });
});

describe("validateDDD", () => {
  test("should validate correct DDD", () => {
    expect(validateDDD("11")).toBe(true); // SP
    expect(validateDDD("21")).toBe(true); // RJ
    expect(validateDDD("85")).toBe(true); // CE
    expect(validateDDD("11")).toBe(true); // String number
  });

  test("should reject invalid DDD", () => {
    expect(validateDDD("00")).toBe(false);
    expect(validateDDD("01")).toBe(false);
    expect(validateDDD("10")).toBe(false);
    expect(validateDDD("100")).toBe(false); // 3 dígitos
    expect(validateDDD("")).toBe(false);
  });

  test("should have all valid DDDs", () => {
    // Verificar se todos os DDDs da lista são válidos
    VALID_DDDS.forEach((ddd) => {
      expect(validateDDD(ddd.toString())).toBe(true);
    });
  });
});

describe("Form validation helpers", () => {
  describe("isRequired", () => {
    test("should validate required fields", () => {
      expect(isRequired("value")).toBe(true);
      expect(isRequired(123)).toBe(true);
      expect(isRequired(0)).toBeFalsy(); // 0 é falsy no JavaScript
      expect(isRequired(false)).toBeFalsy();
    });

    test("should reject empty values", () => {
      expect(isRequired("")).toBeFalsy();
      expect(isRequired("   ")).toBe(false); // Apenas espaços (trim resulta em false)
      expect(isRequired(null)).toBeFalsy();
      expect(isRequired(undefined)).toBeFalsy();
    });
  });

  describe("minLength", () => {
    test("should validate minimum length", () => {
      expect(minLength("hello", 3)).toBe(true);
      expect(minLength("hello", 5)).toBe(true);
      expect(minLength("he", 3)).toBe(false);
      expect(minLength(12345, 4)).toBe(true); // Number
    });

    test("should handle empty values", () => {
      expect(minLength("", 3)).toBeFalsy(); // Empty string is falsy
      expect(minLength(null, 3)).toBeFalsy();
      expect(minLength(undefined, 3)).toBeFalsy();
    });
  });

  describe("maxLength", () => {
    test("should validate maximum length", () => {
      expect(maxLength("hello", 10)).toBe(true);
      expect(maxLength("hello", 5)).toBe(true);
      expect(maxLength("hello world", 5)).toBe(false);
      expect(maxLength(12345, 6)).toBe(true); // Number
    });

    test("should handle empty values", () => {
      expect(maxLength("", 5)).toBe(true); // Empty is valid
      expect(maxLength(null, 5)).toBe(true);
      expect(maxLength(undefined, 5)).toBe(true);
    });
  });
});

describe("Edge cases and error handling", () => {
  test("should handle null and undefined gracefully", () => {
    expect(validateCPF(null)).toBe(false);
    expect(validateCNPJ(undefined)).toBe(false);
    expect(validateCEP(null)).toBe(false);
    expect(validateEmail(null)).toBe(false);
    expect(validatePhone(undefined)).toBe(false);
  });

  test("should handle numeric inputs", () => {
    expect(validateCPF(11144477735)).toBe(true);
    expect(validateCNPJ(11222333000181)).toBe(true);
    expect(validateCEP(1310100)).toBe(false); // CEP precisa 8 dígitos
    expect(validatePhone(11987654321)).toBe(true);
  });

  test("should handle very long strings", () => {
    const longString = "1".repeat(100);
    expect(validateCPF(longString)).toBe(false);
    expect(validateCNPJ(longString)).toBe(false);
    expect(validateCEP(longString)).toBe(false);
    expect(validatePhone(longString)).toBe(false);
  });
});
