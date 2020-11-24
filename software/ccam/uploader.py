import os
import shutil
import subprocess

import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("uploader")

class Uploader(object):

    def __init__(self):
        pass

    def run():
        pass

class RsyncUploader(Uploader):

    def __init__(directories, server_address):
        self.directories = directories
        self.server_address = server_address

    def run(self):
        for directory in self.directories:
            try:

                subprocess.run(["rsync", "-av", self.directory, server_address], check=True)
                
                for root, dirs, files in os.walk(directory):
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))

            except Exception as e:
                log.e("rsync command failed: {}".format(e))
                raise Exception("upload failed")


