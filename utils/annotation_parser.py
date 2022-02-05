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
    """Unzips annotation archive and reads its content.

    Args:
        annotation_path (str): Path to annotation archive

    Returns:
        tuple: (video_metadata, tracks_data)
    """
    assert os.path.isfile(annotation_path), \
        f"No {annotation_path} in directory"

    with ZipFile(annotation_path) as zipfile:
        with zipfile.open('annotations.xml') as xml_file:
            video_annotation = xmltodict.parse(xml_file.read())

    video_metadata = video_annotation['annotations']['meta']
    tracks_data = video_annotation['annotations']['track']

    return video_metadata, tracks_data



def get_metadata(data):
    """Converts metadata from CVAT format.

    Args:
        data (OrderedDict): CVAT annotation

    Returns:
        dict: Annotation metadata
    """
    metadata = {}

    metadata['source_name'] = data['source']
    metadata['frames_size'] = data['task']['size']
    metadata['start_frame'] = data['task']['start_frame']
    metadata['stop_frame'] = data['task']['stop_frame']
    metadata['video_width'] = data['task']['original_size']['width']
    metadata['video_height'] = data['task']['original_size']['height']

    return metadata



def get_trackdata(tracks):
    """Converts CVAT track data.

    Args:
        tracks (OrderedDict): CVAT track data

    Returns:
        dict: Data of all tracks
    """
    trackdata, tracks_size = \
        {}, {}

    trackdata['tracks_number'] = len(tracks)

    for id, track in enumerate(tracks):
        tracks_size[id] = len(track['box'])

    trackdata['tracks_size'] = tracks_size

    return trackdata



def get_labels(metadata, target_labels):
    """Reads labels from annotation metadata

    Args:
        metadata (dict): Annotation metadata
        target_labels (dict): Labels which is needed to extract

    Returns:
        dict: {'labels':labeldata}
    """
    labeldata = {}

    for label in metadata['task']['labels']:
        label_name = metadata['task']['labels'][label]['name']

        if label_name in target_labels:
            attributes = get_attributes(
                metadata['task']['labels'][label]
            )

        labeldata[label_name] = tuple(attributes)

    labels = {'labels':labeldata}

    return labels



def get_attributes(label_data):
    """Reads all attributes of label.

    Args:
        label_data (dict): List of label attributes

    Returns:
        list: List of all attributes
    """
    attributes = []

    if label_data['attributes'] is not None:
        for attribute_name in label_data['attributes']:
            if len(label_data['attributes'][attribute_name]) > 0:
                for attribute in label_data['attributes'][attribute_name]:
                    attributes.append(attribute['name'])

    return attributes
