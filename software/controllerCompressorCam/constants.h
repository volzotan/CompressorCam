// ----------- PINS -----------

#define PIN_BATT_DIRECT                   A1 // PB08
#define PIN_BUTTON                        11 // PA16
#define PIN_ZERO_EN                        9 // PA07
#define PIN_ZERO_FAULT                    A4 // PA05
#define PIN_SERVO                          6 // PA20
#define PIN_PIXEL                         10 // PA18
#define PIN_MUX_STATUS                     2 // PA08                


// ----------- OPTIONS -----------

#define LIPO_CELL_MIN                    3.1
#define LIPO_CELL_MAX                    4.2


// ----------- MISC -----------

#define HARDWARE_REV             "undefined"
#define VERSION                            0

#define VDBASEVOLTAGE                    3.3
#define VDRESISTOR1                      100
#define VDRESISTOR2                       33


// ----------- ERROR CODES -----------

#define ERRORCODE_INVALID_MESSAGE        100
#define ERRORCODE_MESSAGE_EMPTY          101
#define ERRORCODE_MESSAGE_TOO_LONG       102
#define ERRORCODE_UNKNOWN_CMD            103
#define ERRORCODE_INVALID_PARAM          104
#define ERRORCODE_NOT_AVAILABLE          110


// ----------- STATES -----------

#define STATE_UPLOAD                     10
#define STATE_STREAM                     11
#define STATE_IDLE                       12
#define STATE_TRIGGER_START              13
#define STATE_TRIGGER_WAIT               14