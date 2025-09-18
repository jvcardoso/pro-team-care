import { apiRequest } from "./api";

class RolesService {
  async listRoles(params = {}) {
    return apiRequest("GET", "/api/v1/roles/", null, params);
  }

  async getRole(roleId) {
    return apiRequest("GET", `/api/v1/roles/${roleId}`);
  }

  async createRole(roleData) {
    return apiRequest("POST", "/api/v1/roles/", roleData);
  }

  async updateRole(roleId, roleData) {
    return apiRequest("PUT", `/api/v1/roles/${roleId}`, roleData);
  }

  async deleteRole(roleId) {
    return apiRequest("DELETE", `/api/v1/roles/${roleId}`);
  }

  async listPermissions(params = {}) {
    return apiRequest("GET", "/api/v1/roles/permissions/", null, params);
  }

  async getPermissionsGrouped() {
    return apiRequest("GET", "/api/v1/roles/permissions/grouped");
  }

  async getRolePermissions(roleId) {
    return apiRequest("GET", `/api/v1/roles/${roleId}/permissions`);
  }

  async getContextTypes() {
    return apiRequest("GET", "/api/v1/roles/context-types");
  }

  async getRoleLevels() {
    return apiRequest("GET", "/api/v1/roles/levels");
  }

  // Métodos para gerenciar roles de usuários
  async getUserRoles(userId) {
    return apiRequest("GET", `/api/v1/users/${userId}/roles`);
  }

  async assignUserRole(userId, roleId) {
    return apiRequest("POST", `/api/v1/users/${userId}/roles`, {
      role_id: roleId,
    });
  }

  async removeUserRole(userId, roleId) {
    return apiRequest("DELETE", `/api/v1/users/${userId}/roles/${roleId}`);
  }

  async updateUserRoles(userId, roleIds) {
    return apiRequest("PUT", `/api/v1/users/${userId}/roles`, {
      role_ids: roleIds,
    });
  }
}

export const rolesService = new RolesService();
