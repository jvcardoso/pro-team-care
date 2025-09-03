// Mock para services/api.js para testes
export const authService = {
  login: jest.fn(),
  register: jest.fn(),
  getCurrentUser: jest.fn(),
  logout: jest.fn(),
};

export const companiesService = {
  getCompanies: jest.fn(),
  getCompaniesCount: jest.fn(),
  getById: jest.fn(),
  getCompanyByCNPJ: jest.fn(),
  create: jest.fn(),
  updateCompany: jest.fn(),
  deleteCompany: jest.fn(),
  getCompanyContacts: jest.fn(),
};

export const healthService = {
  getHealthStatus: jest.fn(),
  getDetailedHealth: jest.fn(),
};

const api = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
};

export { api };
export default api;
