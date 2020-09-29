from PIL import Image, ExifTags
import os
import argparse
from shutil import copyfile

INPUT_FOLDERS                           = ["_assets"] #, "images"]
OUTPUT_FOLDER_DEFAULT                   = "assets_scaled"
LONGER_BORDER_DOWNSCALE_LENGTH_DEFAULT  = 1000

SCALED_SUFFIX                           = "" #"_scaled"

EXTENSIONS                              = [".jpg", ".png", ".gif"]

JPEG_QUALITY                            = 65

images = []
non_images = []

def get_relative_path(f):

    relative_path = ""

    if f[0].startswith("_work"):
        relative_path = f[0][f[0].index("/")+1:]
        relative_path = "work/" + relative_path
    else:
        try:
            if f[0].index("/") >= 0:
                relative_path = f[0][f[0].index("/")+1:]
        except ValueError as e:
            pass # / not found in string

    return relative_path


def get_new_path(f):

    relative_path = get_relative_path(f)
    extension = f[1][f[1].rfind("."):]
    new_filename = f[1][:-len(extension)] + SCALED_SUFFIX + extension
    new_full_path = os.path.join(OUTPUT_FOLDER, relative_path, new_filename)

    return new_full_path


ap = argparse.ArgumentParser()
ap.add_argument("-o", "--outputfolder", help="Output folder", default=OUTPUT_FOLDER_DEFAULT)
ap.add_argument("-s", "--size", help="Longer border downscale length (px)", type=int, default=LONGER_BORDER_DOWNSCALE_LENGTH_DEFAULT)
ap.add_argument("-w", "--overwrite", help="Overwrite when already existing", type=bool, default=False)
ap.add_argument("-n", "--copynonimagefiles", help="Copy non-image files", type=bool, default=False)
args = vars(ap.parse_args())

OUTPUT_FOLDER = args["outputfolder"]
LONGER_BORDER_DOWNSCALE_LENGTH = args["size"]

skip = 0

for input_folder in INPUT_FOLDERS:
    for root, dirs, files in os.walk(input_folder):
        for f in files:
            non_image = True

            if f.lower().endswith(".ds_store"):
                continue

            if not args["overwrite"]:
                new_full_path = get_new_path((root, f))
                if os.path.exists(new_full_path):
                    print("skipped file: {}".format(f))
                    skip += 1
                    continue;

            for ext in EXTENSIONS:
                if f.lower().endswith(ext):
                    images.append((root, f))
                    non_image = False
                    break

            if non_image:
                non_images.append((root, f))

print("skipped {} files".format(skip))
print("found {} images".format(len(images)))
print("found {} non-images".format(len(non_images)))

for input_folder in INPUT_FOLDERS:
    if input_folder == OUTPUT_FOLDER:
        print("input and output directory identical. overwrite would occur. exit!")
        exit(-1)

try:
    os.mkdir(OUTPUT_FOLDER)
except FileExistsError as e:
    pass

if args["copynonimagefiles"]:
    for f in non_images:

        relative_path = get_relative_path(f)
        dst = os.path.join(OUTPUT_FOLDER, relative_path, f[1])

        # print(f)
        # print(os.path.join(OUTPUT_FOLDER, relative_path))
        # print(dst)
        # print("---")

        try:
            # create output dir incl. subdirs
            os.makedirs(os.path.join(OUTPUT_FOLDER, relative_path))
        except FileExistsError as e:
            pass

        copyfile(os.path.join(*f), dst)
        print("saved: {}".format(dst))

    print("copied {} non-image files".format(len(non_images)))

for image in images:
    # print image

    img = Image.open(os.path.join(image[0], image[1]))

    skip = False
    if img.size[0] < LONGER_BORDER_DOWNSCALE_LENGTH and img.size[1] < LONGER_BORDER_DOWNSCALE_LENGTH:
        skip = True

    if not skip:
        scaled_size = (0, 0)
        if img.size[0] > img.size[1]:
            scaled_size = ( LONGER_BORDER_DOWNSCALE_LENGTH, img.size[1] / (img.size[0] / LONGER_BORDER_DOWNSCALE_LENGTH) )
        else: 
            scaled_size = ( img.size[0] / (img.size[1] / LONGER_BORDER_DOWNSCALE_LENGTH), LONGER_BORDER_DOWNSCALE_LENGTH )

        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break

        if img._getexif() is not None:
            exif = dict(img._getexif().items())

            if orientation in exif:
                if exif[orientation] == 3:
                    img = img.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    img = img.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    img = img.rotate(90, expand=True)

        img.thumbnail(scaled_size, Image.ANTIALIAS)
        #img.show()

    new_full_path = get_new_path(image)

    try:
        os.makedirs(os.path.dirname(new_full_path))
    except Exception as e:
        pass
        
    if new_full_path.lower().endswith(".jpg"):
        img.save(new_full_path, quality=JPEG_QUALITY)
    else:
        img.save(new_full_path)

    print("saved: {}".format(new_full_path))