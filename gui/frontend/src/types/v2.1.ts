/**
 * AetherAccess v2.1 - TypeScript Type Definitions
 * User Management, Authentication, Door Configuration, Access Levels
 */

export type UserRole = 'admin' | 'operator' | 'guard' | 'user';
export type DoorType = 'entry' | 'exit' | 'interior' | 'emergency';

// =============================================================================
// Authentication
// =============================================================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
}

// =============================================================================
// Users
// =============================================================================

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  phone?: string;
  is_active: boolean;
  last_login_at?: number;
  created_at: number;
  updated_at?: number;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  phone?: string;
}

export interface UserUpdate {
  email?: string;
  first_name?: string;
  last_name?: string;
  role?: UserRole;
  phone?: string;
  is_active?: boolean;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

// =============================================================================
// Door Configuration
// =============================================================================

export interface DoorConfig {
  door_id: number;
  door_name: string;
  description?: string;
  location?: string;
  door_type?: DoorType;
  osdp_enabled: boolean;
  scbk?: string;
  reader_address?: number;
  baud_rate: number;
  led_control: boolean;
  buzzer_control: boolean;
  biometric_enabled: boolean;
  display_enabled: boolean;
  keypad_enabled: boolean;
  is_monitored: boolean;
  alert_on_failure: boolean;
  notes?: string;
  created_at: number;
  updated_at: number;
}

export interface DoorConfigCreate {
  door_id: number;
  door_name: string;
  description?: string;
  location?: string;
  door_type?: DoorType;
  osdp_enabled?: boolean;
  scbk?: string;
  reader_address?: number;
  baud_rate?: number;
  led_control?: boolean;
  buzzer_control?: boolean;
  biometric_enabled?: boolean;
  display_enabled?: boolean;
  keypad_enabled?: boolean;
  is_monitored?: boolean;
  alert_on_failure?: boolean;
  notes?: string;
}

export interface DoorConfigUpdate {
  door_name?: string;
  description?: string;
  location?: string;
  door_type?: DoorType;
  osdp_enabled?: boolean;
  scbk?: string;
  reader_address?: number;
  baud_rate?: number;
  led_control?: boolean;
  buzzer_control?: boolean;
  biometric_enabled?: boolean;
  display_enabled?: boolean;
  keypad_enabled?: boolean;
  is_monitored?: boolean;
  alert_on_failure?: boolean;
  notes?: string;
}

export interface OSDPEnableRequest {
  scbk: string;
  reader_address: number;
}

// =============================================================================
// Access Levels
// =============================================================================

export interface AccessLevel {
  id: number;
  name: string;
  description?: string;
  priority: number;
  is_active: boolean;
  created_at: number;
  updated_at?: number;
}

export interface AccessLevelCreate {
  name: string;
  description?: string;
  priority?: number;
}

export interface AccessLevelUpdate {
  name?: string;
  description?: string;
  priority?: number;
  is_active?: boolean;
}

export interface AccessLevelDoorAssignment {
  door_id: number;
  timezone_id?: number;
  entry_allowed?: boolean;
  exit_allowed?: boolean;
}

export interface AccessLevelDoor {
  id: number;
  access_level_id: number;
  door_id: number;
  door_name: string;
  location?: string;
  door_type?: string;
  timezone_id: number;
  entry_allowed: boolean;
  exit_allowed: boolean;
  created_at: number;
}

export interface UserAccessLevelGrant {
  access_level_id: number;
  activation_date?: number;
  expiration_date?: number;
  notes?: string;
}

export interface UserAccessLevel {
  id: number;
  name: string;
  description?: string;
  priority: number;
  is_active: boolean;
  activation_date: number;
  expiration_date: number;
  assignment_active: boolean;
}

export interface UserDoorAccess {
  door_id: number;
  door_name: string;
  location?: string;
  entry_allowed: boolean;
  exit_allowed: boolean;
}

// =============================================================================
// Audit Logs
// =============================================================================

export interface AuditLog {
  id: number;
  timestamp: number;
  user_id?: number;
  action_type: string;
  resource_type?: string;
  resource_id?: number;
  details?: string;
  ip_address?: string;
  user_agent?: string;
  success: boolean;
  error_message?: string;
}

export interface AuditLogQuery {
  limit?: number;
  offset?: number;
  user_id?: number;
  action_type?: string;
  start_time?: number;
  end_time?: number;
}

// =============================================================================
// API Responses
// =============================================================================

export interface APIError {
  detail: string;
}

export interface MessageResponse {
  message: string;
}

// =============================================================================
// Role Permissions
// =============================================================================

export const RolePermissions: Record<UserRole, string[]> = {
  admin: [
    'user.create', 'user.read', 'user.update', 'user.delete',
    'door.create', 'door.read', 'door.update', 'door.delete',
    'access_level.create', 'access_level.read', 'access_level.update', 'access_level.delete',
    'door.control', 'door.configure', 'system.configure',
    'audit.read', 'reports.generate'
  ],
  operator: [
    'user.read', 'door.read', 'access_level.read',
    'door.control', 'audit.read', 'reports.generate'
  ],
  guard: [
    'door.read', 'door.control', 'audit.read'
  ],
  user: [
    'door.read'
  ]
};

export function hasPermission(role: UserRole, permission: string): boolean {
  return RolePermissions[role]?.includes(permission) || false;
}
