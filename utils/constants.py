"""
Project constants
"""

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
EXTRACTOR_RESOLUTION = (500, 500) # pixels
VIDEO_CHUNK_SIZE = 2 # seconds
SKIP_FRAME_NUM = 1
TARGET_FPS = 30
SUPPORTED_VIDEO_FORMATS = ('.ts')
OVERWRITE = True                  # Output dataset directory

# VIDEO_EDITOR
TARGET_ATTRIBUTES = {
    'Vehicle':(
        #'alarm',
        'brake',
        #'turn_left',
        #'turn_right',
    )
}
BASE_CLASS = 'idle'
CLASS_OVERLAY = True  # Same frames can be used for different classes
CHUNK_SIZE = 15 # frames


# ANNOTATION
CVAT_STARTSWITH = 'task_'
CVAT_ENDSWITH = ('cvat for video 1.1.zip')
CVAT_LABELS = ('Vehicle')
