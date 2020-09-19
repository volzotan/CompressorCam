#include <RTCZero.h>

#include <Wire.h>
#include "Adafruit_MCP9808.h"
#include <Adafruit_NeoPixel.h>

// #define DEBUG

#define SHUTDOWN_ON_LOW_BATTERY
// #define DEEP_SLEEP
// #define HOST_DEFAULT_POWERED_ON
// #define WAIT_ON_BOOT_FOR_SERIAL
// #define TEMP_SENSOR_AVAILABLE
#define CONTROLLER_LEGACY

#define SERIAL Serial1
#define SERIAL_DEBUG SerialUSB

#ifdef DEBUG
  #define DEBUG_PRINT(x) SERIAL_DEBUG.print("["); SERIAL_DEBUG.print(getMillis()/1000); SERIAL_DEBUG.print("] "); SERIAL_DEBUG.println (x)
#else
  #define DEBUG_PRINT(x)
#endif

#include "global.h"
#include "constants.h"

// ---------------------------

int state                       = STATE_IDLE;

long trigger_done               = 0;

long currentTrigger             = -1;
long nextTrigger                = -1;
long postTriggerWaitDelayed     = -1;

long trigger_reduced_till       = -1;
long trigger_increased_till     = -1;

boolean trigger_ended_dirty     = false;        // zero was shutdown by force (max time active)

#define TRIGGER_INTERVAL        120 *1000       // take picture every X seconds [ms]
#define TRIGGER_INTERVAL_RED    600 *1000
#define TRIGGER_INTERVAL_INC    60  *1000

#define TRIGGER_MAX_ACTIVE      59  *1000       // zero & cam max time on [ms]
// #define TRIGGER_CAM_DELAY       5   *1000    // turn camera on X seconds after zero [ms]
// #define TRIGGER_WAIT_DELAYED    1   *1000    // wait for X seconds after zero requests shutdown [ms]
#define TRIGGER_COUNT           10000           // max number of triggers

#define STREAM_MODE_MAX_LIFETIME 5*60*1000

// ---------------------------

char *inputBuffer           = (char*) malloc(sizeof(char) * 100);
String serialInputString    = "";
char serialCommand          = 0;
int serialParam             = -1;
int serialParam2            = -1;

// ---------------------------

RTCZero rtc;
long now = -1;

Adafruit_NeoPixel pixels(1, PIN_PIXEL, NEO_GRB + NEO_KHZ800);

#ifdef TEMP_SENSOR_AVAILABLE
    Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
    float temp = 0;
#endif 

// ---------------------------

void setup() {

    SerialUSB.begin(9600);
    SERIAL.begin(9600);

    resetSerial();

    rtc.begin(true); // reset internal timer

    // rtc.setHours(4);
    // rtc.setMinutes(50);

    DEBUG_PRINT("INIT");
    DEBUG_PRINT("DEBUG MODE ON");

    initPins();

    pixels.begin();

    #ifdef WAIT_ON_BOOT_FOR_SERIAL
        while (!SerialUSB) {;}
        DEBUG_PRINT("SerialUsb connected");
    #endif

    // set the resolution mode of reading
    // Mode  Resolution  SampleTime
    //  0    0.5°C       30 ms
    //  1    0.25°C      65 ms
    //  2    0.125°C     130 ms
    //  3    0.0625°C    250 ms

    #ifdef TEMP_SENSOR_AVAILABLE
        if (!tempsensor.begin(0x18)) {
            DEBUG_PRINT("temperature sensor not found");
        } else {
            tempsensor.setResolution(1); 
        }
    #endif

    // battery life
    if (!checkBattHealth()) {
        // battery is empty, abort right now!

        DEBUG_PRINT("battery low! stopping...");
        #ifdef SHUTDOWN_ON_LOW_BATTERY 

            stopAndShutdown();

            // #ifndef DEBUG
            //     led(50, 0, 0);
            //     delay(1000);
            //     stopAndShutdown();
            // #else
            //     DEBUG_PRINT("stopping aborted (DEBUG mode on)");
            // #endif

        #else
            DEBUG_PRINT("stopping aborted (no SHUTDOWN_ON_LOW_BATTERY)");
        #endif

    }

    #ifdef DEBUG
    
        pixels.clear();

        for (int i=0; i<50; i++) {
            SerialUSB.print(".");
            if (i%2 == 0) {
                led(0, 50, 50);
            } else {
                led(0,  0, 0);
            }
            delay(100);
        }
        SerialUSB.println();
        pixels.clear();

        DEBUG_PRINT("-----------------");
        DEBUG_PRINT("Battery pin value:");
        analogRead(PIN_BATT_DIRECT);
        delay(100);
        DEBUG_PRINT(analogRead(PIN_BATT_DIRECT));
        DEBUG_PRINT("Battery [v]:");
        DEBUG_PRINT(getBatteryVoltage());
        DEBUG_PRINT("Battery [%]:");
        DEBUG_PRINT(getBatteryPercentage());
        DEBUG_PRINT("Temperature [C]:");
        #ifdef TEMP_SENSOR_AVAILABLE
            temp = tempsensor.readTempC();
            if (temp == temp) { // is not NaN
                DEBUG_PRINT(temp);
            }
        #else:
            DEBUG_PRINT("(temp sensor not available)");
        #endif
        DEBUG_PRINT("-----------------");
        DEBUG_PRINT("TRIGGER_INTERVAL:");
        DEBUG_PRINT(TRIGGER_INTERVAL);
        DEBUG_PRINT("TRIGGER_INTERVAL_RED:");
        DEBUG_PRINT(TRIGGER_INTERVAL_RED);
        DEBUG_PRINT("TRIGGER_INTERVAL_INC:");
        DEBUG_PRINT(TRIGGER_INTERVAL_INC);
        DEBUG_PRINT("TRIGGER_MAX_ACTIVE:");
        DEBUG_PRINT(TRIGGER_MAX_ACTIVE);
        DEBUG_PRINT("-----------------");
    #endif

    // wait 5 seconds without disabling USB to allow uploads and check for stream-mode
    long bootDelay = millis() + 5000;
    boolean enterStreamMode = false;
    while (millis() < bootDelay) {
        if (buttonPressed(PIN_BUTTON)) { // stream mode
            enterStreamMode = true;
        }

        // TODO: flash LED to signal regular start 
    }

    if (enterStreamMode) {

        switchZeroOn(true);
        state = STATE_STREAM;

        DEBUG_PRINT("entering stream mode");
        led(0, 0, 50);

        // TODO: show stream state via LED

        // TODO: shutdown after 5min

    } else {
        DEBUG_PRINT("setup done");

        // let's go
        nextTrigger = getMillis() + 1000;
    }
}

void loop() { 
    serialEvent();  

    switch(state) {

        // do nothing and wait for incoming serial commands
        case STATE_STREAM: {
            break;

            if (millis() > STREAM_MODE_MAX_LIFETIME) {
                DEBUG_PRINT("stream mode: max lifetime reached");

                // TODO: LED red

                stopAndShutdown();
            } 

            delay(100);
        }

        // do nothing and check if it's time to fire a trigger event
        case STATE_IDLE: {

            // all trigger done?
            if (trigger_done >= TRIGGER_COUNT) {
                DEBUG_PRINT("done [IDLE -> LOOP]");

                stopAndShutdown();
                // state = STATE_LOOP;
            }   

            now = getMillis();

            // time for new trigger event?
            if (now >= nextTrigger) {
                currentTrigger = nextTrigger; 

                int interval_length = TRIGGER_INTERVAL;

                if (trigger_reduced_till > 0) {
                    if (now < trigger_reduced_till) {
                        interval_length = TRIGGER_INTERVAL_RED;
                        DEBUG_PRINT("interval in reduced trigger state");
                    } else {
                        trigger_reduced_till = -1;
                        DEBUG_PRINT("interval switched from reduced to regular");
                    }
                } else if (trigger_increased_till > 0) {
                    if (now < trigger_increased_till) {
                        interval_length = TRIGGER_INTERVAL_INC;
                        DEBUG_PRINT("interval in increased trigger state");
                    } else {
                        trigger_increased_till = -1;
                        DEBUG_PRINT("interval switched from increased to regular");
                    }
                }

                nextTrigger += interval_length; 
                
                // sanity check
                while (nextTrigger < now) {
                    nextTrigger += interval_length; 
                    DEBUG_PRINT("ERROR: nextTrigger in past. adjusting...");
                }

                DEBUG_PRINT("start [IDLE -> TRIGGER_START]");
                state = STATE_TRIGGER_START;
            } else {
                // sleep 
                wait();
            }

            break;
        }

        // start the camera, the pi and the USB connections
        case STATE_TRIGGER_START: {

            if (!checkBattHealth()) {
                #ifdef SHUTDOWN_ON_LOW_BATTERY

                    stopAndShutdown();

                    // #ifndef DEBUG
                    //     stopAndShutdown();
                    // #else
                    //     DEBUG_PRINT("stopping aborted (DEBUG mode on)");
                    // #endif
                #else
                    DEBUG_PRINT("stopping aborted (no SHUTDOWN_ON_LOW_BATTERY)");
            #endif
            }

            switchZeroOn(true);

            trigger_done += 1;
            DEBUG_PRINT("trigger active [TRIGGER_START -> TRIGGER_WAIT]");
            state = STATE_TRIGGER_WAIT;

            break;
        }

        // pi is currently running and should be shutdown at the latest 
        // after TRIGGER_MAX_ACTIVE. May ask for shutdown before that,
        // if so: waiting for X to pass
        case STATE_TRIGGER_WAIT: {

            now = getMillis();

            if (now >= currentTrigger + TRIGGER_MAX_ACTIVE) {

                switchZeroOn(false);
                postTriggerWaitDelayed = -1;
                trigger_ended_dirty = true;
                DEBUG_PRINT("trigger max active done [TRIGGER_WAIT -> IDLE]");
                DEBUG_PRINT("uptime [ms]: ");
                DEBUG_PRINT(now-currentTrigger);
                state = STATE_IDLE;
            } else if (postTriggerWaitDelayed > 0 && now >= postTriggerWaitDelayed) {

                switchZeroOn(false);
                postTriggerWaitDelayed = -1;
                trigger_ended_dirty = false;
                DEBUG_PRINT("trigger done by request [TRIGGER_WAIT -> IDLE]");
                DEBUG_PRINT("uptime [ms]:");
                DEBUG_PRINT(now-currentTrigger);
                state = STATE_IDLE;
            }

            // stay active and do not enter deep sleep since communication
            // via UART will happen

            break;
        }

        default: {
            DEBUG_PRINT("ERROR! illegal state!");
        }
    }
}

void alarmFired() {}

void stopAndShutdown() {

    DEBUG_PRINT("STOP AND SHUTDOWN");

    switchZeroOn(false);
    pixels.clear();
    pixels.show();

    while(true) {
        rtc.standbyMode();
    }
}
