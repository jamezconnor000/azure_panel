#!/usr/bin/env node
/**
 * HAL GUI API - JavaScript/Node.js Client Example
 * Demonstrates how to integrate with the HAL Control Panel API
 */

const axios = require('axios');

class HALClient {
    constructor(baseURL = 'http://localhost:8080') {
        this.baseURL = baseURL;
        this.apiBase = `${baseURL}/api/v1`;
        this.client = axios.create({
            baseURL: this.apiBase,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    // =========================================================================
    // Azure Panel I/O Monitoring
    // =========================================================================

    async getPanelIO(panelId) {
        const response = await this.client.get(`/panels/${panelId}/io`);
        return response.data;
    }

    async getPanelHealth(panelId) {
        const response = await this.client.get(`/panels/${panelId}/health`);
        return response.data;
    }

    // =========================================================================
    // Reader Health Monitoring
    // =========================================================================

    async getReaderHealth(readerId) {
        const response = await this.client.get(`/readers/${readerId}/health`);
        return response.data;
    }

    async getAllReadersHealth() {
        const response = await this.client.get('/readers/health/summary');
        return response.data;
    }

    // =========================================================================
    // Door Control
    // =========================================================================

    async unlockDoor(doorId, durationSeconds = null, reason = null) {
        const params = {};
        if (durationSeconds) params.duration_seconds = durationSeconds;
        if (reason) params.reason = reason;

        const response = await this.client.post(`/doors/${doorId}/unlock`, null, { params });
        return response.data;
    }

    async lockDoor(doorId, reason = null) {
        const params = {};
        if (reason) params.reason = reason;

        const response = await this.client.post(`/doors/${doorId}/lock`, null, { params });
        return response.data;
    }

    async lockdownDoor(doorId, reason) {
        const response = await this.client.post(`/doors/${doorId}/lockdown`, { reason });
        return response.data;
    }

    async releaseDoor(doorId) {
        const response = await this.client.post(`/doors/${doorId}/release`);
        return response.data;
    }

    // =========================================================================
    // Output Control
    // =========================================================================

    async activateOutput(outputId, durationMs = null) {
        const params = {};
        if (durationMs) params.duration_ms = durationMs;

        const response = await this.client.post(`/outputs/${outputId}/activate`, null, { params });
        return response.data;
    }

    async deactivateOutput(outputId) {
        const response = await this.client.post(`/outputs/${outputId}/deactivate`);
        return response.data;
    }

    async pulseOutput(outputId, durationMs = 1000) {
        const response = await this.client.post(`/outputs/${outputId}/pulse`, null, {
            params: { duration_ms: durationMs }
        });
        return response.data;
    }

    async toggleOutput(outputId) {
        const response = await this.client.post(`/outputs/${outputId}/toggle`);
        return response.data;
    }

    // =========================================================================
    // Relay Control
    // =========================================================================

    async activateRelay(relayId, durationMs = null) {
        const params = {};
        if (durationMs) params.duration_ms = durationMs;

        const response = await this.client.post(`/relays/${relayId}/activate`, null, { params });
        return response.data;
    }

    async deactivateRelay(relayId) {
        const response = await this.client.post(`/relays/${relayId}/deactivate`);
        return response.data;
    }

    // =========================================================================
    // Mass Control (Emergency Operations)
    // =========================================================================

    async emergencyLockdown(reason, initiatedBy = 'JavaScript Client') {
        const response = await this.client.post('/control/lockdown', {
            reason,
            initiated_by: initiatedBy
        });
        return response.data;
    }

    async emergencyUnlockAll(reason, initiatedBy = 'JavaScript Client') {
        const response = await this.client.post('/control/unlock-all', {
            reason,
            initiated_by: initiatedBy
        });
        return response.data;
    }

    async returnToNormal(initiatedBy = 'JavaScript Client') {
        const response = await this.client.post('/control/normal', {
            initiated_by: initiatedBy
        });
        return response.data;
    }

    // =========================================================================
    // Control Macros
    // =========================================================================

    async listMacros() {
        const response = await this.client.get('/macros');
        return response.data;
    }

    async executeMacro(macroId, initiatedBy = 'JavaScript Client') {
        const response = await this.client.post(`/macros/${macroId}/execute`, {
            initiated_by: initiatedBy
        });
        return response.data;
    }

    // =========================================================================
    // Override Management
    // =========================================================================

    async getActiveOverrides() {
        const response = await this.client.get('/overrides');
        return response.data;
    }

    async clearOverride(overrideId) {
        const response = await this.client.delete(`/overrides/${overrideId}`);
        return response.data;
    }
}

// =============================================================================
// WebSocket Example
// =============================================================================

class HALWebSocketClient {
    constructor(wsURL = 'ws://localhost:8080/ws/live') {
        this.wsURL = wsURL;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
    }

    connect() {
        return new Promise((resolve, reject) => {
            const WebSocket = require('ws');
            this.ws = new WebSocket(this.wsURL);

            this.ws.on('open', () => {
                console.log('✓ WebSocket connected');
                this.reconnectAttempts = 0;
                resolve();
            });

            this.ws.on('message', (data) => {
                const message = JSON.parse(data.toString());
                this.handleMessage(message);
            });

            this.ws.on('close', () => {
                console.log('✗ WebSocket disconnected');
                this.reconnect();
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error.message);
                reject(error);
            });
        });
    }

    handleMessage(message) {
        switch (message.type) {
            case 'connected':
                console.log(`Connected: ${message.message}`);
                this.subscribe(['io_changes', 'door_control', 'health_alerts']);
                break;

            case 'io_change':
                console.log(`[I/O CHANGE] Panel ${message.event.panel_id}: ${message.event.name} → ${message.event.new_state}`);
                break;

            case 'door_control':
                console.log(`[DOOR CONTROL] Door ${message.door_id}: ${message.action}`);
                break;

            case 'mass_control':
                console.log(`[MASS CONTROL] ${message.action} - ${message.result.message}`);
                break;

            case 'macro_executed':
                console.log(`[MACRO] Macro ${message.macro_id} executed`);
                break;

            default:
                console.log('Received:', message);
        }
    }

    subscribe(topics) {
        if (this.ws && this.ws.readyState === 1) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                topics: topics
            }));
            console.log(`Subscribed to: ${topics.join(', ')}`);
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting in ${this.reconnectDelay/1000}s... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect().catch(console.error), this.reconnectDelay);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// =============================================================================
// Example Usage
// =============================================================================

async function main() {
    console.log('='.repeat(80));
    console.log(' HAL Control Panel - JavaScript Client Examples'.padStart(50));
    console.log('='.repeat(80));
    console.log();

    const client = new HALClient();

    // Example 1: Check panel I/O status
    console.log('1. Getting Panel I/O Status...');
    try {
        const ioStatus = await client.getPanelIO(1);
        console.log(`   Panel: ${ioStatus.panel_name}`);
        console.log(`   Inputs: ${ioStatus.inputs.length}`);
        console.log(`   Outputs: ${ioStatus.outputs.length}`);
        console.log(`   Relays: ${ioStatus.relays.length}`);
        console.log(`   Total events today: ${ioStatus.total_events_today}`);
        console.log();
    } catch (error) {
        console.log(`   Error: ${error.message}`);
        console.log();
    }

    // Example 2: Get reader health
    console.log('2. Getting Reader Health...');
    try {
        const health = await client.getReaderHealth(1);
        console.log(`   Reader: ${health.reader_name}`);
        console.log(`   Overall Health: ${health.overall_health}`);
        console.log(`   Health Score: ${health.health_score}/100`);
        console.log(`   Comm Health: ${health.comm_health}`);
        console.log(`   SC Health: ${health.sc_health}`);
        console.log();
    } catch (error) {
        console.log(`   Error: ${error.message}`);
        console.log();
    }

    // Example 3: Unlock door (momentary)
    console.log('3. Unlocking Door (5 seconds)...');
    try {
        const result = await client.unlockDoor(1, 5, 'Demo test');
        console.log(`   Success: ${result.success}`);
        console.log(`   Message: ${result.message}`);
        console.log();
    } catch (error) {
        console.log(`   Error: ${error.message}`);
        console.log();
    }

    // Example 4: List macros
    console.log('4. Available Control Macros...');
    try {
        const macros = await client.listMacros();
        for (const macro of macros.macros) {
            console.log(`   [${macro.macro_id}] ${macro.name}`);
            console.log(`       ${macro.description}`);
        }
        console.log();
    } catch (error) {
        console.log(`   Error: ${error.message}`);
        console.log();
    }

    // Example 5: WebSocket connection
    console.log('5. Connecting to WebSocket (real-time updates)...');
    try {
        const wsClient = new HALWebSocketClient();
        await wsClient.connect();
        console.log('   Listening for real-time events...');
        console.log('   (Press Ctrl+C to exit)');
        console.log();

        // Keep alive
        process.on('SIGINT', () => {
            console.log('\nDisconnecting...');
            wsClient.disconnect();
            process.exit(0);
        });
    } catch (error) {
        console.log(`   Error: ${error.message}`);
        console.log();
    }
}

// Run if executed directly
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { HALClient, HALWebSocketClient };
