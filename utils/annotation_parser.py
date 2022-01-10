"""
Module for reading and extracting data from annotations to:
- get_annotation
- get_metadata
- get_trackdata
- get_label_attributes
"""

import os
import xmltodict

from zipfile import ZipFile



def get_annotation(annotation_path):
    assert os.path.isfile(annotation_path), f"No {annotation_path} in directory"

    with ZipFile(annotation_path) as zipfile:
        with zipfile.open('annotations.xml') as xml_file:
            video_annotation = xmltodict.parse(xml_file.read())

    video_metadata = video_annotation['annotations']['meta']
    tracks_data = video_annotation['annotations']['track']

    return video_metadata, tracks_data



def get_metadata(md):
    metadata = {}

    metadata['source_name'] = md['source']
    metadata['frames_size'] = md['task']['size']
    metadata['start_frame'] = md['task']['start_frame']
    metadata['stop_frame'] = md['task']['stop_frame']
    metadata['video_width'] = md['task']['original_size']['width']
    metadata['video_height'] = md['task']['original_size']['height']

    return metadata



def get_trackdata(tracks):
    trackdata = {}
    tracks_size = {}

    trackdata['tracks_number'] = len(tracks)

    for id, track in enumerate(tracks):
        tracks_size[id] = len(track['box'])

    trackdata['tracks_size'] = tracks_size

    return trackdata



def get_labels(metadata, target_labels):
    labeldata = {}

    for label in metadata['task']['labels']:
        lable_name = metadata['task']['labels'][label]['name']

        if lable_name in target_labels:
            attributes = get_attributes(
                metadata['task']['labels'][label],
                target_labels
            )

        labeldata[lable_name] = attributes

    return {'Labels':labeldata}



def get_attributes(label_data, target_labels):
    attributes = []

    try:
        for attribute_name in label_data['attributes']:
            for attribute in label_data['attributes'][attribute_name]:
                attributes.append(attribute['name'])
    except TypeError:
        pass

    return attributes
