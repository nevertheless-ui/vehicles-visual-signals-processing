# Main module of the project for vehicle signals recognition
# Author: Filippenko Artyom, 2021
# MISIS Master Degree Project

import os

from utils import constants as c
from utils import video_validator
from utils import annotation_parser
from utils import video_handler
from utils import chunk_extractor


class ExtractionTask:
    def __init__(self, import_path, export_path,
                 filename, annotation, overwrite):
        self.source_path = os.path.join(import_path, filename)
        self.annotation_path = os.path.join(import_path, annotation)

        self.output_path = os.path.join(export_path, f"{filename}_data")
        self.overwrite = overwrite



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

    video_files = video_validator.get_annotations(video_path,
                                                  video_files,
                                                  files)
    return video_files


def create_sub_dir(path, overwrite=False):
    pass
    #if os.path.exists(NEW_DIR_PATH) and \
      # os.path.isdir(NEW_DIR_PATH) and \
       #overwrite:
        #shutil.rmtree(NEW_DIR_PATH)


def generate_dataset(video_path, dataset_path):
    assert os.path.isdir(video_path) != False, \
        f"Input path is not directory"

    supported_files = extract_video_from_path(video_path)




if __name__ == '__main__':
    generate_dataset(video_path=c.DATA_DIR_PATH,
                     dataset_path=c.DATA_DIR_PATH)

    exit()
