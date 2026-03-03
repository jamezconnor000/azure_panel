"""
Azure Panel I/O Monitoring Module
Tracks inputs, outputs, and relay states on Azure BLU-IC2 panels
"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

# =============================================================================
# I/O Data Models
# =============================================================================

class IOType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    RELAY = "relay"

class IOState(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"
    FAULT = "fault"

class InputState(BaseModel):
    """Physical input state (door contacts, REX buttons, etc.)"""
    id: int
    panel_id: int
    name: str
    type: str  # DOOR_CONTACT, REX, TAMPER, AUX
    state: IOState
    last_change: datetime
    trigger_count_today: int
    supervised: bool
    resistance_ohms: Optional[float] = None  # For supervised inputs
    fault_reason: Optional[str] = None

class OutputState(BaseModel):
    """Physical output state (door strikes, LEDs, etc.)"""
    id: int
    panel_id: int
    name: str
    type: str  # STRIKE, LED, BUZZER, AUX
    state: IOState
    last_activated: Optional[datetime]
    activation_count_today: int
    mode: str  # MOMENTARY, LATCHED, TIMED
    duration_ms: Optional[int] = None
    controlled_by: Optional[str] = None  # What triggered it

class RelayState(BaseModel):
    """Relay module state"""
    id: int
    panel_id: int
    name: str
    state: IOState
    last_change: datetime
    activation_count_today: int
    mode: str  # NO, NC, PULSE
    pulse_duration_ms: Optional[int] = None
    linked_to: Optional[str] = None  # Door, elevator, etc.

class PanelIOStatus(BaseModel):
    """Complete I/O status for an Azure panel"""
    panel_id: int
    panel_name: str
    inputs: List[InputState]
    outputs: List[OutputState]
    relays: List[RelayState]
    last_update: datetime
    total_events_today: int

# =============================================================================
# Reader Health Models
# =============================================================================

class ReaderHealthMetric(str, Enum):
    EXCELLENT = "excellent"  # 100-90%
    GOOD = "good"            # 89-75%
    FAIR = "fair"            # 74-50%
    POOR = "poor"            # 49-25%
    CRITICAL = "critical"    # <25%

class ReaderHealth(BaseModel):
    """Comprehensive reader health assessment"""
    reader_id: int
    reader_name: str
    overall_health: ReaderHealthMetric
    health_score: int  # 0-100

    # Communication Health
    comm_health: ReaderHealthMetric
    comm_uptime_percent: float
    last_successful_comm: datetime
    failed_polls_last_hour: int
    avg_response_time_ms: float
    packet_loss_percent: float

    # Secure Channel Health
    sc_health: ReaderHealthMetric
    sc_handshake_success_rate: float
    sc_mac_failure_rate: float
    sc_cryptogram_failure_rate: float
    sc_avg_handshake_time_ms: float
    sc_rekeys_today: int

    # Hardware Health
    hardware_health: ReaderHealthMetric
    tamper_status: str  # OK, TAMPERED, UNKNOWN
    power_voltage: Optional[float]  # Volts
    power_status: str  # NORMAL, LOW, CRITICAL
    temperature_celsius: Optional[float]
    led_status: str  # FUNCTIONAL, FAILED, UNKNOWN
    beeper_status: str  # FUNCTIONAL, FAILED, UNKNOWN

    # Card Reader Health
    card_reader_health: ReaderHealthMetric
    successful_reads_today: int
    failed_reads_today: int
    read_success_rate: float
    avg_read_time_ms: float
    card_reader_errors: int

    # Firmware Info
    firmware_version: str
    firmware_up_to_date: bool
    last_firmware_update: Optional[datetime]
    pending_updates: int

    # Diagnostic Info
    recent_errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    last_health_check: datetime

class PanelHealth(BaseModel):
    """Azure panel health metrics"""
    panel_id: int
    panel_name: str
    overall_health: ReaderHealthMetric
    health_score: int  # 0-100

    # Panel Status
    online: bool
    uptime_hours: float
    last_reboot: datetime
    firmware_version: str

    # Power Metrics
    main_power: bool
    battery_voltage: Optional[float]
    battery_charge_percent: Optional[float]
    battery_health: ReaderHealthMetric

    # Network Health
    network_health: ReaderHealthMetric
    ip_address: Optional[str]
    network_uptime_percent: float
    avg_latency_ms: float

    # I/O Health
    inputs_ok: int
    inputs_fault: int
    outputs_ok: int
    outputs_fault: int
    relays_ok: int
    relays_fault: int

    # Database Health
    database_size_mb: float
    database_health: ReaderHealthMetric
    free_space_mb: float

    # Recent Issues
    errors_last_24h: int
    warnings_last_24h: int
    critical_alerts: List[str]

    last_health_check: datetime

# =============================================================================
# Mock Data Generators (Replace with actual HAL integration)
# =============================================================================

def get_panel_io_status(panel_id: int) -> PanelIOStatus:
    """Get current I/O state for a panel"""
    return PanelIOStatus(
        panel_id=panel_id,
        panel_name=f"Panel {panel_id}",
        inputs=[
            InputState(
                id=1,
                panel_id=panel_id,
                name="Main Door Contact",
                type="DOOR_CONTACT",
                state=IOState.INACTIVE,  # Door closed
                last_change=datetime.now(),
                trigger_count_today=156,
                supervised=True,
                resistance_ohms=2200.0
            ),
            InputState(
                id=2,
                panel_id=panel_id,
                name="REX Button",
                type="REX",
                state=IOState.INACTIVE,
                last_change=datetime.now(),
                trigger_count_today=43,
                supervised=False
            ),
            InputState(
                id=3,
                panel_id=panel_id,
                name="Tamper Switch",
                type="TAMPER",
                state=IOState.INACTIVE,  # No tamper
                last_change=datetime.now(),
                trigger_count_today=0,
                supervised=True,
                resistance_ohms=2200.0
            )
        ],
        outputs=[
            OutputState(
                id=1,
                panel_id=panel_id,
                name="Door Strike",
                type="STRIKE",
                state=IOState.INACTIVE,
                last_activated=datetime.now(),
                activation_count_today=156,
                mode="MOMENTARY",
                duration_ms=3000,
                controlled_by="Access Grant"
            ),
            OutputState(
                id=2,
                panel_id=panel_id,
                name="Reader LED",
                type="LED",
                state=IOState.ACTIVE,
                last_activated=datetime.now(),
                activation_count_today=1,
                mode="LATCHED",
                controlled_by="Reader Status"
            )
        ],
        relays=[
            RelayState(
                id=1,
                panel_id=panel_id,
                name="Elevator Relay",
                state=IOState.INACTIVE,
                last_change=datetime.now(),
                activation_count_today=23,
                mode="PULSE",
                pulse_duration_ms=2000,
                linked_to="Floor 2 Access"
            )
        ],
        last_update=datetime.now(),
        total_events_today=378
    )

def get_reader_health(reader_id: int) -> ReaderHealth:
    """Get comprehensive health metrics for a reader"""
    return ReaderHealth(
        reader_id=reader_id,
        reader_name=f"Reader {reader_id}",
        overall_health=ReaderHealthMetric.EXCELLENT,
        health_score=95,

        # Communication
        comm_health=ReaderHealthMetric.EXCELLENT,
        comm_uptime_percent=99.8,
        last_successful_comm=datetime.now(),
        failed_polls_last_hour=0,
        avg_response_time_ms=45.2,
        packet_loss_percent=0.1,

        # Secure Channel
        sc_health=ReaderHealthMetric.EXCELLENT,
        sc_handshake_success_rate=100.0,
        sc_mac_failure_rate=0.0,
        sc_cryptogram_failure_rate=0.0,
        sc_avg_handshake_time_ms=285.3,
        sc_rekeys_today=0,

        # Hardware
        hardware_health=ReaderHealthMetric.GOOD,
        tamper_status="OK",
        power_voltage=12.3,
        power_status="NORMAL",
        temperature_celsius=32.5,
        led_status="FUNCTIONAL",
        beeper_status="FUNCTIONAL",

        # Card Reader
        card_reader_health=ReaderHealthMetric.EXCELLENT,
        successful_reads_today=156,
        failed_reads_today=2,
        read_success_rate=98.7,
        avg_read_time_ms=125.4,
        card_reader_errors=0,

        # Firmware
        firmware_version="4.5.0",
        firmware_up_to_date=True,
        last_firmware_update=datetime(2025, 10, 15),
        pending_updates=0,

        # Diagnostics
        recent_errors=[],
        warnings=["Temperature slightly elevated (32.5°C)"],
        recommendations=["Monitor temperature trend", "Consider ventilation check in 30 days"],
        last_health_check=datetime.now()
    )

def get_panel_health(panel_id: int) -> PanelHealth:
    """Get comprehensive health metrics for an Azure panel"""
    return PanelHealth(
        panel_id=panel_id,
        panel_name=f"Azure Panel {panel_id}",
        overall_health=ReaderHealthMetric.EXCELLENT,
        health_score=96,

        # Status
        online=True,
        uptime_hours=168.5,  # 1 week
        last_reboot=datetime(2025, 11, 1, 10, 30),
        firmware_version="2.4.1",

        # Power
        main_power=True,
        battery_voltage=13.2,
        battery_charge_percent=95.0,
        battery_health=ReaderHealthMetric.EXCELLENT,

        # Network
        network_health=ReaderHealthMetric.EXCELLENT,
        ip_address="192.168.1.100",
        network_uptime_percent=99.9,
        avg_latency_ms=2.3,

        # I/O
        inputs_ok=3,
        inputs_fault=0,
        outputs_ok=2,
        outputs_fault=0,
        relays_ok=1,
        relays_fault=0,

        # Database
        database_size_mb=45.2,
        database_health=ReaderHealthMetric.GOOD,
        free_space_mb=2048.5,

        # Issues
        errors_last_24h=0,
        warnings_last_24h=1,
        critical_alerts=[],

        last_health_check=datetime.now()
    )
