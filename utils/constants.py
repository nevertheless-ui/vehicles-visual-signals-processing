"""
Project constants
"""
# LOGGER
ENABLE_DEBUG_LOGGER = True
LOGGER_FILENAME = 'debug.log'
# exclude long attributes from logs
LOGGER_SKIP_ATTRIBUTES = (
    'annotation_file',
    'annotation_meta',
    'annotation_tracks',
)


# DATA
DATA_DIR_PATH = 'D:\\data_ml\\raw_data'
DATASET_DIR_PATH = 'D:\\data_ml\\baseline_dataset'
EXTRACTOR_RESOLUTION = (500, 500)           # pixels
#VIDEO_CHUNK_SIZE = 2                       # seconds
#SKIP_FRAME_NUM = 1
#TARGET_FPS = 30
SUPPORTED_VIDEO_FORMATS = ('.ts')
OUTPUT_EXTENTION = 'avi'
OVERWRITE = True                            # Rewrite output dataset directory or backup it
GENERATOR_MODE = 'sequence'                 # 'sequence' or 'singleshot'
DIFF_THRESHOLD = 64                        # Threshold to clean images substraction noise

# VIDEO
TARGET_ATTRIBUTES = {
    'Vehicle':(
        #'alarm',
        'brake',
        #'turn_left',
        #'turn_right',
    )
}
ACTIVATION_NAME = 'activation'
DEACTIVATION_NAME = 'deactivation'
STATIC_NAME = 'static'
BASE_CLASS = 'idle'
CHUNK_SIZE = 5                               # - frames - MUST BE ODD
FRAME_STEP = 3                               # - frames shift
SKIP_FRAMES_NEAR_SWITCH_MARKER_SIZE = 3      # - Number of frames that will be
                                             # skipped in singleshot mode
CHUNK_BORDER_RATIO = 2                       # - Slice border multiplyer to make
                                             # bigger for dynamic markers
CLASS_OVERLAY = True                         # - Same frames can be used for different classes
CLASS_BALANCED = False                       # - Balance classes?
ADD_REVERSED = True                          # - EXPERIMENTAL.Try to reverse frames to augment data



# ANNOTATION
CVAT_STARTSWITH = 'task_'
CVAT_ENDSWITH = ('cvat for video 1.1.zip')
CVAT_LABELS = ('Vehicle')
