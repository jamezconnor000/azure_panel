/**
 * Aether Static Type Definitions
 */

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

export interface DashboardData {
  system_status: string;
  hal_version: string;
  cards: {
    total?: number;
    active?: number;
  };
  doors: {
    total?: number;
  };
  events: {
    total?: number;
    today?: number;
  };
  recent_events: Event[];
  timestamp: string;
}

export interface ReaderMode {
  id: number;
  name: string;
}

export interface CredentialStatus {
  id: number;
  name: string;
}

// Event type names
export const EVENT_TYPE_NAMES: Record<number, string> = {
  0: 'Access Granted',
  1: 'Access Denied',
  2: 'Door Unlock',
  3: 'Door Forced',
  4: 'Door Held',
  5: 'Tamper',
  6: 'Reader Mode Change',
  7: 'APB Reset',
  8: 'Emergency',
};

// Reader mode names
export const READER_MODE_NAMES: Record<number, string> = {
  1: 'Disabled',
  2: 'Unlocked',
  3: 'Locked (REX Only)',
  4: 'Facility Code Only',
  5: 'Card Only',
  6: 'PIN Only',
  7: 'Card and PIN',
  8: 'Card or PIN',
  9: 'Office First',
  10: 'Blocked',
  11: 'Emergency Lock',
  12: 'Emergency Unlock',
  13: 'Fingerprint',
  14: 'Card and Fingerprint',
  15: 'Card or Fingerprint',
};

// Credential status names
export const CREDENTIAL_STATUS_NAMES: Record<number, string> = {
  1: 'Active',
  2: 'Lost',
  3: 'Returned',
  4: 'Deactivated',
  5: 'Terminated',
  6: 'Broken',
  7: 'Furlough',
};
