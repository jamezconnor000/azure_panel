/**
 * Aether Bifrost API Client
 * Connects Aether Saga to the Bifrost API server
 */

import axios from 'axios';

// API base URL - configurable via environment
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Types
// ============================================================================

export interface Card {
  card_number: string;
  permission_id: number;
  holder_name?: string;
  facility_code: number;
  activation_date: number;
  expiration_date: number;
  is_active: boolean;
  status?: number;
}

export interface CardHolder {
  id: number;
  card_number: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  department?: string;
  employee_id?: string;
  badge_number?: string;
  photo_url?: string;
  activation_date: number;
  expiration_date: number;
  is_active: boolean;
  notes?: string;
  created_at: number;
  updated_at: number;
}

export interface Door {
  door_id: number;
  name: string;
  strike_time_ms: number;
  reader_mode?: number;
  osdp_enabled?: boolean;
}

export interface AccessLevel {
  id?: number;
  permission_id: number;
  name: string;
  description?: string;
  doors?: number[];
  priority?: number;
  is_active?: boolean;
}

export interface Event {
  event_id: number;
  event_type: number;
  card_number?: string;
  door_id?: number;
  timestamp: string;
  details?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
}

// ============================================================================
// Auth API
// ============================================================================

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await api.post('/api/v2.1/auth/login', { username, password });
    localStorage.setItem('auth_token', response.data.access_token);
    return response.data;
  },

  logout: async () => {
    await api.post('/api/v2.1/auth/logout');
    localStorage.removeItem('auth_token');
  },

  me: async () => {
    const response = await api.get('/api/v2.1/auth/me');
    return response.data as User;
  },
};

// ============================================================================
// Cards API
// ============================================================================

export const cardsApi = {
  list: async (limit = 100, offset = 0) => {
    const response = await api.get(`/hal/cards?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  get: async (cardNumber: string) => {
    const response = await api.get(`/hal/cards/${cardNumber}`);
    return response.data as Card;
  },

  create: async (card: Partial<Card>) => {
    const response = await api.post('/hal/cards', card);
    return response.data as Card;
  },

  update: async (cardNumber: string, card: Partial<Card>) => {
    const response = await api.put(`/hal/cards/${cardNumber}`, card);
    return response.data as Card;
  },

  delete: async (cardNumber: string) => {
    await api.delete(`/hal/cards/${cardNumber}`);
  },

  getStatus: async (cardNumber: string) => {
    const response = await api.get(`/hal/cards/${cardNumber}/status`);
    return response.data;
  },

  setStatus: async (cardNumber: string, status: number) => {
    const response = await api.put(`/hal/cards/${cardNumber}/status`, { status });
    return response.data;
  },

  resetApb: async (cardNumber: string) => {
    const response = await api.post(`/hal/cards/${cardNumber}/reset-apb`);
    return response.data;
  },

  getHistory: async (cardNumber: string, limit = 50) => {
    const response = await api.get(`/hal/cards/${cardNumber}/history?limit=${limit}`);
    return response.data;
  },
};

// ============================================================================
// Card Holders API
// ============================================================================

export const cardHoldersApi = {
  list: async (includeInactive = false) => {
    const response = await api.get(`/api/v2.1/card-holders?include_inactive=${includeInactive}`);
    return response.data as CardHolder[];
  },

  get: async (id: number) => {
    const response = await api.get(`/api/v2.1/card-holders/${id}`);
    return response.data as CardHolder;
  },

  create: async (cardHolder: Partial<CardHolder>) => {
    const response = await api.post('/api/v2.1/card-holders', cardHolder);
    return response.data as CardHolder;
  },

  update: async (id: number, cardHolder: Partial<CardHolder>) => {
    const response = await api.put(`/api/v2.1/card-holders/${id}`, cardHolder);
    return response.data as CardHolder;
  },

  delete: async (id: number, permanent = false) => {
    await api.delete(`/api/v2.1/card-holders/${id}?permanent=${permanent}`);
  },

  getAccessLevels: async (id: number) => {
    const response = await api.get(`/api/v2.1/card-holders/${id}/access-levels`);
    return response.data;
  },

  grantAccessLevel: async (id: number, levelId: number) => {
    const response = await api.post(`/api/v2.1/card-holders/${id}/access-levels/${levelId}`);
    return response.data;
  },

  revokeAccessLevel: async (id: number, levelId: number) => {
    await api.delete(`/api/v2.1/card-holders/${id}/access-levels/${levelId}`);
  },

  getDoors: async (id: number) => {
    const response = await api.get(`/api/v2.1/card-holders/${id}/doors`);
    return response.data;
  },
};

// ============================================================================
// Doors API
// ============================================================================

export const doorsApi = {
  list: async () => {
    const response = await api.get('/hal/doors');
    return response.data;
  },

  get: async (doorId: number) => {
    const response = await api.get(`/hal/doors/${doorId}`);
    return response.data as Door;
  },

  create: async (door: Partial<Door>) => {
    const response = await api.post('/hal/doors', door);
    return response.data as Door;
  },

  delete: async (doorId: number) => {
    await api.delete(`/hal/doors/${doorId}`);
  },

  unlock: async (doorId: number, durationSeconds = 5) => {
    const response = await api.post(`/api/v1/doors/${doorId}/unlock?duration_seconds=${durationSeconds}`);
    return response.data;
  },

  lock: async (doorId: number) => {
    const response = await api.post(`/api/v1/doors/${doorId}/lock`);
    return response.data;
  },

  getReaderMode: async (doorId: number) => {
    const response = await api.get(`/hal/readers/${doorId}/mode`);
    return response.data;
  },

  setReaderMode: async (doorId: number, mode: number) => {
    const response = await api.post(`/hal/readers/${doorId}/mode`, { mode });
    return response.data;
  },
};

// ============================================================================
// Access Levels API
// ============================================================================

export const accessLevelsApi = {
  list: async () => {
    const response = await api.get('/hal/access-levels');
    return response.data;
  },

  get: async (permissionId: number) => {
    const response = await api.get(`/hal/access-levels/${permissionId}`);
    return response.data as AccessLevel;
  },

  create: async (level: Partial<AccessLevel>) => {
    const response = await api.post('/hal/access-levels', level);
    return response.data as AccessLevel;
  },

  delete: async (permissionId: number) => {
    await api.delete(`/hal/access-levels/${permissionId}`);
  },
};

// ============================================================================
// Events API
// ============================================================================

export const eventsApi = {
  list: async (limit = 100, offset = 0) => {
    const response = await api.get(`/hal/events?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  getAlarms: async (limit = 500) => {
    const response = await api.get(`/hal/alarms?limit=${limit}`);
    return response.data;
  },

  getAlarmCount: async () => {
    const response = await api.get('/hal/alarms/count');
    return response.data;
  },
};

// ============================================================================
// System API
// ============================================================================

// ============================================================================
// Skald Chronicle API (Port 8090)
// ============================================================================

const SKALD_BASE = import.meta.env.VITE_SKALD_URL || 'http://localhost:8090';

export const skaldApi = {
  getStatus: async () => {
    const response = await axios.get(`${SKALD_BASE}/api/v1/status`);
    return response.data;
  },

  getChronicle: async (limit = 100, offset = 0) => {
    const response = await axios.get(`${SKALD_BASE}/api/v1/chronicle?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  getEvent: async (eventId: string) => {
    const response = await axios.get(`${SKALD_BASE}/api/v1/chronicle/${eventId}`);
    return response.data;
  },

  recordEvent: async (event: {
    event_type: string;
    source: string;
    action: string;
    actor_id?: string;
    actor_name?: string;
    target_id?: string;
    target_name?: string;
    result?: string;
    details?: Record<string, unknown>;
  }) => {
    const response = await axios.post(`${SKALD_BASE}/api/v1/chronicle`, event);
    return response.data;
  },

  verifyIntegrity: async (startId?: number, endId?: number) => {
    const params = new URLSearchParams();
    if (startId) params.append('start_id', startId.toString());
    if (endId) params.append('end_id', endId.toString());
    const response = await axios.get(`${SKALD_BASE}/api/v1/verify?${params.toString()}`);
    return response.data;
  },

  createExport: async (format: 'json' | 'csv' | 'siem', filters?: {
    start_date?: string;
    end_date?: string;
    event_types?: string[];
    actor_id?: string;
    target_id?: string;
  }) => {
    const response = await axios.post(`${SKALD_BASE}/api/v1/export`, { format, ...filters });
    return response.data;
  },

  getExportStatus: async (jobId: string) => {
    const response = await axios.get(`${SKALD_BASE}/api/v1/export/${jobId}`);
    return response.data;
  },

  downloadExport: async (jobId: string) => {
    const response = await axios.get(`${SKALD_BASE}/api/v1/export/${jobId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  },
};

// ============================================================================
// System API
// ============================================================================

export const systemApi = {
  health: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  stats: async () => {
    const response = await api.get('/hal/stats');
    return response.data;
  },

  diagnostics: async () => {
    const response = await api.get('/hal/diagnostics');
    return response.data;
  },

  dashboard: async () => {
    const response = await api.get('/api/v1/dashboard');
    return response.data;
  },

  deviceStatus: async () => {
    const response = await api.get('/hal/device-status');
    return response.data;
  },

  readerModes: async () => {
    const response = await api.get('/hal/readers/modes');
    return response.data;
  },

  credentialStatuses: async () => {
    const response = await api.get('/hal/credential-statuses');
    return response.data;
  },

  lockdown: async (reason: string) => {
    const response = await api.post(`/api/v1/control/lockdown?reason=${encodeURIComponent(reason)}`);
    return response.data;
  },

  unlockAll: async (reason: string) => {
    const response = await api.post(`/api/v1/control/unlock-all?reason=${encodeURIComponent(reason)}`);
    return response.data;
  },
};

export default api;
