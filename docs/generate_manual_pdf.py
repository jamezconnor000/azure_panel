#!/usr/bin/env python3
"""
Generate Aether Access Installation Manual PDF with Nordic Rune branding
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

# Aether color scheme
COLORS = {
    'bg_primary': HexColor('#0a0a12'),
    'bg_secondary': HexColor('#12121a'),
    'bg_card': HexColor('#16161e'),
    'accent_blue': HexColor('#4a9eff'),
    'accent_green': HexColor('#00ff88'),
    'accent_red': HexColor('#ff6b6b'),
    'accent_gold': HexColor('#ffd700'),
    'accent_purple': HexColor('#8b5cf6'),
    'text_primary': HexColor('#e0e0e0'),
    'text_secondary': HexColor('#888888'),
}

# Nordic runes
RUNES = "ᚨ ᛖ ᚦ ᛖ ᚱ"


class AetherPDFTemplate:
    """Custom PDF template with Aether branding"""

    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc
        self.width, self.height = letter

    def draw_header(self):
        """Draw branded header"""
        c = self.canvas

        # Header background
        c.setFillColor(COLORS['bg_secondary'])
        c.rect(0, self.height - 80, self.width, 80, fill=1, stroke=0)

        # Gold line
        c.setStrokeColor(COLORS['accent_gold'])
        c.setLineWidth(2)
        c.line(0, self.height - 80, self.width, self.height - 80)

        # Runes
        c.setFillColor(COLORS['accent_gold'])
        c.setFont("Helvetica", 14)
        c.drawString(50, self.height - 35, RUNES)

        # Title
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(140, self.height - 35, "AETHER ACCESS")

        # Subtitle
        c.setFillColor(COLORS['text_secondary'])
        c.setFont("Helvetica", 10)
        c.drawString(140, self.height - 52, "Azure Panel Installation Guide v2.0")

        # Version badge
        c.setFillColor(COLORS['accent_blue'])
        c.roundRect(self.width - 100, self.height - 50, 50, 20, 5, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(self.width - 75, self.height - 44, "v2.0.0")

    def draw_footer(self, page_num):
        """Draw branded footer"""
        c = self.canvas

        # Footer line
        c.setStrokeColor(COLORS['accent_blue'])
        c.setLineWidth(1)
        c.line(50, 50, self.width - 50, 50)

        # Page number
        c.setFillColor(COLORS['text_secondary'])
        c.setFont("Helvetica", 9)
        c.drawCentredString(self.width / 2, 35, f"Page {page_num}")

        # Footer text
        c.setFont("Helvetica", 8)
        c.drawString(50, 35, "Aether Access - Physical Access Control System")
        c.drawRightString(self.width - 50, 35, "Confidential")

    def on_first_page(self, canvas, doc):
        """First page template"""
        self.canvas = canvas
        canvas.saveState()
        self.draw_header()
        self.draw_footer(1)
        canvas.restoreState()

    def on_later_pages(self, canvas, doc):
        """Later pages template"""
        self.canvas = canvas
        canvas.saveState()
        self.draw_header()
        self.draw_footer(doc.page)
        canvas.restoreState()


def create_styles():
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='AetherTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=COLORS['accent_blue'],
        spaceAfter=20,
        spaceBefore=30,
    ))

    # Heading 1
    styles.add(ParagraphStyle(
        name='AetherH1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=COLORS['accent_gold'],
        spaceAfter=12,
        spaceBefore=20,
        leftIndent=0,
    ))

    # Heading 2
    styles.add(ParagraphStyle(
        name='AetherH2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=COLORS['accent_blue'],
        spaceAfter=8,
        spaceBefore=15,
    ))

    # Heading 3
    styles.add(ParagraphStyle(
        name='AetherH3',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=COLORS['accent_purple'],
        spaceAfter=6,
        spaceBefore=12,
    ))

    # Body text
    styles.add(ParagraphStyle(
        name='AetherBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=black,
        spaceAfter=8,
        leading=14,
    ))

    # Code style
    styles.add(ParagraphStyle(
        name='AetherCode',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        textColor=COLORS['accent_green'],
        backColor=HexColor('#f5f5f5'),
        leftIndent=20,
        rightIndent=20,
        spaceAfter=8,
        spaceBefore=8,
        borderPadding=8,
    ))

    # Note style
    styles.add(ParagraphStyle(
        name='AetherNote',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLORS['text_secondary'],
        leftIndent=20,
        spaceAfter=8,
        fontName='Helvetica-Oblique',
    ))

    # Warning style
    styles.add(ParagraphStyle(
        name='AetherWarning',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLORS['accent_red'],
        leftIndent=20,
        spaceAfter=8,
        fontName='Helvetica-Bold',
    ))

    return styles


def build_document(output_path):
    """Build the PDF document"""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=100,
        bottomMargin=70,
    )

    styles = create_styles()
    story = []

    # ========== COVER CONTENT ==========
    story.append(Spacer(1, 100))
    story.append(Paragraph(f"<font color='#ffd700' size='20'>{RUNES}</font>", styles['AetherTitle']))
    story.append(Paragraph("AETHER ACCESS", styles['AetherTitle']))
    story.append(Paragraph("Installation & Configuration Guide", styles['AetherH2']))
    story.append(Spacer(1, 30))
    story.append(Paragraph("Azure Panel Physical Access Control System", styles['AetherBody']))
    story.append(Paragraph("Version 2.0.0 | Ambient.ai Integration", styles['AetherNote']))
    story.append(PageBreak())

    # ========== TABLE OF CONTENTS ==========
    story.append(Paragraph("ᚱ Table of Contents", styles['AetherH1']))

    toc_data = [
        ["1.", "System Overview", "3"],
        ["2.", "System Requirements", "4"],
        ["3.", "Quick Start Installation", "5"],
        ["4.", "Directory Structure", "6"],
        ["5.", "Configuration", "7"],
        ["6.", "Service Management", "8"],
        ["7.", "API Endpoints Reference", "9"],
        ["8.", "Ambient.ai Integration", "11"],
        ["9.", "Troubleshooting", "13"],
        ["10.", "Security Checklist", "14"],
    ]

    toc_table = Table(toc_data, colWidths=[0.4*inch, 4*inch, 0.5*inch])
    toc_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # ========== SECTION 1: OVERVIEW ==========
    story.append(Paragraph("ᛊ 1. System Overview", styles['AetherH1']))
    story.append(Paragraph(
        "Aether Access is a complete Physical Access Control System (PACS) designed for "
        "Azure BLU-IC2 Controllers. It provides a modern REST API, real-time WebSocket updates, "
        "local card database management, and integration with Ambient.ai for intelligent video monitoring.",
        styles['AetherBody']
    ))

    story.append(Paragraph("Key Features", styles['AetherH2']))
    features = [
        "Event-driven architecture with 100K event buffer",
        "Local SQLite card database with 1M+ capacity",
        "REST API server (FastAPI) on port 8080",
        "Real-time WebSocket event streaming",
        "Ambient.ai event ingestion integration",
        "OSDP/Wiegand/DESFire protocol support",
        "Offline operation capability",
        "Standard PACS alarm types",
    ]
    for f in features:
        story.append(Paragraph(f"• {f}", styles['AetherBody']))

    story.append(PageBreak())

    # ========== SECTION 2: REQUIREMENTS ==========
    story.append(Paragraph("ᛈ 2. System Requirements", styles['AetherH1']))

    story.append(Paragraph("Hardware", styles['AetherH2']))
    hw_data = [
        ["Component", "Requirement"],
        ["Controller", "Azure BLU-IC2 (ARM64)"],
        ["RAM", "Minimum 512MB"],
        ["Storage", "Minimum 500MB free"],
        ["Network", "Ethernet connectivity"],
    ]
    hw_table = Table(hw_data, colWidths=[2*inch, 3*inch])
    hw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_blue']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(hw_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Software", styles['AetherH2']))
    sw_data = [
        ["Component", "Requirement"],
        ["Operating System", "Linux (Debian/Ubuntu, Alpine, RHEL)"],
        ["Python", "3.9 or higher"],
        ["Database", "SQLite 3.x"],
        ["Service Manager", "systemd"],
    ]
    sw_table = Table(sw_data, colWidths=[2*inch, 3*inch])
    sw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_blue']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sw_table)
    story.append(PageBreak())

    # ========== SECTION 3: QUICK START ==========
    story.append(Paragraph("ᚷ 3. Quick Start Installation", styles['AetherH1']))

    story.append(Paragraph("Step 1: Transfer Package", styles['AetherH2']))
    story.append(Paragraph("Transfer the deployment package to your Azure Panel:", styles['AetherBody']))
    story.append(Paragraph("scp aether-access-2.0.0.tar.gz root@panel-ip:/tmp/", styles['AetherCode']))

    story.append(Paragraph("Step 2: Extract Package", styles['AetherH2']))
    story.append(Paragraph("cd /tmp && tar -xzf aether-access-2.0.0.tar.gz", styles['AetherCode']))

    story.append(Paragraph("Step 3: Run Installation", styles['AetherH2']))
    story.append(Paragraph("cd aether-access-2.0.0 && sudo ./scripts/install.sh", styles['AetherCode']))
    story.append(Paragraph("For automated installation:", styles['AetherNote']))
    story.append(Paragraph("sudo ./scripts/install.sh --unattended", styles['AetherCode']))

    story.append(Paragraph("Step 4: Verify Installation", styles['AetherH2']))
    story.append(Paragraph("curl http://localhost:8080/health", styles['AetherCode']))
    story.append(Paragraph("Expected response:", styles['AetherNote']))
    story.append(Paragraph('{ "status": "healthy", "version": "2.0.0", "hal": { "status": "healthy" } }', styles['AetherCode']))

    story.append(Paragraph("Installation Options", styles['AetherH2']))
    opts_data = [
        ["Option", "Description"],
        ["--unattended", "Run without prompts (use defaults)"],
        ["--dev", "Install in development mode"],
        ["--no-service", "Don't install systemd services"],
        ["--data-dir DIR", "Custom data directory"],
        ["--port PORT", "API server port (default: 8080)"],
    ]
    opts_table = Table(opts_data, colWidths=[1.5*inch, 3.5*inch])
    opts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_blue']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(opts_table)
    story.append(PageBreak())

    # ========== SECTION 4: DIRECTORY STRUCTURE ==========
    story.append(Paragraph("ᛁ 4. Directory Structure", styles['AetherH1']))

    dirs = [
        ("/opt/aether-access/", "Application files"),
        ("  api/", "API server modules"),
        ("  python/", "HAL Python bindings"),
        ("  venv/", "Python virtual environment"),
        ("  lib/", "HAL C libraries (if available)"),
        ("/etc/aether/", "Configuration"),
        ("  aether.conf", "Main configuration"),
        ("  aether.env", "Environment variables"),
        ("  ambient.env", "Ambient.ai configuration"),
        ("/var/lib/aether/", "Data"),
        ("  hal_database.db", "Main database"),
        ("  backups/", "Database backups"),
        ("/var/log/aether/", "Logs"),
        ("  aether.log", "Application log"),
        ("  ambient_export.log", "Export daemon log"),
    ]

    for path, desc in dirs:
        indent = "    " if path.startswith("  ") else ""
        path_clean = path.strip()
        story.append(Paragraph(f"<font face='Courier' color='#4a9eff'>{indent}{path_clean}</font>  {desc}", styles['AetherBody']))

    story.append(PageBreak())

    # ========== SECTION 5: CONFIGURATION ==========
    story.append(Paragraph("ᚠ 5. Configuration", styles['AetherH1']))

    story.append(Paragraph("Main Configuration (/etc/aether/aether.conf)", styles['AetherH2']))
    story.append(Paragraph(
        "The main configuration file controls server settings, database paths, and security options.",
        styles['AetherBody']
    ))

    config_example = """[security]
secret_key = your-unique-secret-key
allowed_origins = https://your-frontend-domain.com

[server]
port = 8080
workers = 2

[database]
path = /var/lib/aether/hal_database.db"""

    for line in config_example.split('\n'):
        story.append(Paragraph(line, styles['AetherCode']))

    story.append(Paragraph("Environment Variables (/etc/aether/aether.env)", styles['AetherH2']))
    env_vars = [
        ["Variable", "Default", "Description"],
        ["API_PORT", "8080", "API server port"],
        ["HAL_DATABASE_PATH", "/var/lib/aether/hal_database.db", "Database location"],
        ["HAL_LOG_LEVEL", "INFO", "Logging level"],
        ["HAL_MODE", "auto", "HAL mode (auto/native/simulation)"],
    ]
    env_table = Table(env_vars, colWidths=[1.5*inch, 2*inch, 2*inch])
    env_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_blue']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(env_table)
    story.append(PageBreak())

    # ========== SECTION 6: SERVICE MANAGEMENT ==========
    story.append(Paragraph("ᛒ 6. Service Management", styles['AetherH1']))

    story.append(Paragraph("Using systemctl", styles['AetherH2']))
    cmds = [
        ("Start service", "sudo systemctl start aether-access"),
        ("Stop service", "sudo systemctl stop aether-access"),
        ("Restart service", "sudo systemctl restart aether-access"),
        ("View status", "sudo systemctl status aether-access"),
        ("Enable auto-start", "sudo systemctl enable aether-access"),
        ("View logs", "sudo journalctl -u aether-access -f"),
    ]
    for desc, cmd in cmds:
        story.append(Paragraph(f"<b>{desc}:</b>", styles['AetherBody']))
        story.append(Paragraph(cmd, styles['AetherCode']))

    story.append(PageBreak())

    # ========== SECTION 7: API ENDPOINTS ==========
    story.append(Paragraph("ᚱ 7. API Endpoints Reference", styles['AetherH1']))

    story.append(Paragraph("Core Endpoints", styles['AetherH2']))
    core_endpoints = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/", "API root (HTML info page)"],
        ["GET", "/health", "Health check"],
        ["GET", "/docs", "Swagger UI documentation"],
        ["GET", "/redoc", "ReDoc documentation"],
    ]
    core_table = Table(core_endpoints, colWidths=[0.7*inch, 2*inch, 2.5*inch])
    core_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_blue']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(core_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("HAL Core (/hal/*)", styles['AetherH2']))
    hal_endpoints = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/hal/health", "HAL system health"],
        ["GET", "/hal/stats", "HAL statistics"],
        ["GET/POST", "/hal/cards", "Card management"],
        ["GET/PUT/DELETE", "/hal/cards/{number}", "Single card operations"],
        ["GET/POST", "/hal/doors", "Door management"],
        ["GET/POST", "/hal/access-levels", "Access level management"],
        ["GET", "/hal/events", "Event buffer"],
        ["POST", "/hal/access/check", "Check access decision"],
        ["POST", "/hal/simulate/card-read", "Simulate card read"],
    ]
    hal_table = Table(hal_endpoints, colWidths=[1*inch, 2*inch, 2.2*inch])
    hal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_gold']),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(hal_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Frontend API (/api/v1/*)", styles['AetherH2']))
    v1_endpoints = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/api/v1/dashboard", "Dashboard data"],
        ["GET", "/api/v1/panels/{id}/io", "Panel I/O status"],
        ["POST", "/api/v1/doors/{id}/unlock", "Unlock door"],
        ["POST", "/api/v1/doors/{id}/lock", "Lock door"],
        ["POST", "/api/v1/control/lockdown", "Emergency lockdown"],
    ]
    v1_table = Table(v1_endpoints, colWidths=[0.8*inch, 2.2*inch, 2.2*inch])
    v1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_purple']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(v1_table)

    story.append(Paragraph("WebSocket", styles['AetherH2']))
    story.append(Paragraph("ws://panel-ip:8080/ws/live", styles['AetherCode']))
    story.append(Paragraph("Subscribe to real-time events: Card reads, Door events, System alerts, Heartbeat", styles['AetherNote']))
    story.append(PageBreak())

    # ========== SECTION 8: AMBIENT.AI ==========
    story.append(Paragraph("ᚾ 8. Ambient.ai Integration", styles['AetherH1']))

    story.append(Paragraph(
        "Aether Access supports real-time event export to Ambient.ai for intelligent video monitoring integration.",
        styles['AetherBody']
    ))

    story.append(Paragraph("Configuration", styles['AetherH2']))
    story.append(Paragraph("1. Create configuration file:", styles['AetherBody']))
    story.append(Paragraph("sudo cp /etc/aether/ambient.env.template /etc/aether/ambient.env", styles['AetherCode']))

    story.append(Paragraph("2. Add your API key:", styles['AetherBody']))
    story.append(Paragraph("AMBIENT_API_KEY=your-api-key-from-ambient-ai", styles['AetherCode']))

    story.append(Paragraph("3. Enable and start the export daemon:", styles['AetherBody']))
    story.append(Paragraph("sudo systemctl enable aether-ambient-export", styles['AetherCode']))
    story.append(Paragraph("sudo systemctl start aether-ambient-export", styles['AetherCode']))

    story.append(Paragraph("Ambient.ai API Endpoints", styles['AetherH2']))
    ambient_endpoints = [
        ["Endpoint", "Description"],
        ["/hal/ambient/source-system", "Get source system UUID"],
        ["/hal/ambient/devices", "Get all devices for sync"],
        ["/hal/ambient/persons", "Get all persons for sync"],
        ["/hal/ambient/access-items", "Get all cards/credentials"],
        ["/hal/ambient/alarms", "Get alarm definitions"],
        ["/hal/ambient/export-queue", "View export queue status"],
    ]
    ambient_table = Table(ambient_endpoints, colWidths=[2.5*inch, 2.8*inch])
    ambient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_green']),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ambient_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Supported PACS Event Types", styles['AetherH2']))
    events_data = [
        ["Event Type", "Is Alarm", "Description"],
        ["Access Granted", "No", "Card read, access allowed"],
        ["Access Denied", "Yes", "Card read, access denied"],
        ["Door Forced Open", "Yes", "Door opened without credential"],
        ["Door Held Open", "Yes", "Door left open past timer"],
        ["Invalid Badge", "Yes", "Unknown card presented"],
        ["Expired Badge", "Yes", "Expired card presented"],
        ["Tamper Alarm", "Yes", "Device tamper detected"],
        ["Communication Failure", "Yes", "Reader/panel communication lost"],
        ["Anti-Passback Violation", "Yes", "APB rule violated"],
        ["Duress Alarm", "Yes", "Duress code entered"],
        ["Emergency Lockdown", "Yes", "System locked down"],
    ]
    events_table = Table(events_data, colWidths=[1.8*inch, 0.8*inch, 2.6*inch])
    events_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_red']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['text_secondary']),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('TEXTCOLOR', (1, 1), (1, 1), COLORS['accent_green']),
        ('TEXTCOLOR', (1, 2), (1, -1), COLORS['accent_red']),
    ]))
    story.append(events_table)
    story.append(PageBreak())

    # ========== SECTION 9: TROUBLESHOOTING ==========
    story.append(Paragraph("ᛉ 9. Troubleshooting", styles['AetherH1']))

    story.append(Paragraph("Service Won't Start", styles['AetherH2']))
    story.append(Paragraph("1. Check logs:", styles['AetherBody']))
    story.append(Paragraph("sudo journalctl -u aether-access -n 50 --no-pager", styles['AetherCode']))
    story.append(Paragraph("2. Check port availability:", styles['AetherBody']))
    story.append(Paragraph("sudo lsof -i :8080", styles['AetherCode']))
    story.append(Paragraph("3. Verify permissions:", styles['AetherBody']))
    story.append(Paragraph("ls -la /var/lib/aether/", styles['AetherCode']))

    story.append(Paragraph("Database Errors", styles['AetherH2']))
    story.append(Paragraph("1. Check database file:", styles['AetherBody']))
    story.append(Paragraph('sqlite3 /var/lib/aether/hal_database.db ".tables"', styles['AetherCode']))
    story.append(Paragraph("2. Reset database (if needed):", styles['AetherBody']))
    story.append(Paragraph("sudo systemctl stop aether-access", styles['AetherCode']))
    story.append(Paragraph("sudo rm /var/lib/aether/hal_database.db", styles['AetherCode']))
    story.append(Paragraph("sudo systemctl start aether-access", styles['AetherCode']))

    story.append(Paragraph("Permission Issues", styles['AetherH2']))
    story.append(Paragraph("sudo chown -R aether:aether /var/lib/aether", styles['AetherCode']))
    story.append(Paragraph("sudo chown -R aether:aether /var/log/aether", styles['AetherCode']))
    story.append(PageBreak())

    # ========== SECTION 10: SECURITY ==========
    story.append(Paragraph("ᛊ 10. Security Checklist", styles['AetherH1']))

    story.append(Paragraph("Production Deployment Checklist", styles['AetherH2']))
    checklist = [
        "Change default secret_key in configuration",
        "Restrict allowed_origins to your frontend domain",
        "Enable HTTPS (use reverse proxy like nginx)",
        "Configure firewall rules",
        "Set up log rotation",
        "Enable database backups",
        "Review user permissions",
        "Disable debug mode",
    ]
    for item in checklist:
        story.append(Paragraph(f"☐ {item}", styles['AetherBody']))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Firewall Rules", styles['AetherH2']))
    story.append(Paragraph("Allow API port:", styles['AetherBody']))
    story.append(Paragraph("sudo ufw allow 8080/tcp", styles['AetherCode']))

    story.append(Spacer(1, 20))
    story.append(Paragraph("HTTPS with nginx", styles['AetherH2']))
    nginx_config = """server {
    listen 443 ssl;
    server_name panel.example.com;

    ssl_certificate /etc/ssl/certs/panel.crt;
    ssl_certificate_key /etc/ssl/private/panel.key;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}"""
    for line in nginx_config.split('\n'):
        story.append(Paragraph(line.replace(' ', '&nbsp;'), styles['AetherCode']))

    story.append(PageBreak())

    # ========== FINAL PAGE ==========
    story.append(Spacer(1, 150))
    story.append(Paragraph(f"<font color='#ffd700' size='24'>{RUNES}</font>", ParagraphStyle('Center', alignment=TA_CENTER)))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<font color='#4a9eff' size='16'>AETHER ACCESS</font>", ParagraphStyle('Center', alignment=TA_CENTER)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>\"The machines answer to US.\"</i>", ParagraphStyle('Center', alignment=TA_CENTER, textColor=COLORS['text_secondary'])))
    story.append(Spacer(1, 30))
    story.append(Paragraph("Physical Access Control System", ParagraphStyle('Center', alignment=TA_CENTER)))
    story.append(Paragraph("Version 2.0.0", ParagraphStyle('Center', alignment=TA_CENTER, textColor=COLORS['text_secondary'])))

    # Build PDF
    template = AetherPDFTemplate(None, doc)
    doc.build(
        story,
        onFirstPage=template.on_first_page,
        onLaterPages=template.on_later_pages
    )

    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "Aether_Access_Installation_Guide_v2.0.pdf")
    build_document(output_path)
