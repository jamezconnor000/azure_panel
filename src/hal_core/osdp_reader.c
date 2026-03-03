/**
 * @file osdp_reader.c
 * @brief OSDP Reader Communication Implementation
 */

#include "osdp_reader.h"
#include "osdp_secure_channel.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <errno.h>
#include <time.h>
#include <sys/time.h>
#include <pthread.h>

// =============================================================================
// Event Queue Implementation
// =============================================================================

typedef struct {
    OSDP_Event_Type_t event_type;
    OSDP_Card_Data_t card_data;
    uint64_t timestamp;
} OSDP_QueuedEvent_t;

typedef struct {
    OSDP_QueuedEvent_t events[OSDP_QUEUE_SIZE];
    uint8_t head;           // Next read position
    uint8_t tail;           // Next write position
    uint8_t count;          // Number of events in queue
    pthread_mutex_t mutex;  // Thread safety
} OSDP_EventQueue_t;

static OSDP_EventQueue_t* EventQueue_Create(void) {
    OSDP_EventQueue_t* queue = (OSDP_EventQueue_t*)calloc(1, sizeof(OSDP_EventQueue_t));
    if (queue) {
        queue->head = 0;
        queue->tail = 0;
        queue->count = 0;
        pthread_mutex_init(&queue->mutex, NULL);
    }
    return queue;
}

static void EventQueue_Destroy(OSDP_EventQueue_t* queue) {
    if (queue) {
        pthread_mutex_destroy(&queue->mutex);
        free(queue);
    }
}

static bool EventQueue_Push(OSDP_EventQueue_t* queue, OSDP_Event_Type_t event_type,
                            const OSDP_Card_Data_t* card_data, uint64_t timestamp) {
    if (!queue) return false;

    pthread_mutex_lock(&queue->mutex);

    if (queue->count >= OSDP_QUEUE_SIZE) {
        // Queue full - drop oldest event
        queue->head = (queue->head + 1) % OSDP_QUEUE_SIZE;
        queue->count--;
    }

    OSDP_QueuedEvent_t* event = &queue->events[queue->tail];
    event->event_type = event_type;
    event->timestamp = timestamp;
    if (card_data) {
        memcpy(&event->card_data, card_data, sizeof(OSDP_Card_Data_t));
    } else {
        memset(&event->card_data, 0, sizeof(OSDP_Card_Data_t));
    }

    queue->tail = (queue->tail + 1) % OSDP_QUEUE_SIZE;
    queue->count++;

    pthread_mutex_unlock(&queue->mutex);
    return true;
}

static bool EventQueue_Pop(OSDP_EventQueue_t* queue, OSDP_Event_Type_t* event_type,
                           OSDP_Card_Data_t* card_data) {
    if (!queue || !event_type) return false;

    pthread_mutex_lock(&queue->mutex);

    if (queue->count == 0) {
        pthread_mutex_unlock(&queue->mutex);
        return false;
    }

    OSDP_QueuedEvent_t* event = &queue->events[queue->head];
    *event_type = event->event_type;
    if (card_data) {
        memcpy(card_data, &event->card_data, sizeof(OSDP_Card_Data_t));
    }

    queue->head = (queue->head + 1) % OSDP_QUEUE_SIZE;
    queue->count--;

    pthread_mutex_unlock(&queue->mutex);
    return true;
}

static bool EventQueue_HasEvents(OSDP_EventQueue_t* queue) {
    if (!queue) return false;

    pthread_mutex_lock(&queue->mutex);
    bool has_events = (queue->count > 0);
    pthread_mutex_unlock(&queue->mutex);

    return has_events;
}

static uint8_t EventQueue_Count(OSDP_EventQueue_t* queue) {
    if (!queue) return 0;

    pthread_mutex_lock(&queue->mutex);
    uint8_t count = queue->count;
    pthread_mutex_unlock(&queue->mutex);

    return count;
}

// =============================================================================
// Private Helper Functions
// =============================================================================

static uint64_t get_time_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

static int serial_open(const char* port, uint32_t baud_rate) {
    int fd = open(port, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0) {
        return -1;
    }

    struct termios options;
    tcgetattr(fd, &options);

    // Set baud rate
    speed_t speed;
    switch (baud_rate) {
        case 9600:   speed = B9600; break;
        case 19200:  speed = B19200; break;
        case 38400:  speed = B38400; break;
        case 115200: speed = B115200; break;
        default:     speed = B9600; break;
    }

    cfsetispeed(&options, speed);
    cfsetospeed(&options, speed);

    // 8N1, no flow control
    options.c_cflag &= ~PARENB;
    options.c_cflag &= ~CSTOPB;
    options.c_cflag &= ~CSIZE;
    options.c_cflag |= CS8;
    options.c_cflag &= ~CRTSCTS;
    options.c_cflag |= CREAD | CLOCAL;

    // Raw mode
    options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
    options.c_iflag &= ~(IXON | IXOFF | IXANY);
    options.c_oflag &= ~OPOST;

    // Timeouts
    options.c_cc[VMIN] = 0;
    options.c_cc[VTIME] = 1;

    tcsetattr(fd, TCSANOW, &options);
    tcflush(fd, TCIOFLUSH);

    return fd;
}

static void serial_close(int fd) {
    if (fd >= 0) {
        close(fd);
    }
}

static ssize_t serial_write(int fd, const uint8_t* data, size_t len) {
    return write(fd, data, len);
}

static ssize_t serial_read(int fd, uint8_t* buffer, size_t len, uint16_t timeout_ms) {
    size_t total = 0;
    uint64_t start = get_time_ms();

    while (total < len && (get_time_ms() - start) < timeout_ms) {
        ssize_t n = read(fd, buffer + total, len - total);
        if (n > 0) {
            total += n;
        } else if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
            return -1;
        }
        usleep(1000); // 1ms delay
    }

    return total;
}

// =============================================================================
// CRC-16 Calculation
// =============================================================================

uint16_t OSDP_CalcCRC16(const uint8_t* data, uint16_t len) {
    uint16_t crc = 0x1D0F;  // OSDP CRC-16 initial value

    for (uint16_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x0001) {
                crc = (crc >> 1) ^ 0x8005;
            } else {
                crc = crc >> 1;
            }
        }
    }

    return crc;
}

// =============================================================================
// OSDP Packet Building/Parsing
// =============================================================================

ErrorCode_t OSDP_BuildPacket(uint8_t addr, uint8_t sequence, uint8_t cmd,
                              const uint8_t* data, uint16_t data_len,
                              uint8_t* packet, uint16_t max_len, uint16_t* actual_len) {
    if (!packet || !actual_len) {
        return ErrorCode_BadParams;
    }

    uint16_t packet_len = 6 + data_len + 2; // SOM + ADDR + LEN(2) + CTRL + CMD + DATA + CRC(2)

    if (packet_len > max_len) {
        return ErrorCode_OutOfMemory;
    }

    // Build packet
    uint16_t idx = 0;
    packet[idx++] = OSDP_SOM;                    // Start of message
    packet[idx++] = addr & 0x7F;                 // Address (0-127)
    packet[idx++] = packet_len & 0xFF;           // Length LSB
    packet[idx++] = (packet_len >> 8) & 0xFF;    // Length MSB
    packet[idx++] = sequence & 0x03;             // Control (sequence number)
    packet[idx++] = cmd;                         // Command code

    // Copy data
    if (data && data_len > 0) {
        memcpy(&packet[idx], data, data_len);
        idx += data_len;
    }

    // Calculate CRC
    uint16_t crc = OSDP_CalcCRC16(packet, idx);
    packet[idx++] = crc & 0xFF;                  // CRC LSB
    packet[idx++] = (crc >> 8) & 0xFF;           // CRC MSB

    *actual_len = idx;
    return ErrorCode_OK;
}

ErrorCode_t OSDP_ParsePacket(const uint8_t* packet, uint16_t packet_len,
                              uint8_t* reply, uint8_t* data, uint16_t max_len, uint16_t* actual_len) {
    if (!packet || !reply || !actual_len) {
        return ErrorCode_BadParams;
    }

    if (packet_len < 8) { // Minimum: SOM + ADDR + LEN(2) + CTRL + REPLY + CRC(2)
        return ErrorCode_BadParams;
    }

    // Verify SOM
    if (packet[0] != OSDP_SOM) {
        return ErrorCode_Failed;
    }

    // Extract length
    uint16_t len = packet[2] | (packet[3] << 8);
    if (len != packet_len) {
        return ErrorCode_Failed;
    }

    // Verify CRC
    uint16_t crc_calc = OSDP_CalcCRC16(packet, packet_len - 2);
    uint16_t crc_recv = packet[packet_len - 2] | (packet[packet_len - 1] << 8);
    if (crc_calc != crc_recv) {
        return ErrorCode_Failed;
    }

    // Extract reply code
    *reply = packet[5];

    // Extract data
    uint16_t data_len = packet_len - 8; // Total - header - CRC
    if (data_len > 0) {
        if (data && max_len >= data_len) {
            memcpy(data, &packet[6], data_len);
            *actual_len = data_len;
        } else {
            return ErrorCode_OutOfMemory;
        }
    } else {
        *actual_len = 0;
    }

    return ErrorCode_OK;
}

// =============================================================================
// OSDP Reader Management
// =============================================================================

OSDP_Reader_t* OSDP_Reader_Create(LPA_t lpa, const OSDP_Config_t* config) {
    if (!config) {
        return NULL;
    }

    OSDP_Reader_t* reader = (OSDP_Reader_t*)calloc(1, sizeof(OSDP_Reader_t));
    if (!reader) {
        return NULL;
    }

    reader->lpa = lpa;
    reader->config = *config;
    reader->state = OSDP_STATE_INIT;
    reader->sequence = 0;
    reader->fd = -1;
    reader->event_queue = EventQueue_Create();  // Initialize event queue
    reader->sc_ctx = NULL;  // Secure channel context (initialized on demand)
    reader->packets_sent = 0;
    reader->packets_received = 0;
    reader->errors = 0;
    reader->last_poll_time = 0;

    // Initialize secure channel if enabled
    if (config->secure_channel) {
        SecureChannelContext_t* sc_ctx = (SecureChannelContext_t*)malloc(sizeof(SecureChannelContext_t));
        if (sc_ctx) {
            if (OSDP_SC_Init(sc_ctx, config->scbk) == ErrorCode_OK) {
                reader->sc_ctx = sc_ctx;
            } else {
                free(sc_ctx);
                free(reader);
                return NULL;
            }
        } else {
            free(reader);
            return NULL;
        }
    }

    return reader;
}

void OSDP_Reader_Destroy(OSDP_Reader_t* reader) {
    if (reader) {
        OSDP_Reader_Close(reader);

        // Free event queue
        if (reader->event_queue) {
            EventQueue_Destroy((OSDP_EventQueue_t*)reader->event_queue);
            reader->event_queue = NULL;
        }

        // Free secure channel context
        if (reader->sc_ctx) {
            SecureChannelContext_t* sc_ctx = (SecureChannelContext_t*)reader->sc_ctx;
            OSDP_SC_Reset(sc_ctx);
            free(sc_ctx);
            reader->sc_ctx = NULL;
        }

        free(reader);
    }
}

ErrorCode_t OSDP_Reader_Init(OSDP_Reader_t* reader, const char* port) {
    if (!reader || !port) {
        return ErrorCode_BadParams;
    }

    // Open serial port
    reader->fd = serial_open(port, reader->config.baud_rate);
    if (reader->fd < 0) {
        reader->state = OSDP_STATE_ERROR;
        return ErrorCode_Failed;
    }

    reader->state = OSDP_STATE_IDLE;
    return ErrorCode_OK;
}

ErrorCode_t OSDP_Reader_Close(OSDP_Reader_t* reader) {
    if (!reader) {
        return ErrorCode_BadParams;
    }

    if (reader->fd >= 0) {
        serial_close(reader->fd);
        reader->fd = -1;
    }

    reader->state = OSDP_STATE_OFFLINE;
    return ErrorCode_OK;
}

// =============================================================================
// OSDP Communication
// =============================================================================

ErrorCode_t OSDP_Reader_SendCommand(OSDP_Reader_t* reader, OSDP_Command_t cmd,
                                     const uint8_t* data, uint16_t data_len) {
    if (!reader || reader->fd < 0) {
        return ErrorCode_BadParams;
    }

    uint8_t packet[OSDP_MAX_PACKET_SIZE];
    uint16_t packet_len;

    ErrorCode_t err = OSDP_BuildPacket(reader->config.address, reader->sequence, cmd,
                                        data, data_len, packet, sizeof(packet), &packet_len);
    if (err != ErrorCode_OK) {
        return err;
    }

    // Send packet
    ssize_t sent = serial_write(reader->fd, packet, packet_len);
    if (sent != packet_len) {
        reader->errors++;
        return ErrorCode_Failed;
    }

    reader->packets_sent++;
    reader->sequence = (reader->sequence + 1) & 0x03;

    return ErrorCode_OK;
}

ErrorCode_t OSDP_Reader_ReceiveReply(OSDP_Reader_t* reader, OSDP_Reply_t* reply,
                                      uint8_t* data, uint16_t max_len, uint16_t* actual_len) {
    if (!reader || !reply || !actual_len || reader->fd < 0) {
        return ErrorCode_BadParams;
    }

    uint8_t packet[OSDP_MAX_PACKET_SIZE];

    // Read minimum header first (6 bytes)
    ssize_t n = serial_read(reader->fd, packet, 6, reader->config.timeout_ms);
    if (n < 6) {
        reader->errors++;
        return ErrorCode_Failed;
    }

    // Get packet length
    uint16_t packet_len = packet[2] | (packet[3] << 8);
    if (packet_len > OSDP_MAX_PACKET_SIZE || packet_len < 8) {
        reader->errors++;
        return ErrorCode_Failed;
    }

    // Read rest of packet
    n = serial_read(reader->fd, &packet[6], packet_len - 6, reader->config.timeout_ms);
    if (n != (packet_len - 6)) {
        reader->errors++;
        return ErrorCode_Failed;
    }

    // Parse packet
    uint8_t reply_code;
    ErrorCode_t err = OSDP_ParsePacket(packet, packet_len, &reply_code, data, max_len, actual_len);
    if (err != ErrorCode_OK) {
        reader->errors++;
        return err;
    }

    *reply = (OSDP_Reply_t)reply_code;
    reader->packets_received++;

    return ErrorCode_OK;
}

ErrorCode_t OSDP_Reader_Poll(OSDP_Reader_t* reader) {
    if (!reader) {
        return ErrorCode_BadParams;
    }

    ErrorCode_t err = OSDP_Reader_SendCommand(reader, OSDP_POLL, NULL, 0);
    if (err != ErrorCode_OK) {
        return err;
    }

    OSDP_Reply_t reply;
    uint8_t data[OSDP_MAX_PACKET_SIZE];
    uint16_t data_len;

    err = OSDP_Reader_ReceiveReply(reader, &reply, data, sizeof(data), &data_len);
    if (err != ErrorCode_OK) {
        reader->state = OSDP_STATE_ERROR;
        return err;
    }

    reader->last_poll_time = get_time_ms();

    switch (reply) {
        case OSDP_ACK:
            // No events pending
            if (reader->state != OSDP_STATE_SECURE) {
                reader->state = OSDP_STATE_ONLINE;
            }
            break;

        case OSDP_RAW:
        case OSDP_FMT:
            // Card read event - queue it
            if (data_len >= 4 && reader->event_queue) {
                OSDP_Card_Data_t card_data = {0};
                card_data.reader = data[0];
                card_data.format = data[1];
                card_data.bit_count = data[2] | (data[3] << 8);

                uint16_t byte_count = (card_data.bit_count + 7) / 8;
                if (byte_count > 64) byte_count = 64;
                if (data_len >= 4 + byte_count) {
                    memcpy(card_data.data, &data[4], byte_count);
                }

                OSDP_Reader_QueueEvent(reader, OSDP_EVENT_CARD_READ, &card_data);
            }
            if (reader->state != OSDP_STATE_SECURE) {
                reader->state = OSDP_STATE_ONLINE;
            }
            break;

        case OSDP_KEYPPAD:
            // Keypress event
            if (reader->event_queue) {
                OSDP_Reader_QueueEvent(reader, OSDP_EVENT_KEYPRESS, NULL);
            }
            break;

        case OSDP_NAK:
            reader->state = OSDP_STATE_ERROR;
            break;

        case OSDP_BUSY:
            // Reader is busy, try again later
            break;

        default:
            // Other replies - maintain state
            break;
    }

    return ErrorCode_OK;
}

// =============================================================================
// OSDP Device Information
// =============================================================================

ErrorCode_t OSDP_Reader_GetDeviceID(OSDP_Reader_t* reader, uint32_t* vendor_code,
                                     uint8_t* model, uint32_t* version, uint32_t* serial) {
    if (!reader || !vendor_code || !model || !version || !serial) {
        return ErrorCode_BadParams;
    }

    ErrorCode_t err = OSDP_Reader_SendCommand(reader, OSDP_ID, NULL, 0);
    if (err != ErrorCode_OK) {
        return err;
    }

    OSDP_Reply_t reply;
    uint8_t data[64];
    uint16_t data_len;

    err = OSDP_Reader_ReceiveReply(reader, &reply, data, sizeof(data), &data_len);
    if (err != ErrorCode_OK || reply != OSDP_PDID || data_len < 12) {
        return ErrorCode_Failed;
    }

    *vendor_code = data[0] | (data[1] << 8) | (data[2] << 16);
    *model = data[3];
    *version = data[4];
    *serial = data[5] | (data[6] << 8) | (data[7] << 16) | (data[8] << 24);

    return ErrorCode_OK;
}

ErrorCode_t OSDP_Reader_GetCapabilities(OSDP_Reader_t* reader, OSDP_PD_Capability_t* caps,
                                         uint8_t max_caps, uint8_t* actual_caps) {
    if (!reader || !caps || !actual_caps) {
        return ErrorCode_BadParams;
    }

    ErrorCode_t err = OSDP_Reader_SendCommand(reader, OSDP_CAP, NULL, 0);
    if (err != ErrorCode_OK) {
        return err;
    }

    OSDP_Reply_t reply;
    uint8_t data[256];
    uint16_t data_len;

    err = OSDP_Reader_ReceiveReply(reader, &reply, data, sizeof(data), &data_len);
    if (err != ErrorCode_OK || reply != OSDP_PDCAP) {
        return ErrorCode_Failed;
    }

    uint8_t count = data_len / 3;
    if (count > max_caps) {
        count = max_caps;
    }

    for (uint8_t i = 0; i < count; i++) {
        caps[i].function_code = data[i * 3];
        caps[i].compliance = data[i * 3 + 1];
        caps[i].num_items = data[i * 3 + 2];
    }

    *actual_caps = count;
    return ErrorCode_OK;
}

// =============================================================================
// OSDP LED Control
// =============================================================================

ErrorCode_t OSDP_Reader_SetLED(OSDP_Reader_t* reader, const OSDP_LED_Cmd_t* led_cmd) {
    if (!reader || !led_cmd) {
        return ErrorCode_BadParams;
    }

    uint8_t data[14];
    memcpy(data, led_cmd, sizeof(OSDP_LED_Cmd_t));

    return OSDP_Reader_SendCommand(reader, OSDP_LED, data, sizeof(OSDP_LED_Cmd_t));
}

ErrorCode_t OSDP_Reader_SetLED_Solid(OSDP_Reader_t* reader, uint8_t led_number, OSDP_LED_Color_t color) {
    OSDP_LED_Cmd_t cmd = {
        .reader = 0,
        .led_number = led_number,
        .temp_control = 0,
        .temp_on_time = 0,
        .temp_off_time = 0,
        .temp_color = 0,
        .perm_control = 1,  // Set permanent state
        .perm_on_time = 0,  // Solid
        .perm_off_time = 0,
        .perm_color = color
    };

    return OSDP_Reader_SetLED(reader, &cmd);
}

ErrorCode_t OSDP_Reader_SetLED_Blink(OSDP_Reader_t* reader, uint8_t led_number,
                                      OSDP_LED_Color_t color, uint8_t on_time, uint8_t off_time) {
    OSDP_LED_Cmd_t cmd = {
        .reader = 0,
        .led_number = led_number,
        .temp_control = 0,
        .temp_on_time = 0,
        .temp_off_time = 0,
        .temp_color = 0,
        .perm_control = 1,
        .perm_on_time = on_time,
        .perm_off_time = off_time,
        .perm_color = color
    };

    return OSDP_Reader_SetLED(reader, &cmd);
}

// =============================================================================
// OSDP Buzzer Control
// =============================================================================

ErrorCode_t OSDP_Reader_SetBuzzer(OSDP_Reader_t* reader, const OSDP_Buzzer_Cmd_t* buzzer_cmd) {
    if (!reader || !buzzer_cmd) {
        return ErrorCode_BadParams;
    }

    uint8_t data[5];
    memcpy(data, buzzer_cmd, sizeof(OSDP_Buzzer_Cmd_t));

    return OSDP_Reader_SendCommand(reader, OSDP_BUZ, data, sizeof(OSDP_Buzzer_Cmd_t));
}

ErrorCode_t OSDP_Reader_Beep(OSDP_Reader_t* reader, uint8_t duration) {
    OSDP_Buzzer_Cmd_t cmd = {
        .reader = 0,
        .tone_code = OSDP_BUZZER_ON,
        .on_time = duration,
        .off_time = 0,
        .count = 1
    };

    return OSDP_Reader_SetBuzzer(reader, &cmd);
}

// =============================================================================
// OSDP Output Control
// =============================================================================

ErrorCode_t OSDP_Reader_SetOutput(OSDP_Reader_t* reader, uint8_t output_number, bool state) {
    if (!reader) {
        return ErrorCode_BadParams;
    }

    uint8_t data[4] = {
        output_number,
        state ? 1 : 0,  // Control code
        0,              // Timer LSB
        0               // Timer MSB
    };

    return OSDP_Reader_SendCommand(reader, OSDP_OUT, data, 4);
}

ErrorCode_t OSDP_Reader_PulseOutput(OSDP_Reader_t* reader, uint8_t output_number, uint8_t duration) {
    if (!reader) {
        return ErrorCode_BadParams;
    }

    uint8_t data[4] = {
        output_number,
        2,              // Pulse control code
        duration,       // Timer LSB (100ms units)
        0               // Timer MSB
    };

    return OSDP_Reader_SendCommand(reader, OSDP_OUT, data, 4);
}

// =============================================================================
// OSDP Event Handling
// =============================================================================

bool OSDP_Reader_HasEvents(OSDP_Reader_t* reader) {
    if (!reader || !reader->event_queue) {
        return false;
    }
    return EventQueue_HasEvents((OSDP_EventQueue_t*)reader->event_queue);
}

ErrorCode_t OSDP_Reader_GetEvent(OSDP_Reader_t* reader, OSDP_Event_Type_t* event_type,
                                  OSDP_Card_Data_t* card_data) {
    if (!reader || !event_type) {
        return ErrorCode_BadParams;
    }

    if (!reader->event_queue) {
        return ErrorCode_InvalidState;
    }

    if (EventQueue_Pop((OSDP_EventQueue_t*)reader->event_queue, event_type, card_data)) {
        return ErrorCode_OK;
    }

    return ErrorCode_ObjectNotFound;
}

ErrorCode_t OSDP_Reader_QueueEvent(OSDP_Reader_t* reader, OSDP_Event_Type_t event_type,
                                    const OSDP_Card_Data_t* card_data) {
    if (!reader) {
        return ErrorCode_BadParams;
    }

    if (!reader->event_queue) {
        return ErrorCode_InvalidState;
    }

    if (EventQueue_Push((OSDP_EventQueue_t*)reader->event_queue, event_type, card_data, get_time_ms())) {
        return ErrorCode_OK;
    }

    return ErrorCode_Failed;
}

uint8_t OSDP_Reader_GetEventCount(OSDP_Reader_t* reader) {
    if (!reader || !reader->event_queue) {
        return 0;
    }
    return EventQueue_Count((OSDP_EventQueue_t*)reader->event_queue);
}

// =============================================================================
// OSDP Status
// =============================================================================

OSDP_State_t OSDP_Reader_GetState(OSDP_Reader_t* reader) {
    return reader ? reader->state : OSDP_STATE_OFFLINE;
}

ErrorCode_t OSDP_Reader_GetStats(OSDP_Reader_t* reader, uint32_t* packets_sent,
                                  uint32_t* packets_received, uint32_t* errors) {
    if (!reader || !packets_sent || !packets_received || !errors) {
        return ErrorCode_BadParams;
    }

    *packets_sent = reader->packets_sent;
    *packets_received = reader->packets_received;
    *errors = reader->errors;

    return ErrorCode_OK;
}

bool OSDP_Reader_IsOnline(OSDP_Reader_t* reader) {
    if (!reader) {
        return false;
    }

    return (reader->state == OSDP_STATE_ONLINE || reader->state == OSDP_STATE_SECURE);
}

// =============================================================================
// OSDP Secure Channel Integration
// =============================================================================

ErrorCode_t OSDP_Reader_EstablishSecureChannel(OSDP_Reader_t* reader) {
    if (!reader) {
        return ErrorCode_BadParams;
    }

    if (!reader->config.secure_channel) {
        return ErrorCode_NotEnabled;
    }

    if (!reader->sc_ctx) {
        return ErrorCode_InvalidState;
    }

    SecureChannelContext_t* sc_ctx = (SecureChannelContext_t*)reader->sc_ctx;

    // 1. Start handshake (generates CP random)
    ErrorCode_t result = OSDP_SC_StartHandshake(sc_ctx);
    if (result != ErrorCode_OK) {
        return result;
    }

    // 2. Send osdp_CHLNG command with CP random
    uint8_t chlng_data[8];
    memcpy(chlng_data, sc_ctx->cp_random, 8);
    result = OSDP_Reader_SendCommand(reader, OSDP_CHLNG, chlng_data, 8);
    if (result != ErrorCode_OK) {
        return result;
    }

    // 3. Receive osdp_CCRYPT reply with PD random and cryptogram
    OSDP_Reply_t reply;
    uint8_t reply_data[128];
    uint16_t reply_len;

    result = OSDP_Reader_ReceiveReply(reader, &reply, reply_data, 128, &reply_len);
    if (result != ErrorCode_OK || reply != OSDP_CCRYPT) {
        return ErrorCode_Failed;
    }

    // Reply contains: PD_Random (8 bytes) + PD_Cryptogram (16 bytes)
    if (reply_len < 24) {
        return ErrorCode_BadParams;
    }

    uint8_t pd_random[8];
    uint8_t pd_cryptogram[16];
    memcpy(pd_random, reply_data, 8);
    memcpy(pd_cryptogram, reply_data + 8, 16);

    // 4. Process and verify client cryptogram
    result = OSDP_SC_ProcessClientCryptogram(sc_ctx, pd_random, pd_cryptogram);
    if (result != ErrorCode_OK) {
        reader->errors++;
        return result;
    }

    // 5. Generate server cryptogram
    uint8_t server_cryptogram[16];
    result = OSDP_SC_GenerateServerCryptogram(sc_ctx, server_cryptogram);
    if (result != ErrorCode_OK) {
        return result;
    }

    // 6. Send osdp_SCRYPT command with server cryptogram
    result = OSDP_Reader_SendCommand(reader, OSDP_SCRYPT, server_cryptogram, 16);
    if (result != ErrorCode_OK) {
        return result;
    }

    // 7. Finalize secure channel
    result = OSDP_SC_Finalize(sc_ctx);
    if (result != ErrorCode_OK) {
        return result;
    }

    // 8. Update reader state
    reader->state = OSDP_STATE_SECURE;

    return ErrorCode_OK;
}

bool OSDP_Reader_IsSecureChannelActive(OSDP_Reader_t* reader) {
    if (!reader || !reader->sc_ctx) {
        return false;
    }

    SecureChannelContext_t* sc_ctx = (SecureChannelContext_t*)reader->sc_ctx;
    return OSDP_SC_IsEstablished(sc_ctx);
}

void OSDP_Reader_ResetSecureChannel(OSDP_Reader_t* reader) {
    if (!reader || !reader->sc_ctx) {
        return;
    }

    SecureChannelContext_t* sc_ctx = (SecureChannelContext_t*)reader->sc_ctx;
    OSDP_SC_Reset(sc_ctx);

    if (reader->state == OSDP_STATE_SECURE) {
        reader->state = OSDP_STATE_ONLINE;
    }
}
