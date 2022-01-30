"""
Module for Video Extraction.
Contains class TrackAnalyzer which generates script for video chunks extractions
Each chunk contains data of source, lable, class and attributes
"""

from utils import constants as c
from utils.track_analyzer import TrackAnalyzer



def get_chunks(tracks, settings, labels):
    chunks = []

    for track in tracks:
        analyst = TrackAnalyzer(track, settings, labels)
        analyst.generate_sequences(add_reversed=c.ADD_REVERSED)

        for sequence_class, sequence_frames in analyst.sequences:
            new_chunk = {
                'track':analyst.track_id,
                'label':analyst.track_label,
                'class':sequence_class,
                'sequence':sequence_frames
            }
            chunks.append(new_chunk)

    return tuple(chunks)



def read_script_settings():
    settings = {}
    labels_and_attributes = \
        {key:value for (key,value) in c.TARGET_ATTRIBUTES.items()}

    settings['target_attributes'] = labels_and_attributes
    settings['base_class'] = c.BASE_CLASS
    settings['classes_overlay'] = c.CLASS_OVERLAY
    settings['chunks_size'] = c.CHUNK_SIZE

    return settings



def get_script(extraction):
    extraction_status = \
        extraction.info is not None and \
        extraction.annotation_tracks is not None
    assert extraction_status, "Extraction was not initialized properly"
    script = {}

    script['source_name'] = extraction.info['source_name']
    script['script_settings'] = read_script_settings()
    script['chunks'] = get_chunks(
        tracks=extraction.annotation_tracks,
        settings=script['script_settings'],
        labels=extraction.info['labels']
    )

    return script
