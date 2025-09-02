/**
 * Companies Service - API calls tipadas para empresas
 * Implementação TypeScript com type safety completo
 */

import { get, post, put, del } from './api';
import { 
  Company, 
  CompanyDetailed, 
  CompanyCreate, 
  CompanyUpdate, 
  CompanyList,
  PaginatedResponse,
  PersonType,
  PersonStatus,
  PhoneType,
  EmailType,
  AddressType
} from '@/types';

// ===============================
// COMPANIES API SERVICE
// ===============================

class CompaniesService {
  private readonly basePath = '/api/v1/companies';

  /**
   * Listar empresas com paginação
   */
  async getAll(params?: {
    page?: number;
    per_page?: number;
    search?: string;
    status?: string;
  }): Promise<PaginatedResponse<CompanyList>> {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.per_page) queryParams.append('per_page', params.per_page.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.status) queryParams.append('status', params.status);
    
    const url = `${this.basePath}/?${queryParams.toString()}`;
    return get<PaginatedResponse<CompanyList>>(url);
  }

  /**
   * Buscar empresa por ID
   */
  async getById(id: number): Promise<CompanyDetailed> {
    return get<CompanyDetailed>(`${this.basePath}/${id}`);
  }

  /**
   * Buscar empresa por CNPJ
   */
  async getByCNPJ(cnpj: string): Promise<CompanyDetailed> {
    const cleanCNPJ = cnpj.replace(/\D/g, '');
    return get<CompanyDetailed>(`${this.basePath}/cnpj/${cleanCNPJ}`);
  }

  /**
   * Criar nova empresa
   */
  async create(data: CompanyCreate): Promise<CompanyDetailed> {
    return post<CompanyDetailed, CompanyCreate>(this.basePath, data);
  }

  /**
   * Atualizar empresa existente
   */
  async update(id: number, data: CompanyUpdate): Promise<CompanyDetailed> {
    return put<CompanyDetailed, CompanyUpdate>(`${this.basePath}/${id}`, data);
  }

  /**
   * Deletar empresa (soft delete)
   */
  async delete(id: number): Promise<void> {
    await del<void>(`${this.basePath}/${id}`);
  }

  /**
   * Buscar empresas por filtros avançados
   */
  async search(filters: {
    name?: string;
    tax_id?: string;
    city?: string;
    state?: string;
    status?: string;
    person_type?: 'PF' | 'PJ';
  }): Promise<CompanyList[]> {
    const queryParams = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value) queryParams.append(key, value);
    });
    
    const url = `${this.basePath}/search?${queryParams.toString()}`;
    return get<CompanyList[]>(url);
  }

  /**
   * Validar se CNPJ já existe
   */
  async validateCNPJ(cnpj: string): Promise<{ exists: boolean; company?: CompanyList }> {
    const cleanCNPJ = cnpj.replace(/\D/g, '');
    try {
      const company = await get<CompanyList>(`${this.basePath}/validate/cnpj/${cleanCNPJ}`);
      return { exists: true, company };
    } catch (error: any) {
      if (error.status_code === 404) {
        return { exists: false };
      }
      throw error;
    }
  }

  /**
   * Enriquecer endereço com ViaCEP e geocoding
   */
  async enrichAddress(address: {
    street?: string;
    number?: string;
    neighborhood?: string;
    city?: string;
    state?: string;
    zip_code: string;
    country?: string;
  }): Promise<{
    street: string;
    neighborhood: string;
    city: string;
    state: string;
    zip_code: string;
    ibge_city_code?: number;
    latitude?: number;
    longitude?: number;
    geocoding_accuracy?: string;
  }> {
    return post<any, any>('/api/v1/geocoding/enrich-address', address);
  }
}

// ===============================
// CNPJ CONSULTATION SERVICE
// ===============================

interface CNPJData {
  cnpj: string;
  nome: string;
  fantasia?: string;
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  municipio: string;
  uf: string;
  cep: string;
  telefone?: string;
  email?: string;
  situacao: string;
  data_situacao: string;
  atividade_principal: Array<{
    code: string;
    text: string;
  }>;
}

class CNPJService {
  /**
   * Consultar CNPJ na Receita Federal
   */
  async consultCNPJ(cnpj: string): Promise<CNPJData> {
    const cleanCNPJ = cnpj.replace(/\D/g, '');
    return get<CNPJData>(`/api/v1/cnpj/${cleanCNPJ}`);
  }

  /**
   * Converter dados do CNPJ para formato do CompanyCreate
   */
  convertCNPJToCompanyData(cnpjData: CNPJData): CompanyCreate {
    return {
      people: {
        person_type: PersonType.PJ,
        name: cnpjData.nome,
        trade_name: cnpjData.fantasia || undefined,
        tax_id: cnpjData.cnpj.replace(/\D/g, ''),
        status: cnpjData.situacao === 'ATIVA' ? PersonStatus.ACTIVE : PersonStatus.INACTIVE,
      },
      company: {
        settings: {},
        metadata: {
          cnpj_consultation_date: new Date().toISOString(),
          atividade_principal: cnpjData.atividade_principal
        },
        display_order: 0
      },
      phones: cnpjData.telefone ? [{
        country_code: '55',
        number: cnpjData.telefone.replace(/\D/g, ''),
        type: PhoneType.COMMERCIAL,
        is_principal: true,
        is_active: true,
        is_whatsapp: false,
        whatsapp_verified: false,
        whatsapp_business: false,
        accepts_whatsapp_marketing: true,
        accepts_whatsapp_notifications: true,
        contact_priority: 5,
        can_receive_calls: true,
        can_receive_sms: true
      }] : [],
      emails: cnpjData.email ? [{
        email_address: cnpjData.email,
        type: EmailType.WORK,
        is_principal: true,
        is_active: true
      }] : [],
      addresses: [{
        street: cnpjData.logradouro,
        number: cnpjData.numero,
        details: cnpjData.complemento || undefined,
        neighborhood: cnpjData.bairro,
        city: cnpjData.municipio,
        state: cnpjData.uf,
        zip_code: cnpjData.cep.replace(/\D/g, ''),
        country: 'BR',
        type: AddressType.COMMERCIAL,
        is_principal: true,
        is_validated: false
      }]
    };
  }
}

// ===============================
// SINGLETON INSTANCES
// ===============================

export const companiesService = new CompaniesService();
export const cnpjService = new CNPJService();

// Default export
export default companiesService;