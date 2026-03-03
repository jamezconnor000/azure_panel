/**
 * HAL Control Panel - TypeScript Type Definitions
 */

export type SystemStatus = 'HEALTHY' | 'WARNING' | 'ERROR' | 'OFFLINE';
export type IOState = 'active' | 'inactive' | 'unknown' | 'fault';
export type HealthMetric = 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
export type ControlAction = 'activate' | 'deactivate' | 'pulse' | 'toggle' | 'override' | 'release_override';

// =============================================================================
// Panel I/O Monitoring
// =============================================================================

export interface InputState {
  id: number;
  panel_id: number;
  name: string;
  type: string; // DOOR_CONTACT, REX, TAMPER, AUX
  state: IOState;
  last_change: string;
  trigger_count_today: number;
  supervised: boolean;
  resistance_ohms?: number;
  fault_reason?: string;
}

export interface OutputState {
  id: number;
  panel_id: number;
  name: string;
  type: string; // STRIKE, LED, BUZZER, AUX
  state: IOState;
  last_activated?: string;
  activation_count_today: number;
  mode: string; // MOMENTARY, LATCHED, TIMED
  duration_ms?: number;
  controlled_by?: string;
}

export interface RelayState {
  id: number;
  panel_id: number;
  name: string;
  state: IOState;
  last_change: string;
  activation_count_today: number;
  mode: string; // NO, NC, PULSE
  pulse_duration_ms?: number;
  linked_to?: string;
}

export interface PanelIOStatus {
  panel_id: number;
  panel_name: string;
  inputs: InputState[];
  outputs: OutputState[];
  relays: RelayState[];
  last_update: string;
  total_events_today: number;
}

export interface PanelHealth {
  panel_id: number;
  panel_name: string;
  overall_health: HealthMetric;
  health_score: number; // 0-100
  online: boolean;
  uptime_hours: number;
  last_reboot: string;
  firmware_version: string;
  main_power: boolean;
  battery_voltage?: number;
  battery_charge_percent?: number;
  battery_health: HealthMetric;
  network_health: HealthMetric;
  ip_address?: string;
  network_uptime_percent: number;
  avg_latency_ms: number;
  inputs_ok: number;
  inputs_fault: number;
  outputs_ok: number;
  outputs_fault: number;
  relays_ok: number;
  relays_fault: number;
  database_size_mb: number;
  database_health: HealthMetric;
  free_space_mb: number;
  errors_last_24h: number;
  warnings_last_24h: number;
  critical_alerts: string[];
  last_health_check: string;
}

// =============================================================================
// Reader Health
// =============================================================================

export interface ReaderHealth {
  reader_id: number;
  reader_name: string;
  overall_health: HealthMetric;
  health_score: number; // 0-100

  // Communication Health
  comm_health: HealthMetric;
  comm_uptime_percent: number;
  last_successful_comm: string;
  failed_polls_last_hour: number;
  avg_response_time_ms: number;
  packet_loss_percent: number;

  // Secure Channel Health
  sc_health: HealthMetric;
  sc_handshake_success_rate: number;
  sc_mac_failure_rate: number;
  sc_cryptogram_failure_rate: number;
  sc_avg_handshake_time_ms: number;
  sc_rekeys_today: number;

  // Hardware Health
  hardware_health: HealthMetric;
  tamper_status: string; // OK, TAMPERED, UNKNOWN
  power_voltage?: number;
  power_status: string; // NORMAL, LOW, CRITICAL
  temperature_celsius?: number;
  led_status: string; // FUNCTIONAL, FAILED, UNKNOWN
  beeper_status: string;

  // Card Reader Health
  card_reader_health: HealthMetric;
  successful_reads_today: number;
  failed_reads_today: number;
  read_success_rate: number;
  avg_read_time_ms: number;
  card_reader_errors: number;

  // Firmware
  firmware_version: string;
  firmware_up_to_date: boolean;
  last_firmware_update?: string;
  pending_updates: number;

  // Diagnostics
  recent_errors: string[];
  warnings: string[];
  recommendations: string[];
  last_health_check: string;
}

export interface ReaderHealthSummary {
  reader_id: number;
  reader_name: string;
  overall_health: HealthMetric;
  health_score: number;
  issues: number;
}

// =============================================================================
// Control Operations
// =============================================================================

export interface ControlResult {
  success: boolean;
  action: ControlAction;
  target_id: number;
  target_type: string;
  message: string;
  timestamp: string;
  executed_by?: string;
}

export interface DoorControl {
  door_id: number;
  action: string; // UNLOCK, LOCK, UNLOCK_MOMENTARY, LOCKDOWN, RELEASE
  duration_seconds?: number;
  reason?: string;
  initiated_by: string;
}

export interface OutputControl {
  output_id: number;
  action: ControlAction;
  duration_ms?: number;
  reason?: string;
}

export interface RelayControl {
  relay_id: number;
  action: ControlAction;
  duration_ms?: number;
  reason?: string;
}

export interface MassControl {
  target_type: string; // ALL_DOORS, ALL_OUTPUTS, ALL_RELAYS, PANEL
  action: string; // LOCKDOWN, UNLOCK_ALL, NORMAL
  duration_seconds?: number;
  reason: string;
  initiated_by: string;
}

// =============================================================================
// Macros and Overrides
// =============================================================================

export interface Macro {
  macro_id: number;
  name: string;
  description: string;
  actions?: Array<{
    type: string;
    [key: string]: any;
  }>;
}

export interface IOOverride {
  override_id: number;
  target_type: string; // door, output, relay
  target_id: number;
  target_name: string;
  override_state: string; // LOCKED, UNLOCKED, ON, OFF
  override_since: string;
  override_by: string;
  reason: string;
  auto_release?: string;
}

// =============================================================================
// WebSocket Messages
// =============================================================================

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface IOChangeEvent {
  type: 'io_change';
  event: {
    panel_id: number;
    input_id?: number;
    output_id?: number;
    name: string;
    new_state: IOState;
    timestamp: string;
  };
}

export interface DoorControlEvent {
  type: 'door_control';
  action: string;
  door_id: number;
  result: ControlResult;
  timestamp: string;
}

export interface MassControlEvent {
  type: 'mass_control';
  action: string;
  priority?: string;
  result: ControlResult;
  timestamp: string;
}
