# arduino or arduino-cli ... (I renamed the latter to the first one)

arduino-cli core install arduino:samd
# arduino-cli lib install "Adafruit Unified Sensor"
# arduino-cli lib install "Adafruit MCP9808 Library"
arduino-cli lib install "Adafruit NeoPixel"
arduino-cli lib install "LM75A Arduino library"

# version 1.6.0 of the RTCZero library may not wake up after a few hours
# see: https://github.com/arduino-libraries/RTCZero/issues/62
arduino-cli lib install RTCZero@1.5.2