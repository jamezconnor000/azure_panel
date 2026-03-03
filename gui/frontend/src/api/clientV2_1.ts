/**
 * AetherAccess v2.1 - API Client
 * TypeScript client for v2.1 authentication, user management, door configuration
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  UserInfo,
  User,
  UserCreate,
  UserUpdate,
  PasswordChange,
  DoorConfig,
  DoorConfigCreate,
  DoorConfigUpdate,
  OSDPEnableRequest,
  AccessLevel,
  AccessLevelCreate,
  AccessLevelUpdate,
  AccessLevelDoorAssignment,
  AccessLevelDoor,
  UserAccessLevelGrant,
  UserAccessLevel,
  UserDoorAccess,
  AuditLog,
  AuditLogQuery,
  MessageResponse,
  APIError
} from '../types/v2.1';

class AetherAccessAPIClientV2_1 {
  private client: AxiosInstance;
  private tokenKey = 'aetheraccess_token';
  private refreshTokenKey = 'aetheraccess_refresh_token';
  private userKey = 'aetheraccess_user';

  constructor(baseURL: string = '/api/v2.1') {
    this.client = axios.create({
      baseURL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<APIError>) => {
        // Handle 401 errors (unauthorized)
        if (error.response?.status === 401) {
          // Try to refresh token
          const refreshed = await this.tryRefreshToken();
          if (refreshed && error.config) {
            // Retry the original request
            return this.client.request(error.config);
          } else {
            // Refresh failed, logout
            this.logout();
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // ===========================================================================
  // Token Management
  // ===========================================================================

  private getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  private setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem(this.refreshTokenKey);
  }

  private setRefreshToken(token: string): void {
    localStorage.setItem(this.refreshTokenKey, token);
  }

  private setUser(user: UserInfo): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  getCurrentUser(): UserInfo | null {
    const userJson = localStorage.getItem(this.userKey);
    if (!userJson) return null;
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private clearAuth(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
  }

  private async tryRefreshToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await axios.post(`/api/v2.1/auth/refresh`, { refresh_token: refreshToken });
      this.setToken(response.data.access_token);
      return true;
    } catch {
      return false;
    }
  }

  // ===========================================================================
  // Authentication
  // ===========================================================================

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', credentials);
    this.setToken(response.data.access_token);
    this.setRefreshToken(response.data.refresh_token);
    this.setUser(response.data.user);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch {
      // Ignore errors on logout
    } finally {
      this.clearAuth();
      // Redirect to login
      window.location.href = '/login';
    }
  }

  async fetchCurrentUser(): Promise<UserInfo> {
    const response = await this.client.get<UserInfo>('/auth/me');
    this.setUser(response.data);
    return response.data;
  }

  // ===========================================================================
  // User Management
  // ===========================================================================

  async createUser(userData: UserCreate): Promise<User> {
    const response = await this.client.post<User>('/users', userData);
    return response.data;
  }

  async getUsers(includeInactive = false): Promise<User[]> {
    const response = await this.client.get<User[]>('/users', {
      params: { include_inactive: includeInactive }
    });
    return response.data;
  }

  async getUser(userId: number): Promise<User> {
    const response = await this.client.get<User>(`/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: number, userData: UserUpdate): Promise<User> {
    const response = await this.client.put<User>(`/users/${userId}`, userData);
    return response.data;
  }

  async deleteUser(userId: number): Promise<MessageResponse> {
    const response = await this.client.delete<MessageResponse>(`/users/${userId}`);
    return response.data;
  }

  async changePassword(userId: number, passwordData: PasswordChange): Promise<MessageResponse> {
    const response = await this.client.post<MessageResponse>(
      `/users/${userId}/change-password`,
      passwordData
    );
    return response.data;
  }

  async getUserDoors(userId: number): Promise<UserDoorAccess[]> {
    const response = await this.client.get<UserDoorAccess[]>(`/users/${userId}/doors`);
    return response.data;
  }

  // ===========================================================================
  // Door Configuration
  // ===========================================================================

  async createDoorConfig(doorData: DoorConfigCreate): Promise<DoorConfig> {
    const response = await this.client.post<DoorConfig>('/doors', doorData);
    return response.data;
  }

  async getDoorConfigs(): Promise<DoorConfig[]> {
    const response = await this.client.get<DoorConfig[]>('/doors');
    return response.data;
  }

  async getDoorConfig(doorId: number): Promise<DoorConfig> {
    const response = await this.client.get<DoorConfig>(`/doors/${doorId}`);
    return response.data;
  }

  async updateDoorConfig(doorId: number, doorData: DoorConfigUpdate): Promise<DoorConfig> {
    const response = await this.client.put<DoorConfig>(`/doors/${doorId}`, doorData);
    return response.data;
  }

  async deleteDoorConfig(doorId: number): Promise<MessageResponse> {
    const response = await this.client.delete<MessageResponse>(`/doors/${doorId}`);
    return response.data;
  }

  async enableOSDP(doorId: number, osdpData: OSDPEnableRequest): Promise<MessageResponse> {
    const response = await this.client.post<MessageResponse>(
      `/doors/${doorId}/osdp/enable`,
      osdpData
    );
    return response.data;
  }

  async disableOSDP(doorId: number): Promise<MessageResponse> {
    const response = await this.client.post<MessageResponse>(`/doors/${doorId}/osdp/disable`);
    return response.data;
  }

  // ===========================================================================
  // Access Levels
  // ===========================================================================

  async createAccessLevel(levelData: AccessLevelCreate): Promise<AccessLevel> {
    const response = await this.client.post<AccessLevel>('/access-levels', levelData);
    return response.data;
  }

  async getAccessLevels(includeInactive = false): Promise<AccessLevel[]> {
    const response = await this.client.get<AccessLevel[]>('/access-levels', {
      params: { include_inactive: includeInactive }
    });
    return response.data;
  }

  async getAccessLevel(levelId: number): Promise<AccessLevel> {
    const response = await this.client.get<AccessLevel>(`/access-levels/${levelId}`);
    return response.data;
  }

  async updateAccessLevel(levelId: number, levelData: AccessLevelUpdate): Promise<AccessLevel> {
    const response = await this.client.put<AccessLevel>(`/access-levels/${levelId}`, levelData);
    return response.data;
  }

  async deleteAccessLevel(levelId: number): Promise<MessageResponse> {
    const response = await this.client.delete<MessageResponse>(`/access-levels/${levelId}`);
    return response.data;
  }

  async addDoorToAccessLevel(
    levelId: number,
    assignment: AccessLevelDoorAssignment
  ): Promise<MessageResponse> {
    const response = await this.client.post<MessageResponse>(
      `/access-levels/${levelId}/doors`,
      assignment
    );
    return response.data;
  }

  async removeDoorFromAccessLevel(levelId: number, doorId: number): Promise<MessageResponse> {
    const response = await this.client.delete<MessageResponse>(
      `/access-levels/${levelId}/doors/${doorId}`
    );
    return response.data;
  }

  async getAccessLevelDoors(levelId: number): Promise<AccessLevelDoor[]> {
    const response = await this.client.get<AccessLevelDoor[]>(`/access-levels/${levelId}/doors`);
    return response.data;
  }

  // ===========================================================================
  // User Access Level Assignment
  // ===========================================================================

  async grantUserAccessLevel(
    userId: number,
    grantData: UserAccessLevelGrant
  ): Promise<MessageResponse> {
    const response = await this.client.post<MessageResponse>(
      `/users/${userId}/access-levels`,
      grantData
    );
    return response.data;
  }

  async revokeUserAccessLevel(userId: number, levelId: number): Promise<MessageResponse> {
    const response = await this.client.delete<MessageResponse>(
      `/users/${userId}/access-levels/${levelId}`
    );
    return response.data;
  }

  async getUserAccessLevels(userId: number): Promise<UserAccessLevel[]> {
    const response = await this.client.get<UserAccessLevel[]>(`/users/${userId}/access-levels`);
    return response.data;
  }

  // ===========================================================================
  // Audit Logs
  // ===========================================================================

  async getAuditLogs(query: AuditLogQuery = {}): Promise<AuditLog[]> {
    const response = await this.client.get<AuditLog[]>('/audit-logs', { params: query });
    return response.data;
  }

  // ===========================================================================
  // Card Holders
  // ===========================================================================

  async createCardHolder(data: any): Promise<any> {
    const response = await this.client.post('/card-holders', data);
    return response.data;
  }

  async getCardHolders(includeInactive: boolean = false): Promise<any[]> {
    const response = await this.client.get('/card-holders', {
      params: { include_inactive: includeInactive }
    });
    return response.data;
  }

  async getCardHolder(cardHolderId: number): Promise<any> {
    const response = await this.client.get(`/card-holders/${cardHolderId}`);
    return response.data;
  }

  async updateCardHolder(cardHolderId: number, data: any): Promise<any> {
    const response = await this.client.put(`/card-holders/${cardHolderId}`, data);
    return response.data;
  }

  async deleteCardHolder(cardHolderId: number, permanent: boolean = false): Promise<MessageResponse> {
    const response = await this.client.delete(`/card-holders/${cardHolderId}`, {
      params: { permanent }
    });
    return response.data;
  }

  async grantCardHolderAccessLevel(cardHolderId: number, levelId: number): Promise<MessageResponse> {
    const response = await this.client.post(`/card-holders/${cardHolderId}/access-levels/${levelId}`);
    return response.data;
  }

  async revokeCardHolderAccessLevel(cardHolderId: number, levelId: number): Promise<MessageResponse> {
    const response = await this.client.delete(`/card-holders/${cardHolderId}/access-levels/${levelId}`);
    return response.data;
  }

  async getCardHolderAccessLevels(cardHolderId: number): Promise<any[]> {
    const response = await this.client.get(`/card-holders/${cardHolderId}/access-levels`);
    return response.data;
  }

  async getCardHolderDoors(cardHolderId: number): Promise<any[]> {
    const response = await this.client.get(`/card-holders/${cardHolderId}/doors`);
    return response.data;
  }

  async getAccessLevelCardHolders(levelId: number): Promise<any[]> {
    const response = await this.client.get(`/access-levels/${levelId}/card-holders`);
    return response.data;
  }
}

// Create singleton instance
const apiClientV2_1 = new AetherAccessAPIClientV2_1();

export default apiClientV2_1;
