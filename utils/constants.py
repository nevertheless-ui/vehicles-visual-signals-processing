# Project constants
# Author: Filippenko Artyom, 2021
# MISIS Master Degree Project
# Created: 2021.12.11
# Modified: 2021.12.11


import os

# LOGGER
ENABLE_DEBUG_LOGGER = True
LOGGER_FILENAME = 'debug.log'
# exclude long attributes from logs
SKIP_ATTRIBUTE = ('annotation_file',
                  'annotation_meta',
                  'annotation_tracks')


# DATA
DATA_DIR_PATH = 'data\\raw_data'
EXTRACTOR_RESOLUTION = (500, 500)     # pixels
VIDEO_CHUNK_SIZE = 2 # seconds
SKIP_FRAME_NUM = 1
TARGET_FPS = 30
SUPPORTED_VIDEO_FORMATS = ('.ts')
OVERWRITE = True                      # Output dataset directory


# ANNOTATION
CVAT_STARTSWITH = 'task_'
CVAT_ENDSWITH = ('cvat for video 1.1.zip')
