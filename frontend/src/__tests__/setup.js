// Test setup file for Jest
import "@testing-library/jest-dom";

// Mock import.meta.env for Vite compatibility
Object.defineProperty(global, "import", {
  value: {
    meta: {
      env: {
        VITE_API_URL: "http://localhost:8000",
      },
    },
  },
  writable: true,
});

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Basic test to satisfy Jest requirement
describe("Test environment setup", () => {
  test("should be properly configured", () => {
    expect(global.localStorage).toBeDefined();
    expect(global.sessionStorage).toBeDefined();
    expect(window.matchMedia).toBeDefined();
  });
});
