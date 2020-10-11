import cv2
import numpy as np
import os, sys
import datetime
import json
import traceback
import subprocess

import matplotlib as mpl
mpl.use('Agg') # allows plotting with empty DISPLAY variable
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUTPUT_STR  = "{0} {1:>5d}  / {2:>5d} | "
OUTPUT_STR += "skipped {3:>4d} | "
OUTPUT_STR += "aligned {4:>4d} | "
OUTPUT_STR += "failed {5:>4d} | "
OUTPUT_STR += "outlier {6:>4d} | "
OUTPUT_STR += "time_align {7:>.1f}"

class Aligner(object):

    # Paths
    REFERENCE_IMAGE                 = None
    EXTENSION                       = ".tif"

    INPUT_DIR                       = "images"
    OUTPUT_DIR                      = "aligned"

    TRANSLATION_DATA                = "translation_data.json"
    JSON_SAVE_INTERVAL              = 100
    SKIP_TRANSLATION                = -1     # do calculate translation data only from every n-th image
    # USE_CORRECTED_TRANSLATION_DATA  = False  # use the second set of values hidden in the json file

    LIMIT                           = -1

    # Options
    DOWNSIZE                        = True
    DOWNSIZE_FACTOR                 = 4.0
    CROP                            = False
    TRANSFER_METADATA               = True
    RESET_MATRIX_EVERY_LOOP         = True
    OUTPUT_IMAGE_QUALITY            = 75    # JPEG
    USE_SOBEL                       = True

    ALGORITHM                       = "ECC"

    # ECC Algorithm
    # WARP_MODE                       = cv2.MOTION_TRANSLATION 
    # WARP_MODE                       = cv2.MOTION_EUCLIDEAN  
    # WARP_MODE                       = cv2.MOTION_AFFINE 
    WARP_MODE                       = cv2.MOTION_HOMOGRAPHY
    NUMBER_OF_ITERATIONS            = 1000
    TERMINATION_EPS                 = 1e-6 #1e-10

    # ORB Algorithm
    # WARP_MODE                       = cv2.MOTION_HOMOGRAPHY
    # MAX_FEATURES                    = 500
    # GOOD_MATCH_PERCENT              = 0.15

    def __init__(self):

        self.counter             = 0
        self.skipped             = 0
        self.already_existing    = 0
        self.success             = 0
        self.failed              = 0
        self.outlier             = 0
        

    def init(self):

        self.__init__()

        # Read the reference image (as 8bit for the ECC algorithm)
        self.reference_image = cv2.imread(self.REFERENCE_IMAGE)

        if self.reference_image is None:
            print("reference image not found!")
            sys.exit(-1)

        # Find size
        self.sz = self.reference_image.shape

        if self.DOWNSIZE:
            # proceed with downsized version
            self.reference_image = cv2.resize(self.reference_image, (0,0), fx=1.0/self.DOWNSIZE_FACTOR, fy=1.0/self.DOWNSIZE_FACTOR)

        self.reference_image_gray = None
        self.reference_image_gray = cv2.cvtColor(self.reference_image, cv2.COLOR_BGR2GRAY)
        
        if self.USE_SOBEL:
            self.reference_image_gray = self._get_gradient(self.reference_image_gray)
            
        if self.ALGORITHM == "ECC":
            # Define termination criteria
            self.CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, self.NUMBER_OF_ITERATIONS,  self.TERMINATION_EPS)

        if self.ALGORITHM == "ORB":           
            orb = cv2.ORB_create(self.MAX_FEATURES)
            self.reference_image_gray = np.uint8(self.reference_image_gray) # TODO: different conversion if reference image is tiff?
            self.orb_keypoints1, self.orb_descriptors1 = orb.detectAndCompute(self.reference_image_gray, None)


    def _get_gradient(self, im):
        # Calculate the x and y gradients using Sobel operator
        grad_x = cv2.Sobel(im,cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(im,cv2.CV_32F, 0, 1, ksize=3)
     
        # Combine the two gradients
        grad = cv2.addWeighted(np.absolute(grad_x), 0.5, np.absolute(grad_y), 0.5, 0)
        return grad


    def calculate_translation_values(self, image, warp_matrix):

        source_file = os.path.join(self.INPUT_DIR, image)

        if self.RESET_MATRIX_EVERY_LOOP:
            warp_matrix = self._create_warp_matrix() # reset

        im2 = self._read_image_and_crop(source_file, read_as_8bit=True) 

        # proceed with downsized version
        if self.DOWNSIZE:
            im2_downsized = cv2.resize(im2, (0,0), fx=1.0/self.DOWNSIZE_FACTOR, fy=1.0/self.DOWNSIZE_FACTOR)
        else:
            im2_downsized = im2

        im2_gray = cv2.cvtColor(im2_downsized, cv2.COLOR_BGR2GRAY)
        if self.USE_SOBEL:
            im2_gray = self._get_gradient(im2_gray)

        if self.ALGORITHM == "ECC":
            try:
                # see: https://docs.opencv.org/3.4.7/dc/d6b/group__video__track.html#ga1aa357007eaec11e9ed03500ecbcbe47
                # inputMask     : An optional mask to indicate valid values of inputImage.
                # gaussFiltSize : An optional value indicating size of gaussian blur filter; (DEFAULT: 5)
                (cc, warp_matrix) = cv2.findTransformECC(self.reference_image_gray, im2_gray, warp_matrix, self.WARP_MODE, self.CRITERIA, None, 5)
            except Exception as e:
                raise e

        elif self.ALGORITHM == "ORB":
            orb = cv2.ORB_create(self.MAX_FEATURES)
            im2_gray = np.uint8(im2_gray)
            keypoints2, descriptors2 = orb.detectAndCompute(im2_gray, None)

            # Match features.
            matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
            matches = matcher.match(self.orb_descriptors1, descriptors2, None)
               
            # Sort matches by score
            matches.sort(key=lambda x: x.distance, reverse=False)
             
            # Remove not so good matches
            numGoodMatches = int(len(matches) * self.GOOD_MATCH_PERCENT)
            matches = matches[:numGoodMatches]
             
            # Draw top matches
            imMatches = cv2.drawMatches(self.reference_image_gray, self.orb_keypoints1, im2_gray, keypoints2, matches, None)
            cv2.imwrite(image + "_match.jpg", imMatches)
               
            # Extract location of good matches
            points1 = np.zeros((len(matches), 2), dtype=np.float32)
            points2 = np.zeros((len(matches), 2), dtype=np.float32)
             
            for i, match in enumerate(matches):
                points1[i, :] = self.orb_keypoints1[match.queryIdx].pt
                points2[i, :] = keypoints2[match.trainIdx].pt
               
            # Find homography
            h, mask = cv2.findHomography(points1, points2, cv2.RANSAC)
            warp_matrix = h

        else:
            raise Exception("unknown algorithm: {}".format(self.ALGORITHM))

        return (im2, warp_matrix)


    def step1(self, images):

        self._load_data()

        # Calculate all the translation values and write them into an JSON file

        warp_matrix = self._create_warp_matrix()

        for image in images:

            if self.SKIP_TRANSLATION > 0 and self.counter % self.SKIP_TRANSLATION != 0:
                skip = True
            else:
                skip = False

            self.counter += 1

            if self.LIMIT > 0 and self.counter > self.LIMIT:
                print("limit reached. abort.")
                break

            if image in self.translation_data:
                self.already_existing += 1
                print("{} already calculated".format(image))
                continue

            timer_start = datetime.datetime.now()
            if not skip:
                try:
                    (image_object, new_warp_matrix) = self.calculate_translation_values(image, warp_matrix)
                except Exception as e:
                    self.failed += 1
                    timediff = datetime.datetime.now() - timer_start
                    print("{} failed [{}s]".format(image, round(timediff.total_seconds(), 2)))
                    tb = traceback.format_exc()
                    print(tb)
                    continue

                # reuse warp matrix for next computation to speed up algorithm
                warp_matrix = new_warp_matrix
            else:
                continue
                # new_warp_matrix = self._create_warp_matrix()

            timediff = datetime.datetime.now() - timer_start
            self.success += 1

            save_matrix = new_warp_matrix.copy()
            if self.DOWNSIZE:
                if self.WARP_MODE == cv2.MOTION_HOMOGRAPHY:
                    save_matrix = save_matrix * np.array([[1, 1, self.DOWNSIZE_FACTOR], [1, 1, self.DOWNSIZE_FACTOR], [1.0/self.DOWNSIZE_FACTOR, 1.0/self.DOWNSIZE_FACTOR, 1]])
                else:
                    save_matrix = save_matrix * np.array([[1, 1, self.DOWNSIZE_FACTOR], [1, 1, self.DOWNSIZE_FACTOR]])

            translation_x = save_matrix[0][2]
            translation_y = save_matrix[1][2]

            # numpy float32 to python float
            #                                                     calculated translation in both axes           corrected values
            self.translation_data[image] = (save_matrix.tolist(), (float(translation_x), float(translation_y)), (0.0, 0.0))

            if not skip:
                print(OUTPUT_STR.format(image, self.counter, len(images), self.skipped, self.success, self.failed, self.outlier, timediff.total_seconds()))

            if self.counter % self.JSON_SAVE_INTERVAL == 0:
                self._save_data()
                self.display_curve()

        self._save_data()
        self.display_curve()


    def display_curve(self):

        trans_x = []
        trans_y = []
        trans_abs = []

        for item in self.translation_data:
            trans_x.append(self.translation_data[item][1][0])
            trans_y.append(self.translation_data[item][1][1])
            trans_abs.append(abs(self.translation_data[item][1][0]) + abs(self.translation_data[item][1][1]))

        xs = [x for x in range(0, len(trans_x))]

        # plt.subplot(3, 1, 1)
        # plt.plot(xs, trans_x)
        # plt.title('foo')
        # plt.ylabel('trans x')

        # plt.subplot(3, 1, 2)
        # plt.plot(xs, trans_y)
        # plt.ylabel('trans y')

        # plt.subplot(3, 1, 3)
        # plt.plot(xs, trans_abs)
        # plt.xlabel('images')
        # plt.ylabel('trans abs')


        plt.plot(xs, trans_x, color='#00ff00')
        plt.plot(xs, trans_y, color='#0000ff')
        plt.plot(xs, trans_abs, color='#999999')

        custom_lines = [Line2D([0], [0], color="#00ff00", lw=4),
                        Line2D([0], [0], color="#0000ff", lw=4),
                        Line2D([0], [0], color="#999999", lw=4)]

        plt.legend(custom_lines, ['x', 'y', 'x+y abs'], loc=0)

        plt.savefig(os.path.join(self.OUTPUT_DIR, "alignplot.png"))


    def step2(self):
        self._load_data()

        images = []

        for item in self.translation_data.keys():
            images.append(item)

        for image in images:
            self.counter += 1

            source_file = os.path.join(self.INPUT_DIR, image)
            destination_file = os.path.join(self.OUTPUT_DIR, image)

            if os.path.isfile(destination_file):
                self.already_existing += 1
                print("{} already transformed".format(image))
                continue

            if image not in self.translation_data:
                self.failed += 1
                print("{} translation data missing".format(image))

            # if self.USE_CORRECTED_TRANSLATION_DATA:
            #     # translation_data[image] = ( (original warp matrix), (computed_x, computed_y), (corrected_x, corrected_y) ) 
            #     (x, y) = (self.translation_data[image][2][0], self.translation_data[image][2][1])
            # else:
            #     (x, y) = (self.translation_data[image][1][0], self.translation_data[image][1][1])

            matrix = np.matrix(self.translation_data[image][0])

            timer_start = datetime.datetime.now()

            im2 = self._read_image_and_crop(source_file)
            im2_aligned = self.transform(im2, matrix, self.sz)
            cv2.imwrite(destination_file, im2_aligned, [int(cv2.IMWRITE_JPEG_QUALITY), self.OUTPUT_IMAGE_QUALITY])

            timediff_align = datetime.datetime.now() - timer_start

            # extract metadata and insert into aligned image
            if self.TRANSFER_METADATA:
                self._transfer_metadata(source_file, destination_file)

            print(OUTPUT_STR.format(image, self.counter, len(images), self.skipped, self.success, self.failed, self.outlier, timediff_align.total_seconds()))


    def transform(self, image_object, warp_matrix, size):

        if self.WARP_MODE == cv2.MOTION_HOMOGRAPHY :
            # Use warpPerspective for Homography 
            im2_aligned = cv2.warpPerspective(image_object, warp_matrix, (size[1], size[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        else :
            # Use warpAffine for Translation, Euclidean and Affine
            im2_aligned = cv2.warpAffine(image_object, warp_matrix, (size[1], size[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        
        return im2_aligned


    def _transfer_metadata(self, source, destination):
        # TODO: interim solution till I find something useful in GExiv2 to copy metadata

        return_value = subprocess.call(["exiftool", "-TagsFromFile", source, destination])
        subprocess.call(["exiftool", "-delete_original!", destination])

        if return_value != 0:
            print("transfer metadata failed")

        # metadata_source = GExiv2.Metadata()
        # metadata_source.open_path(source)
        # metadata_destination = GExiv2.Metadata()
        # metadata_destination.open_path(destination)

        # for item in dir(metadata_source):
        #     print(item)

        # for tag in metadata_source.get_exif_tags():
        #     metadata_destination.

        # metadata_destination.write()


    def _load_data(self):

        # translation_data already existing?

        self.translation_data = {}

        try:
            self.translation_data = json.load(open(self.TRANSLATION_DATA, "r"))
        except Exception as e:
            print("load json: " + str(e))


    def _save_data(self):
        json.dump(self.translation_data, open(self.TRANSLATION_DATA, "w"))
        print("json exported...")


    def _create_warp_matrix(self):
        # Define 2x3 or 3x3 matrices and initialize the matrix to identity
        if self.WARP_MODE == cv2.MOTION_HOMOGRAPHY:
            return np.eye(3, 3, dtype=np.float32)
        else:
            return np.eye(2, 3, dtype=np.float32)


    def _read_image_and_crop(self, source_file, read_as_8bit=False):

        if not read_as_8bit:
            im = cv2.imread(source_file, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        else:
            im = cv2.imread(source_file) 

        if not self.CROP:
            return im
        else:
            return im[290:3426, 0:5184]


    """
    That's something tricky here. What if I want to know if one alignment process
    yields better results than another? 
    This function can be called externally (e.g. compressor.py).

    """
    def compare_sharpness(self, path1, path2):
        im1 = self._get_gradient(cv2.imread(path1))
        im2 = self._get_gradient(cv2.imread(path2))

        # cv2.imshow("1", grad_x)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        print("img: {} means: {}".format(path1, cv2.mean(im1)))
        print("img: {} means: {}".format(path2, cv2.mean(im2)))
        