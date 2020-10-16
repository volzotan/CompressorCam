SECOND_EXPOSURE_SHUTTER_SPEED   = 9
SECOND_EXPOSURE_ISO             = 25
THIRD_EXPOSURE_SHUTTER_SPEED    = SECOND_EXPOSURE_SHUTTER_SPEED*(2**7)
FOURTH_EXPOSURE_SHUTTER_SPEED   = SECOND_EXPOSURE_SHUTTER_SPEED*(2**11)
FIFTH_EXPOSURE_SHUTTER_SPEED    = 2*1000*1000
EXPOSURE_COMPENSATION           = 4 # 6 = +1 stop

SHUTDOWN_ON_COMPLETE            = True 
CHECK_FOR_INTERVAL_REDUCE       = True
CHECK_FOR_INTERVAL_INCREASE     = True 

INCREASE_INTERVAL_ABOVE         = 0.00001
REDUCE_INTERVAL_BELOW           = 0.01

# very slow. gzip takes even with lowest 
# settings ~13s for one jpeg+raw image     
COMPRESS_CAPTURE_1              = False 
EVEN_ODD_DELETION_CAPTURE_1     = False

IMAGE_FORMAT                    = "jpeg"    # JPG format # V2: ~ 4.5 mb | 14 mb (incl. raw) // HQ: ~ 5 mb | 24 mb (incl. raw) 
# IMAGE_FORMAT                  = "rgb"   # 24-bit RGB format # V2: ~ 23 mb
# IMAGE_FORMAT                  = "yuv"   # YUV420 format
# IMAGE_FORMAT                  = "png"   # PNG format # V2: ~ 9 mb
WRITE_RAW                       = True
MODULO_RAW                      = 5        # only every n-th image contains RAW data, set to None to use WRITE_RAW

BASE_DIR                        = "/media/storage/"
OUTPUT_DIR_1                    = BASE_DIR + "captures_regular"
OUTPUT_DIR_2                    = BASE_DIR + "captures_low1"
OUTPUT_DIR_3                    = BASE_DIR + "captures_low2"
OUTPUT_DIR_4                    = BASE_DIR + "captures_low3"
OUTPUT_DIR_5                    = BASE_DIR + "captures_low4"
OUTPUT_FILENAME                 = "cap"

LOG_FILE                        = BASE_DIR + "log_ccam.log"

SERIAL_PORT                     = "/dev/ttyAMA0"

MIN_FREE_SPACE                  = 300

# PERSISTENT MODE
INTERVAL                        = 60 # in sec
MAX_ITERATIONS                  = 3000