#include <RTCZero.h>
#include <Wire.h>
#include <Adafruit_NeoPixel.h>

#include <M2M_LM75A.h> // LM75A Temp Sensor

#include "global.h"
#include "constants.h"

// #define DEBUG
// #define WAIT_ON_BOOT_FOR_SERIAL

#define SHUTDOWN_ON_LOW_BATTERY
// #define DEEP_SLEEP
// #define HOST_DEFAULT_POWERED_ON
#define VERSION                     12.0

#define SERIAL Serial1
#define SERIAL_DEBUG SerialUSB

#ifdef DEBUG
  #define DEBUG_PRINT(x) SERIAL_DEBUG.print("["); SERIAL_DEBUG.print(getMillis()/1000); SERIAL_DEBUG.print("] "); SERIAL_DEBUG.println (x)
#else
  #define DEBUG_PRINT(x)
#endif

// #include "settings_revG.h"
// #include "settings_revH.h"
#include "settings_revI.h"
// #include "settings_revJ.h"

// ---------------------------

#define TRIGGER_INTERVAL        120 *1000       // take picture every X seconds [ms]
#define TRIGGER_INTERVAL_RED    600 *1000
#define TRIGGER_INTERVAL_INC    60  *1000

#define TRIGGER_MAX_ACTIVE      59  *1000       // zero & cam max time on [ms]
// #define TRIGGER_CAM_DELAY       5   *1000    // turn camera on X seconds after zero [ms]
// #define TRIGGER_WAIT_DELAYED    1   *1000    // wait for X seconds after zero requests shutdown [ms]
#define TRIGGER_COUNT           10000           // max number of triggers

#define STREAM_MODE_MAX_LIFETIME 5*60*1000
#define UPLOAD_MODE_MAX_LIFETIME 3*60*1000

// ---------------------------

int state                       = STATE_IDLE;

long trigger_done               = 0;

long currentTrigger             = -1;
long nextTrigger                = -1;
long postTriggerWaitDelayed     = -1;

long trigger_reduced_till       = -1;
long trigger_increased_till     = -1;

boolean trigger_ended_dirty     = false;        // zero was shutdown by force (max time active)

// ---------------------------

char *inputBuffer           = (char*) malloc(sizeof(char) * 100);
String serialInputString    = "";
char serialCommand          = 0;
long serialParam            = -1;
long serialParam2           = -1;

// ---------------------------

RTCZero rtc;
long now = -1;
long enter_state_time = -1;

Adafruit_NeoPixel pixels(1, PIN_PIXEL, NEO_GRB + NEO_KHZ800);
uint32_t ledBlinkColor = 0;
long ledBlinkTrigger = 0;

#ifdef TEMP_SENSOR_AVAILABLE
    // Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
    M2M_LM75A lm75a;;
    float temp = 0;
#endif 

// ---------------------------

void setup() {

    SerialUSB.begin(9600);
    SERIAL.begin(9600);

    resetSerial();

    rtc.begin(true); // reset internal timer

    DEBUG_PRINT("INIT");
    DEBUG_PRINT("DEBUG MODE ON");

    initPins();

    pixels.begin();
    pixels.clear();

    #ifdef WAIT_ON_BOOT_FOR_SERIAL
        while (!SerialUSB) {;}
        DEBUG_PRINT("SerialUsb connected");
    #endif

    #ifdef TEMP_SENSOR_AVAILABLE
        lm75a.begin();
        lm75a.shutdown();
    #endif

    // battery life
    if (!checkBattHealth()) {
        // battery is empty, abort right now!

        DEBUG_PRINT("battery low! stopping...");
        #ifdef SHUTDOWN_ON_LOW_BATTERY 
            stopAndShutdown();
        #else
            DEBUG_PRINT("stopping aborted (no SHUTDOWN_ON_LOW_BATTERY)");
        #endif
    }

    #ifdef DEBUG

        for (int i=0; i<50; i++) {
            SerialUSB.print(".");
            if (i%2 == 0) {
                led(10, 10, 0);
            } else {
                led(0,  0, 0);
            }
            delay(100);
        }
        SerialUSB.println();
        pixels.clear();

        DEBUG_PRINT("-----------------");

        #ifdef POWER_MUX_AVAILABLE
            DEBUG_PRINT("Power source:");
            if (digitalRead(PIN_MUX_STATUS)) {
                DEBUG_PRINT("USB");
            } else {
                DEBUG_PRINT("BATTERY");

                // if running from battery, flash bright
                led(100, 100, 0);
                delay(500);
                pixels.clear();
            }
        #endif
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
            lm75a.wakeup();
            delay(10);
            temp = lm75a.getTemperature();
            if (temp == temp) { // is not NaN
                DEBUG_PRINT(temp);
            }
            lm75a.shutdown();
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
    boolean alternate = false;
    while (millis() < bootDelay) {
        if (buttonPressed(PIN_BUTTON)) { // stream mode
            enterStreamMode = true;
            break;
        }

        if (alternate) {
            led(10, 10, 10);
        } else {
            led(0,  0, 0);
        }
        alternate = !alternate;
        delay(100);
    }

    if (enterStreamMode) {

        switchZeroOn(true);
        state = STATE_STREAM;
        enter_state_time = millis();

        DEBUG_PRINT("entering stream mode");
        ledBlink(0, 0, 10);

    } else {
        DEBUG_PRINT("setup done");

        // let's go
        nextTrigger = getMillis() + 2000;

        led(0, 30, 0);
        delay(1000);
        led(0, 0, 0);
    }

}

void loop() { 
    serialEvent();  
    ledEvent();

    switch(state) {

        // do nothing and wait for incoming serial commands
        case STATE_STREAM: {
            // if (enter_state_time - millis() > STREAM_MODE_MAX_LIFETIME) {
            //     DEBUG_PRINT("stream mode: max lifetime reached");

            //     // TODO: LED red

            //     stopAndShutdown();
            // } 

            // delay(100);

            break;
        }

        // do nothing wail waiting for incoming commands or timeout
        case STATE_UPLOAD: {
            if (enter_state_time - millis() > UPLOAD_MODE_MAX_LIFETIME) {
                DEBUG_PRINT("upload mode: max lifetime reached");

                state = STATE_IDLE;
                break;
            } 

            delay(100);
            berak;
        }

        // do nothing and check if it's time to fire a trigger event
        case STATE_IDLE: {

            // all trigger done?
            if (trigger_done >= TRIGGER_COUNT) {
                DEBUG_PRINT("done [IDLE -> LOOP]");

                stopAndShutdown();
                // state = STATE_LOOP;
            }   

            // millis overflow happens after 49 days, so ignore that issue here
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
                #else
                    DEBUG_PRINT("stopping aborted (no SHUTDOWN_ON_LOW_BATTERY)");
            #endif
            }

            switchZeroOn(true);

            trigger_done += 1;
            DEBUG_PRINT("trigger active [TRIGGER_START -> TRIGGER_WAIT]");
            state = STATE_TRIGGER_WAIT;

            // blink green once
            led(0, 10, 0);
            delay(500);
            led(0, 0, 0);

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

    for (int i=0; i<10; i++) {
        if (i%2 == 0) {
            led(30, 0, 0);
        } else {
            led(0,  0, 0);
        }
        delay(100);
    }

    pixels.clear();
    pixels.show();

    while(true) {
        rtc.standbyMode();
    }
}
