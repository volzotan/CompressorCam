/* Commandlist
 *
 *  K  ---  Knock | returns state (regular/stream mode)
 *
 *  B  ---  Battery
 *    8.00    80
 *    voltage percentage
 *  
 *  S  ---  Shutdown                        (S / S 1000)
 *  U  ---  Get Uptime
 *  T  ---  Temperature
 *  Z  ---  Turn Zero On/Off                (Z 0 / Z 1)

 *  D  ---  Read Debug Registers
 *  N  ---  Next Invocation

 *  L  ---  Set LED                         (L uint32_t) W|R|G|B --> 32 bytes

 *  R  ---  Reduce Interval
 *  I  ---  Increase Interval

     *  E  ---  Print EEPROM
     *  K  ---  Kill/reset EEPROM data
     *  
     *  Q  ---  Read Value
     *  W  ---  Write Value

 *  V  ---  Version Info

 *  [...]
 */

void serialEvent() {
    while (SERIAL.available()) {
        char inChar = (char) SERIAL.read();
        processCommand(inChar);
    }
}

void processCommand(char inChar) {

    // Buffer size exceeded
    if (strlen(inputBuffer) > 99) {
        errorSerial(ERRORCODE_MESSAGE_TOO_LONG);
        return;
    }
    
    if (inChar == '\n' || inChar == '\r') {

        int spacePos = strchr(inputBuffer, ' ')-inputBuffer;

        // sanity checks

        // empty
        if (strlen(inputBuffer) < 1) {
            errorSerial(ERRORCODE_MESSAGE_EMPTY);
            return;
        }

        // space on wrong pos / cmd longer than one char
        if (spacePos > 0 && spacePos != 1) {
            errorSerial(ERRORCODE_INVALID_MESSAGE);
            return;
        }

        // double space
        if (spacePos > 0 && spacePos != lastIndexOf(inputBuffer, ' ')) {
            errorSerial(ERRORCODE_INVALID_MESSAGE);
            return;
        }

        // everything ok:

        serialCommand = inputBuffer[0];    
        // ser.port->println(ser.serialCommand);
        
        if (spacePos > 0) {                
            sscanf(inputBuffer, "%*s %d", &serialParam);
        }
        
        executeCommand();
        resetSerial();
    } else {
        int len = strlen(inputBuffer);
        
        inputBuffer[len] = inChar; 
        inputBuffer[len+1] = '\0';    
    }    
}

void executeCommand() {
    #ifdef DEBUG
        DEBUG_PRINT("=> ");
        SerialUSB.println(serialCommand);
    #endif
    
    switch(serialCommand) {

        case 'K': // Ping / Knock
            SERIAL.print("K ");
            SERIAL.println(state);
        break;

        case 'B': // Battery Health
            SERIAL.print("K ");
            SERIAL.print(getBatteryVoltage());
            SERIAL.print(" ");
            SERIAL.println(getBatteryPercentage());
        break;
            
        case 'S': // Shutdown 
            if (serialParam > 0) {
                if (state != STATE_TRIGGER_WAIT) {
                    errorSerial(ERRORCODE_INVALID_PARAM);
                    break;
                }
                postTriggerWaitDelayed = getMillis() + serialParam; 
                DEBUG_PRINT("postTriggerWaitDelayed set");
            } else {
                switchZeroOn(false);    
                postTriggerWaitDelayed = -1;
            }
            okSerial();
            break;
        
        case 'U': // Uptime 
            //errorSerial(ERRORCODE_NOT_AVAILABLE, ser);
            SERIAL.print("K ");
            SERIAL.println(getMillis());
        break;   

        case 'T': // Temperature

            #ifdef TEMP_SENSOR_AVAILABLE
                lm75a.wakeup();
                delay(10);
                temp = lm75a.getTemperature();
                if (temp == temp) { // is not NaN
                    SERIAL.print("K ");
                    SERIAL.print(temp, 4);
                    SERIAL.println();
                } else {
                    errorSerial(ERRORCODE_NOT_AVAILABLE);
                }

                lm75a.shutdown();
            #else
                errorSerial(ERRORCODE_NOT_AVAILABLE);
            #endif
        break;     

        case 'Z': // Zero On 
            if (serialParam == 0) {
                switchZeroOn(false);
                okSerial();
            } else if (serialParam == 1) {
                switchZeroOn(true);
                okSerial();
            } else {
                errorSerial(ERRORCODE_INVALID_PARAM);
            }
        break; 

        case 'D': // Debug Registers
            SERIAL.print("K ");
            SERIAL.print(trigger_done);
            SERIAL.print(" ");
            SERIAL.print(trigger_reduced_till);
            SERIAL.print(" ");
            SERIAL.print(trigger_increased_till);
            SERIAL.print(" ");
            SERIAL.print(trigger_ended_dirty);
            SERIAL.println();
        break; 

        case 'N': // Next Invocation
            SERIAL.print("K ");
            SERIAL.print(nextTrigger);
            SERIAL.println();
        break; 

        case 'L': // Set LED

            // if (state != STATE_TRIGGER_WAIT) {
            //     errorSerial(ERRORCODE_INVALID_PARAM);
            //     break;
            // }

            led(serialParam);

            okSerial();
        break; 

        case 'R': // Reduce Interval
            trigger_reduced_till = getMillis() + TRIGGER_INTERVAL_RED * 1 + 30*1000L;
            trigger_increased_till = -1;

            // replace already existing next trigger
            nextTrigger = currentTrigger + TRIGGER_INTERVAL_RED; 
            okSerial();
        break; 
        
        case 'I': // Increase Interval
            trigger_reduced_till = -1;
            trigger_increased_till = getMillis() + TRIGGER_INTERVAL_INC * 3 + 30*1000L;

            // replace already existing next trigger
            nextTrigger = currentTrigger + TRIGGER_INTERVAL_INC; 
            okSerial();
        break; 

        case 'V': // Version Info
            SERIAL.print("K ");
            SERIAL.print(HARDWARE_REV);
            SERIAL.print(" ");
            SERIAL.print(VERSION);
            SERIAL.println();
        break; 
        
        default:
            errorSerial(ERRORCODE_UNKNOWN_CMD);
    }    

    // method returns and serial is reset
}

void resetSerial() {
    inputBuffer[0] = '\0';
    serialCommand = 0;
    serialParam = -1;
}

void errorSerial(int errcode) {
    resetSerial();
    SERIAL.print("E ");
    SERIAL.println(errcode);

    #ifdef DEBUG
        DEBUG_PRINT(">> sent ERROR");
    #endif
}

void okSerial() {
    SERIAL.println("K");

    #ifdef DEBUG
        DEBUG_PRINT(">> sent OK");
    #endif
}
