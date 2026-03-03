#include "reader.h"
#include "../../hal_core/osdp_reader.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>

// Simple in-memory storage
#define MAX_READERS 100
#define MAX_LED_CONFIGS 50
#define MAX_BUZZER_CONFIGS 50
#define MAX_READER_INDICATIONS 50

static Reader_t* g_readers[MAX_READERS];
static int g_reader_count = 0;

static LEDConfig_t* g_led_configs[MAX_LED_CONFIGS];
static int g_led_config_count = 0;

static BuzzerConfig_t* g_buzzer_configs[MAX_BUZZER_CONFIGS];
static int g_buzzer_config_count = 0;

static ReaderIndication_t* g_indications[MAX_READER_INDICATIONS];
static int g_indication_count = 0;

// =============================================================================
// LED Config Implementation
// =============================================================================

LEDConfig_t* LEDConfig_Create(LPA_t id) {
    LEDConfig_t* config = (LEDConfig_t*)malloc(sizeof(LEDConfig_t));
    if (config) {
        memset(config, 0, sizeof(LEDConfig_t));
        config->Id = id;
        config->LEDId = LEDId_Green;
        config->CancelTemp = 0;
        config->OnTime = 10;  // 1 second
        config->OffTime = 0;  // Solid
        config->OnColor = LEDColor_Green;
        config->OffColor = LEDColor_Off;
    }
    return config;
}

void LEDConfig_Destroy(LEDConfig_t* config) {
    if (config) {
        free(config);
    }
}

// =============================================================================
// Buzzer Config Implementation
// =============================================================================

BuzzerConfig_t* BuzzerConfig_Create(LPA_t id) {
    BuzzerConfig_t* config = (BuzzerConfig_t*)malloc(sizeof(BuzzerConfig_t));
    if (config) {
        memset(config, 0, sizeof(BuzzerConfig_t));
        config->Id = id;
        config->Tone = 2;  // Default tone
        config->OnTime = 2;  // 200ms
        config->OffTime = 0;
        config->Count = 1;  // Single beep
    }
    return config;
}

void BuzzerConfig_Destroy(BuzzerConfig_t* config) {
    if (config) {
        free(config);
    }
}

// =============================================================================
// Reader Indication Implementation
// =============================================================================

ReaderIndication_t* ReaderIndication_Create(LPA_t id) {
    ReaderIndication_t* indication = (ReaderIndication_t*)malloc(sizeof(ReaderIndication_t));
    if (indication) {
        memset(indication, 0, sizeof(ReaderIndication_t));
        indication->Id = id;
        indication->ConfigCount = 0;

        // Initialize all states
        for (int i = 0; i < 25; i++) {
            indication->States[i].State = (ReaderIndicationState_t)i;
            for (int j = 0; j < MAX_INDICATION_CONFIGS; j++) {
                indication->States[i].Configs[j] = c_lpaNULL;
            }
        }
    }
    return indication;
}

void ReaderIndication_Destroy(ReaderIndication_t* indication) {
    if (indication) {
        free(indication);
    }
}

void ReaderIndication_SetState(ReaderIndication_t* indication, ReaderIndicationState_t state,
                                LPA_t* configs, int count) {
    if (!indication || state >= 25 || count > MAX_INDICATION_CONFIGS) return;

    IndicationConfig_t* config = &indication->States[state];
    config->State = state;

    for (int i = 0; i < count && i < MAX_INDICATION_CONFIGS; i++) {
        config->Configs[i] = configs[i];
    }

    // Clear remaining slots
    for (int i = count; i < MAX_INDICATION_CONFIGS; i++) {
        config->Configs[i] = c_lpaNULL;
    }
}

IndicationConfig_t* ReaderIndication_GetState(ReaderIndication_t* indication,
                                                ReaderIndicationState_t state) {
    if (!indication || state >= 25) return NULL;
    return &indication->States[state];
}

// =============================================================================
// Reader Structure Implementation
// =============================================================================

Reader_t* Reader_Create(LPA_t id) {
    Reader_t* reader = (Reader_t*)malloc(sizeof(Reader_t));
    if (reader) {
        memset(reader, 0, sizeof(Reader_t));
        reader->Id = id;
        reader->AccessPoint = c_lpaNULL;
        reader->CipherCode = 0xFFFFFFFF;
        reader->ScriptId = 0;
        reader->Flags = ReaderFlags_None;
        reader->TimedAPB = 0;
        reader->TimedAPBEx = 0;
        reader->ThreatLevel = 0;
        reader->NextTO = 0;
        reader->SignalType = 0;
        reader->Direction = 0;
        reader->NumOfCards = 1;
        reader->InitMode = ReaderMode_CardOnly;
        reader->OfflineMode = ReaderMode_CardOnly;
        reader->UseLimit = 0;
        reader->CardFormatListId = 0;
        reader->CtrlTimeZone = 0;
        reader->SmartCardFormat = c_lpaNULL;
        reader->TZStartMode = ReaderMode_Unknown;
        reader->TZEndMode = ReaderMode_Unknown;
        reader->DiddleThreshold = 3;
        reader->Indication = c_lpaNULL;
        reader->UnlockedMode = ReaderMode_Unlocked;
        reader->LockedMode = ReaderMode_Locked;
        reader->LockTimeout = 0;
        reader->DisableReaderToggle = c_lpaNULL;
        reader->CommandTO = 3000;  // 3 seconds
        reader->DiddleLockoutTO = 2;
        reader->PINTimeout = 10;
        reader->CurrentMode = ReaderMode_CardOnly;
        reader->LastActivity = time(NULL);
    }
    return reader;
}

void Reader_Destroy(Reader_t* reader) {
    if (reader) {
        free(reader);
    }
}

// =============================================================================
// Internal Helper Functions
// =============================================================================

static int FindReaderIndex(LPA_t id) {
    for (int i = 0; i < g_reader_count; i++) {
        if (g_readers[i] && LPA_Equals(&g_readers[i]->Id, &id)) {
            return i;
        }
    }
    return -1;
}

// =============================================================================
// Reader Management Functions
// =============================================================================

ErrorCode_t Reader_Add(Reader_t* reader) {
    if (!reader) return ErrorCode_BadParams;
    if (g_reader_count >= MAX_READERS) return ErrorCode_OutOfMemory;

    // Check if already exists
    if (FindReaderIndex(reader->Id) >= 0) {
        return ErrorCode_AlreadyExists;
    }

    g_readers[g_reader_count++] = reader;
    return ErrorCode_OK;
}

Reader_t* Reader_Get(LPA_t id) {
    int index = FindReaderIndex(id);
    if (index >= 0) {
        return g_readers[index];
    }
    return NULL;
}

ErrorCode_t Reader_Update(Reader_t* reader) {
    if (!reader) return ErrorCode_BadParams;

    int index = FindReaderIndex(reader->Id);
    if (index < 0) return ErrorCode_ObjectNotFound;

    // Keep runtime state
    ReaderMode_t current_mode = g_readers[index]->CurrentMode;
    time_t last_activity = g_readers[index]->LastActivity;

    // Replace reader
    Reader_Destroy(g_readers[index]);
    g_readers[index] = reader;

    // Restore state
    reader->CurrentMode = current_mode;
    reader->LastActivity = last_activity;

    return ErrorCode_OK;
}

ErrorCode_t Reader_Delete(LPA_t id) {
    int index = FindReaderIndex(id);
    if (index < 0) return ErrorCode_ObjectNotFound;

    Reader_Destroy(g_readers[index]);

    // Shift remaining readers
    for (int i = index; i < g_reader_count - 1; i++) {
        g_readers[i] = g_readers[i + 1];
    }
    g_reader_count--;

    return ErrorCode_OK;
}

// =============================================================================
// Reader Control Functions
// =============================================================================

ErrorCode_t Reader_SetMode(LPA_t id, ReaderMode_t mode) {
    Reader_t* reader = Reader_Get(id);
    if (!reader) return ErrorCode_ObjectNotFound;

    reader->CurrentMode = mode;
    reader->LastActivity = time(NULL);

    printf("READER [%d:%d]: Mode set to %d\n", id.type, id.id, mode);
    return ErrorCode_OK;
}

ReaderMode_t Reader_GetMode(LPA_t id) {
    Reader_t* reader = Reader_Get(id);
    if (reader) {
        return reader->CurrentMode;
    }
    return ReaderMode_Unknown;
}

ErrorCode_t Reader_Lock(LPA_t id) {
    return Reader_SetMode(id, ReaderMode_Locked);
}

ErrorCode_t Reader_Unlock(LPA_t id) {
    return Reader_SetMode(id, ReaderMode_Unlocked);
}

ErrorCode_t Reader_SetCardOnly(LPA_t id) {
    return Reader_SetMode(id, ReaderMode_CardOnly);
}

ErrorCode_t Reader_SetCardAndPIN(LPA_t id) {
    return Reader_SetMode(id, ReaderMode_CardAndPin);
}

// =============================================================================
// Reader Indication Functions
// =============================================================================

ErrorCode_t Reader_SetIndicationState(LPA_t reader_id, ReaderIndicationState_t state) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader) return ErrorCode_ObjectNotFound;

    printf("READER [%d:%d]: Indication state -> %d", reader_id.type, reader_id.id, state);

    // Map common states to user-friendly output
    switch (state) {
        case ReaderIndicationState_Grant:
            printf(" (ACCESS GRANTED - Green LED, 2 beeps)\n");
            break;
        case ReaderIndicationState_Deny:
            printf(" (ACCESS DENIED - Red LED, 3 beeps)\n");
            break;
        case ReaderIndicationState_Unlocked:
            printf(" (UNLOCKED - Green LED solid)\n");
            break;
        case ReaderIndicationState_Locked:
            printf(" (LOCKED - Red LED solid)\n");
            break;
        case ReaderIndicationState_HeldOpenAlarm:
            printf(" (DOOR HELD OPEN - Red LED flash, alarm)\n");
            break;
        case ReaderIndicationState_ForceOpenAlarm:
            printf(" (FORCED OPEN - Red LED fast flash, alarm)\n");
            break;
        default:
            printf("\n");
            break;
    }

    return ErrorCode_OK;
}

void Reader_ApplyLEDPattern(LPA_t reader_id, LEDConfig_t* config) {
    if (!config) return;

    const char* led_names[] = {"RED", "YELLOW", "GREEN"};
    const char* color_names[] = {"OFF", "RED", "YELLOW", "GREEN"};

    printf("READER [%d:%d]: LED %s -> %s",
           reader_id.type, reader_id.id,
           led_names[config->LEDId],
           color_names[config->OnColor]);

    if (config->OffTime > 0) {
        printf(" FLASH (on:%dms off:%dms)\n", config->OnTime * 100, config->OffTime * 100);
    } else {
        printf(" SOLID\n");
    }
}

void Reader_ApplyBuzzerPattern(LPA_t reader_id, BuzzerConfig_t* config) {
    if (!config) return;

    printf("READER [%d:%d]: BUZZER -> %d beeps (on:%dms off:%dms)\n",
           reader_id.type, reader_id.id,
           config->Count,
           config->OnTime * 100,
           config->OffTime * 100);
}

// =============================================================================
// Testing Functions
// =============================================================================

ErrorCode_t Reader_PostCard(LPA_t reader_id, uint64_t card_number) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader) return ErrorCode_ObjectNotFound;

    printf("READER [%d:%d]: Card %llu presented (mode: %d)\n",
           reader_id.type, reader_id.id, card_number, reader->CurrentMode);

    reader->LastActivity = time(NULL);
    return ErrorCode_OK;
}

ErrorCode_t Reader_PostKey(LPA_t reader_id, char key) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader) return ErrorCode_ObjectNotFound;

    printf("READER [%d:%d]: Key '%c' pressed\n",
           reader_id.type, reader_id.id, key);

    reader->LastActivity = time(NULL);
    return ErrorCode_OK;
}

ErrorCode_t Reader_PostPIN(LPA_t reader_id, const char* pin) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader) return ErrorCode_ObjectNotFound;

    printf("READER [%d:%d]: PIN %s entered\n",
           reader_id.type, reader_id.id, pin);

    reader->LastActivity = time(NULL);
    return ErrorCode_OK;
}

// =============================================================================
// OSDP Reader Functions
// =============================================================================

ErrorCode_t Reader_InitOSDP(LPA_t reader_id, const OSDP_Config_t* config, const char* port) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader || !config || !port) {
        return ErrorCode_BadParams;
    }

    // Create OSDP reader handle
    OSDP_Reader_t* osdp = OSDP_Reader_Create(reader_id, config);
    if (!osdp) {
        return ErrorCode_OutOfMemory;
    }

    // Initialize communication
    ErrorCode_t err = OSDP_Reader_Init(osdp, port);
    if (err != ErrorCode_OK) {
        OSDP_Reader_Destroy(osdp);
        return err;
    }

    // Store handle in reader
    reader->osdp_handle = osdp;
    reader->SignalType = SignalType_OSDP;

    printf("READER [%d:%d]: OSDP initialized on %s\n",
           reader_id.type, reader_id.id, port);

    return ErrorCode_OK;
}

ErrorCode_t Reader_PollOSDP(LPA_t reader_id) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader || !reader->osdp_handle) {
        return ErrorCode_BadParams;
    }

    OSDP_Reader_t* osdp = (OSDP_Reader_t*)reader->osdp_handle;
    return OSDP_Reader_Poll(osdp);
}

ErrorCode_t Reader_SetOSDPLED(LPA_t reader_id, uint8_t led_number, OSDP_LED_Color_t color) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader || !reader->osdp_handle) {
        return ErrorCode_BadParams;
    }

    OSDP_Reader_t* osdp = (OSDP_Reader_t*)reader->osdp_handle;
    return OSDP_Reader_SetLED_Solid(osdp, led_number, color);
}

ErrorCode_t Reader_OSDPBeep(LPA_t reader_id, uint8_t duration) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader || !reader->osdp_handle) {
        return ErrorCode_BadParams;
    }

    OSDP_Reader_t* osdp = (OSDP_Reader_t*)reader->osdp_handle;
    return OSDP_Reader_Beep(osdp, duration);
}

bool Reader_IsOSDPOnline(LPA_t reader_id) {
    Reader_t* reader = Reader_Get(reader_id);
    if (!reader || !reader->osdp_handle) {
        return false;
    }

    OSDP_Reader_t* osdp = (OSDP_Reader_t*)reader->osdp_handle;
    return OSDP_Reader_IsOnline(osdp);
}
