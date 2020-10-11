import os
import argparse
import datetime

from pydng.core import RPICAM2DNG
import exifread

MIN_RAW_SIZE_IN_BYTES   = 1024*1024*10 
EXIF_DATE_FORMAT        = "%Y:%m:%d %H:%M:%S"

filenames = []

parser = argparse.ArgumentParser()
parser.add_argument("directory", help="directory containing JPEGs with RAW data")
args = parser.parse_args()

for root, dirs, files in os.walk(args.directory):
    for file in files:
        if file.endswith('.jpg'):
            filenames.append([os.path.join(root, *dirs), file])

filenames = sorted(filenames)

d = RPICAM2DNG()
# r = RAW2DNG()
for filename in filenames:
    p = os.path.join(*filename)

    if os.path.getsize(p) < MIN_RAW_SIZE_IN_BYTES:
        print("skip:    {}".format(p))
        continue

    with open(p, 'rb') as f:

        # copy EXIF DateTime Original (Format 1970:01:01 01:23:45)

        metadata = exifread.process_file(f)
        try:
            timetaken = metadata["EXIF DateTimeOriginal"].values
            timetaken = datetime.datetime.strptime(timetaken, EXIF_DATE_FORMAT)
        except Exception as e:
            print("copying DateTimeOriginal Exif data failed for image {}. Error: {}".format(filename[-1], e))
            exit(-1)

    d.etags["EXIF DateTimeDigitized"] = timetaken.strftime(EXIF_DATE_FORMAT)

    d.convert(p, compress=False)

    print("convert: {}".format(p))
