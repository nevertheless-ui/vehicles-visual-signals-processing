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
    try:
        os.mkdir(path)

    except FileExistsError:
        if overwrite:
            shutil.rmtree(path)
            os.mkdir(path)

        else:
            dir_counter = 0
            next_path = f"{path}_{str.zfill(str(dir_counter), 4)}"

            while os.path.isdir(next_path):
                dir_counter += 1
                next_path = f"{path}_{str.zfill(str(dir_counter), 4)}"

            os.mkdir(next_path)



def extract_supported_filenames(filenames):
    assert isinstance(filenames, list)
    assert len(filenames) > 0
    assert len(c.SUPPORTED_VIDEO_FORMATS) >= 1

    for filename in filenames:
        if filename.endswith(c.SUPPORTED_VIDEO_FORMATS):
            yield filename



def extract_video_from_path(video_path):
    all_files = os.listdir(video_path)

    video_files = \
        [file for file in extract_supported_filenames(all_files)]

    video_files = video_validator.get_annotations(
        video_path,
        video_files,
        all_files
    )
    return video_files
