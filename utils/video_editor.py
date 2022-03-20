"""
Module for Video Extraction.
Contains class TrackAnalyzer which generates script for video chunks
extractions. Each chunk contains data of source, lable, class and
attributes.
"""
from collections import OrderedDict
from utils.track_analyzer import TrackAnalyzer



def get_chunks_stats(chunks):
    """Iterates over chunks and collects info about main features, such
    as:
    - labels
    - classes
    - tracks

    Args:
        chunks (list): Tupls of chunks with video data

    Returns:
        OrderedDict: Statistics of chunks
    """
    stats = OrderedDict()
    classes = OrderedDict()
    counted_tracks = []
    labels = []
    chunk_classes = []

    for chunk in chunks:
        if chunk['track'] not in counted_tracks:
            stats['tracks_in_script_total'] = stats.setdefault('tracks_in_script_total', 0) + 1
            counted_tracks.append(chunk['track'])
        if chunk['label'] not in labels:
            labels.append(chunk['label'])
        if chunk['class'] not in chunk_classes:
            chunk_classes.append(chunk['class'])
        classes[chunk['class']] = classes.setdefault(chunk['class'], 0) + 1

    stats['labels'] = labels
    stats['classes'] = classes
    stats['tracks_used'] = counted_tracks
    return stats


def get_chunks(tracks, settings, labels, frames_total, allow_class_mixing):
    """Iterates over tracks and analyze each track. Runs analysis tool
    to generate sequences. Sequences from tracks are appended to general
    chunks list with adding attributes of track, label, class, type and
    frames.

    Args:
        tracks (obj): Track object of ExtractionTask instance
        settings (dict): Script settings
        labels (dict): Labels from .info of ExtractionTask instance
        frames_total (int): Record from .info of ExtractionTask instance
        allow_class_mixing (bool): e.g. If True - One frame can be added to
            brake and turn_left classes at the same time. Else - mixed signals
            frames will be dropped as confusing.

    Returns:
        tuple: ({'track':(int), 'label':(str), 'class':(str),
            'type':(str),
            'sequence':(
                {frame:{'coordinates': (ax, ay, bx, by)}}, ...)},
                ...
            )
    """
    chunks = []
    for track in tracks:
        analyst = TrackAnalyzer(track, settings, labels, frames_total, allow_class_mixing)
        analyst.generate_sequences(
            extend_with_reversed=settings['extend_with_reversed']
        )
        #print(f'Frames in track: {list(analyst.track_frames.keys())}')
        #print(f'Mixed signals frames: {analyst.frames_with_mix_classes}')
        #print(f'Border signals frames: {analyst.frames_near_border}')
        #input()
        for sequence in analyst.sequences.values():
            for sequence_class, sequence_type, sequence_frames in sequence:
                skip_frames_in_sequence = \
                    any(
                        [frame in analyst.frames_to_skip
                         for frame in sequence_frames.keys()]
                    )
                if not skip_frames_in_sequence:
                    new_chunk = {
                        'track':analyst.track_id,
                        'label':analyst.track_label,
                        'class':sequence_class,
                        'type':sequence_type,
                        'sequence':sequence_frames,
                    }
                    chunks.append(new_chunk)
                else:
                    pass
    return tuple(chunks)



def read_script_settings(extraction):
    """Reads CONSTANTS and generate settings for script.

    Returns:
        dict: Settings in one object
    """
    settings = {}
    labels_and_attributes = {key:value for (key,value) in extraction.target_attributes.items()}
    settings['extend_with_reversed'] = extraction.extend_with_reversed
    settings['classes_overlay'] = extraction.class_overlay
    settings['target_attributes'] = labels_and_attributes
    settings['chunk_size'] = extraction.chunk_size
    settings['base_class'] = extraction.base_class
    settings['mode'] = extraction.mode

    return settings



def get_script(extraction):
    """Creates script for extraction. Makes brief analysis and adds
    settings for script. Collect chunks from the annotation.

    Args:
        extraction (obj): Instance of class ExtractionTask

    Returns:
        dict: {'source_name':str, 'script_settings':dict,
               'chunks':tuple, 'statistics':dict}
    """
    extraction_status = \
        (extraction.info is not None) and (extraction.annotation_tracks is not None)
    assert extraction_status, "Extraction was not initialized properly"
    script = {}
    script['source_name'] = extraction.info['source_name']
    script['script_settings'] = read_script_settings(extraction)
    script['chunks'] = get_chunks(
        tracks=extraction.annotation_tracks,
        settings=script['script_settings'],
        labels=extraction.info['labels'],
        frames_total=extraction.info['frames_size'],
        allow_class_mixing=extraction.allow_class_mixing
    )
    script['statistics'] = get_chunks_stats(script['chunks'])

    return script
