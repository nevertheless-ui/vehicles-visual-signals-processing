# Main module of the project for vehicle signals recognition
# Author: Filippenko Artyom, 2021
# MISIS Master Degree Project

import os

from utils import constants as c
from utils import video_validator
from utils import video_handler
from utils import annotation_parser
from utils import chunk_extractor



def extract_supported_filenames(filenames):
    assert isinstance(filenames, list)
    assert len(filenames) > 0
    assert len(c.SUPPORTED_VIDEO_FORMATS) >= 1

    for filename in filenames:
        if filename.endswith(c.SUPPORTED_VIDEO_FORMATS):
            yield filename


def extract_videos(video_path):
    assert os.path.isdir(video_path) != False, \
        f"Input path is not directory"

    files = os.listdir(video_path)
    video_files = [file for file in extract_supported_filenames(files)]

    video_files = video_validator.add_annotations(video_path,
                                                  video_files,
                                                  files)


def generate_dataset(video_path, dataset_path):
    extract_videos(video_path)



if __name__ == '__main__':
    generate_dataset(video_path=c.DATA_DIR_PATH,
                     dataset_path=c.DATA_DIR_PATH)

    exit()
