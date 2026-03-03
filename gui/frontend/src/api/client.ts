/**
 * HAL Control Panel - API Client
 * TypeScript client for HAL backend API
 */

import axios, { AxiosInstance } from 'axios';
import type {
  PanelIOStatus,
  PanelHealth,
  ReaderHealth,
  ReaderHealthSummary,
  ControlResult,
  Macro,
  IOOverride,
} from '../types';

class HALAPIClient {
  private client: AxiosInstance;
  private wsConnection: WebSocket | null = null;
  private wsReconnectAttempts = 0;
  private wsMaxReconnectAttempts = 5;
  private wsReconnectDelay = 3000;
  private wsListeners: Map<string, Set<(data: any) => void>> = new Map();

  constructor(baseURL: string = '/api/v1') {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ===========================================================================
  // Panel I/O Monitoring
  // ===========================================================================

  async getPanelIO(panelId: number): Promise<PanelIOStatus> {
    const response = await this.client.get(`/panels/${panelId}/io`);
    return response.data;
  }

  async getPanelHealth(panelId: number): Promise<PanelHealth> {
    const response = await this.client.get(`/panels/${panelId}/health`);
    return response.data;
  }

  // ===========================================================================
  // Reader Health Monitoring
  // ===========================================================================

  async getReaderHealth(readerId: number): Promise<ReaderHealth> {
    const response = await this.client.get(`/readers/${readerId}/health`);
    return response.data;
  }

  async getAllReadersHealth(): Promise<{ readers: ReaderHealthSummary[]; timestamp: string }> {
    const response = await this.client.get('/readers/health/summary');
    return response.data;
  }

  // ===========================================================================
  // Door Control
  // ===========================================================================

  async unlockDoor(
    doorId: number,
    durationSeconds?: number,
    reason?: string
  ): Promise<ControlResult> {
    const params: any = {};
    if (durationSeconds) params.duration_seconds = durationSeconds;
    if (reason) params.reason = reason;

    const response = await this.client.post(`/doors/${doorId}/unlock`, null, { params });
    return response.data;
  }

  async lockDoor(doorId: number, reason?: string): Promise<ControlResult> {
    const params: any = {};
    if (reason) params.reason = reason;

    const response = await this.client.post(`/doors/${doorId}/lock`, null, { params });
    return response.data;
  }

  async lockdownDoor(doorId: number, reason: string): Promise<ControlResult> {
    const response = await this.client.post(`/doors/${doorId}/lockdown`, { reason });
    return response.data;
  }

  async releaseDoor(doorId: number): Promise<ControlResult> {
    const response = await this.client.post(`/doors/${doorId}/release`);
    return response.data;
  }

  // ===========================================================================
  // Output Control
  // ===========================================================================

  async activateOutput(outputId: number, durationMs?: number): Promise<ControlResult> {
    const params: any = {};
    if (durationMs) params.duration_ms = durationMs;

    const response = await this.client.post(`/outputs/${outputId}/activate`, null, { params });
    return response.data;
  }

  async deactivateOutput(outputId: number): Promise<ControlResult> {
    const response = await this.client.post(`/outputs/${outputId}/deactivate`);
    return response.data;
  }

  async pulseOutput(outputId: number, durationMs: number = 1000): Promise<ControlResult> {
    const response = await this.client.post(`/outputs/${outputId}/pulse`, null, {
      params: { duration_ms: durationMs },
    });
    return response.data;
  }

  async toggleOutput(outputId: number): Promise<ControlResult> {
    const response = await this.client.post(`/outputs/${outputId}/toggle`);
    return response.data;
  }

  // ===========================================================================
  // Relay Control
  // ===========================================================================

  async activateRelay(relayId: number, durationMs?: number): Promise<ControlResult> {
    const params: any = {};
    if (durationMs) params.duration_ms = durationMs;

    const response = await this.client.post(`/relays/${relayId}/activate`, null, { params });
    return response.data;
  }

  async deactivateRelay(relayId: number): Promise<ControlResult> {
    const response = await this.client.post(`/relays/${relayId}/deactivate`);
    return response.data;
  }

  // ===========================================================================
  // Mass Control (Emergency Operations)
  // ===========================================================================

  async emergencyLockdown(reason: string, initiatedBy: string = 'Web UI'): Promise<ControlResult> {
    const response = await this.client.post('/control/lockdown', {
      reason,
      initiated_by: initiatedBy,
    });
    return response.data;
  }

  async emergencyUnlockAll(reason: string, initiatedBy: string = 'Web UI'): Promise<ControlResult> {
    const response = await this.client.post('/control/unlock-all', {
      reason,
      initiated_by: initiatedBy,
    });
    return response.data;
  }

  async returnToNormal(initiatedBy: string = 'Web UI'): Promise<ControlResult> {
    const response = await this.client.post('/control/normal', {
      initiated_by: initiatedBy,
    });
    return response.data;
  }

  // ===========================================================================
  // Control Macros
  // ===========================================================================

  async listMacros(): Promise<{ macros: Macro[] }> {
    const response = await this.client.get('/macros');
    return response.data;
  }

  async executeMacro(macroId: number, initiatedBy: string = 'Web UI'): Promise<{ macro_id: number; results: ControlResult[] }> {
    const response = await this.client.post(`/macros/${macroId}/execute`, {
      initiated_by: initiatedBy,
    });
    return response.data;
  }

  // ===========================================================================
  // Override Management
  // ===========================================================================

  async getActiveOverrides(): Promise<IOOverride[]> {
    const response = await this.client.get('/overrides');
    return response.data;
  }

  async clearOverride(overrideId: number): Promise<ControlResult> {
    const response = await this.client.delete(`/overrides/${overrideId}`);
    return response.data;
  }

  // ===========================================================================
  // WebSocket for Real-time Updates
  // ===========================================================================

  connectWebSocket(url: string = 'ws://localhost:8080/ws/live'): void {
    if (this.wsConnection) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      this.wsConnection = new WebSocket(url);

      this.wsConnection.onopen = () => {
        console.log('✓ WebSocket connected');
        this.wsReconnectAttempts = 0;

        // Subscribe to all topics
        this.wsConnection?.send(
          JSON.stringify({
            action: 'subscribe',
            topics: ['io_changes', 'door_control', 'health_alerts', 'mass_control'],
          })
        );
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.wsConnection.onclose = () => {
        console.log('✗ WebSocket disconnected');
        this.wsConnection = null;
        this.reconnectWebSocket(url);
      };

      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  private reconnectWebSocket(url: string): void {
    if (this.wsReconnectAttempts < this.wsMaxReconnectAttempts) {
      this.wsReconnectAttempts++;
      console.log(
        `Reconnecting WebSocket in ${this.wsReconnectDelay / 1000}s... (${this.wsReconnectAttempts}/${this.wsMaxReconnectAttempts})`
      );
      setTimeout(() => this.connectWebSocket(url), this.wsReconnectDelay);
    } else {
      console.error('Max WebSocket reconnection attempts reached');
    }
  }

  private handleWebSocketMessage(message: any): void {
    // Notify all listeners for this message type
    const listeners = this.wsListeners.get(message.type);
    if (listeners) {
      listeners.forEach((callback) => callback(message));
    }

    // Notify wildcard listeners
    const wildcardListeners = this.wsListeners.get('*');
    if (wildcardListeners) {
      wildcardListeners.forEach((callback) => callback(message));
    }
  }

  onWebSocketMessage(type: string, callback: (data: any) => void): () => void {
    if (!this.wsListeners.has(type)) {
      this.wsListeners.set(type, new Set());
    }
    this.wsListeners.get(type)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.wsListeners.get(type)?.delete(callback);
    };
  }

  disconnectWebSocket(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }
}

// Create singleton instance
export const apiClient = new HALAPIClient();

export default HALAPIClient;
