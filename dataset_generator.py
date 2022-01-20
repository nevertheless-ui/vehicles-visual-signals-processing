"""
Main Dataset Generator module of the project for vehicle signals recognition
Author: Filippenko Artyom, 2021-2022
MISIS Master Degree Project
"""

import os

from utils import constants as c
from utils import logging_tool
from utils import filesystem_tool as fs_tool
from utils import annotation_parser
from utils import video_editor



class ExtractionTask:
    def __init__(self, import_path, export_path,
                 filename, annotation, overwrite):
        assert isinstance(overwrite, bool), "Overwrite must be boolean type"

        self.source_path = os.path.join(import_path, filename)
        self.output_path = os.path.join(export_path, f"{filename}_data")
        self.annotation_path = os.path.join(import_path, annotation)
        self.overwrite = overwrite


    def read_annotation(self):
        self.annotation_meta, \
        self.annotation_tracks = \
            annotation_parser.get_annotation(self.annotation_path)

        self.info = {
            **annotation_parser.get_metadata(self.annotation_meta),
            **annotation_parser.get_trackdata(self.annotation_tracks),
            **annotation_parser.get_labels(self.annotation_meta,
                                           c.TARGET_ATTRIBUTES.keys())
        }


    def create_output_dir(self):
        fs_tool.create_dir(path=self.output_path, overwrite=c.OVERWRITE)


    def log_attributes(self):
        for attribute, value in self.__dict__.items():
            if attribute not in c.SKIP_ATTRIBUTE:
                logger.debug(f"{attribute}: {value}")



def process_video(source_path, output_path, file, annotation):
    if c.ENABLE_DEBUG_LOGGER:
        logger.debug(f"Processing... {file}")

    extraction = ExtractionTask(
        source_path,
        output_path,
        file,
        annotation,
        c.OVERWRITE
    )

    extraction.read_annotation()
    extraction.create_output_dir()

    extraction.script = video_editor.create_script(extraction)

    if c.ENABLE_DEBUG_LOGGER:
        extraction.log_attributes()



def generate_dataset(video_path, output_path):
    assert os.path.isdir(video_path) != False, \
        f"Input path is not directory"

    supported_files = fs_tool.extract_video_from_path(video_path)

    for file, annotation in supported_files.items():
        process_video(
            video_path,
            output_path,
            file,
            annotation,
        )



if __name__ == '__main__':
    if c.ENABLE_DEBUG_LOGGER:
        logger = logging_tool.get_logger()

    generate_dataset(
        video_path=c.DATA_DIR_PATH,
        output_path=c.DATA_DIR_PATH
    )
