"""
Module for Video Extraction.
Contains class VideoDirector which creates ExtractionScript
"""

import os

from utils import constants as c



def create_script(extraction):
    extraction_status = \
        extraction.info is not None and \
        extraction.annotation_tracks is not None
    assert extraction_status, "Extraction was not initialized properly"

    script = {}

    script['source_name'] = extraction.info['source_name']
    script['script_settings'] = read_script_settings()
    script['chunks'] = generate_script_chunks(extraction.annotation_tracks)

    return script



def read_script_settings():
    settings = {}

    labels_and_attributes = \
        {key:value for (key,value) in c.TARGET_ATTRIBUTES.items()}

    settings['target_attributes'] = labels_and_attributes
    settings['base_class'] = c.BASE_CLASS
    settings['classes_overlay'] = c.CLASS_OVERLAY
    settings['frame_step'] = c.FRAME_STEP

    return settings



def generate_script_chunks(tracks):
    chunks = []

    chunks.append({'track':0, 'class':'idle', 'frames_seq':[1,2,3,4,5,6,7]})

    return tuple(chunks)


def write_video(file, script):
    pass
