"""
Module for specific tasks with OS and filesystem, such as:
- Smart directory creation
- Extracting video files
- Searching annotation for video
"""

import os
import shutil

from utils import constants as c
from utils import video_validator



def create_dir(path, overwrite=False):
    """Creates new directory. If 'overwrite' is true - remove existing
    directory and creates a new one. Otherwise - backups old directory.

    Args:
        path (str): Path to the new directory
        overwrite (bool, optional): Remove old directory, if exists
            already. Defaults to False.

    Returns:
        next_path
    """
    try:
        os.mkdir(path)

    except FileExistsError:
        if overwrite:
            shutil.rmtree(path)
            os.mkdir(path)

        else:
            dir_counter = 0
            next_path = \
                f"{path}_backup_{str.zfill(str(dir_counter), 4)}"

            while os.path.isdir(next_path):
                    dir_counter += 1
                    next_path = \
                        f"{path}_backup_{str.zfill(str(dir_counter), 4)}"

            os.rename(path, next_path)
            os.mkdir(path)

    return path



def extract_supported_filenames(filenames):
    """Yields video files with supported extention. Refer to constants
    to check or add more supported extentions.

    Default tested ext - '.ts' (5 min, 30 fps)

    Args:
        filenames (list): List of file names

    Yields:
        str: Video file name
    """
    assert isinstance(filenames, list)
    assert len(filenames) > 0
    assert len(c.SUPPORTED_VIDEO_FORMATS) >= 1

    for filename in filenames:
        if filename.endswith(c.SUPPORTED_VIDEO_FORMATS):
            yield filename



def extract_video_from_path(video_path):
    """Extracts video file names with annotations.

    Args:
        video_path (str): Path to directory with video files

    Returns:
        dict: Where: key - video name, value - annotation name
    """
    files_in_directory = os.listdir(video_path)

    # Generator is used for cases with big number of files in directory
    video_files = \
        [file for file in extract_supported_filenames(files_in_directory)]

    video_files = video_validator.get_annotations(
        video_path,
        video_files,
        files_in_directory
    )
    return video_files



def supported_labels_check(extraction):
    """Checks if extraction contains attributes, which should be
    extracted to dataset.

    Args:
        extraction (obj): Instance of ExtractionTask

    Returns:
        bool: If annotation exists - True, else - False
    """
    extraction_status = False
    target_labels = extraction.target_attributes.keys()
    extraction_labels = extraction.info['labels'].keys()
    if any(label in extraction_labels for label in target_labels):
        for label, attributes in extraction.target_attributes.items():
            if label in extraction_labels:
                extration_label_attributes = extraction.info['labels'][label]
                if any(i in extration_label_attributes for i in attributes):
                    extraction_status = True
                    break
    return extraction_status
