"""
Main Dataset Generator module of the project for vehicle signals recognition
Author: Filippenko Artyom, 2021-2022
MISIS Master Degree Project
"""

import os

from utils import constants as c
from utils import filesystem_tool as fs_tool
from utils import logging_tool
from utils import annotation_parser
from utils import video_handler
from utils import chunk_extractor



class ExtractionTask:
    def __init__(self, import_path, export_path,
                 filename, annotation, overwrite):
        assert isinstance(overwrite, bool), "Overwrite must be boolean type"

        self.source_path = os.path.join(import_path, filename)
        self.output_path = os.path.join(export_path, f"{filename}_data")
        self.annotation_path = os.path.join(import_path, annotation)
        self.overwrite = overwrite


    def read_annotation(self):
        self.annotation_file = \
            annotation_parser.get_annotation(self.annotation_path)

        self.annotation_meta = self.annotation_file['annotations']['meta']
        self.annotation_tracks = self.annotation_file['annotations']['track']

        self.source_name = self.annotation_meta['source']
        self.frames_size = self.annotation_meta['task']['size']
        self.start_frame = self.annotation_meta['task']['start_frame']
        self.stop_frame = self.annotation_meta['task']['stop_frame']
        self.video_width, self.video_height = \
            self.annotation_meta['task']['original_size'].values()

        self.tracks_number = len(self.annotation_tracks)
        self.tracks_size = {}
        for id, track in enumerate(self.annotation_tracks):
            self.tracks_size[id] = len(track['box'])


    def show_info(self):
        for attribute in [self.source_name, self.frames_size,
                          self.tracks_number, self.tracks_size,
                          self.video_width, self.video_height]:
            print(attribute)
        try:
            print(self.annotation_tracks[0]['box'][0]['attribute'][0]['@name'])
            print(self.annotation_tracks[0]['box'][0]['attribute'][0]['#text'])
        except KeyError:
            pass


    def create_output_dir(self):
        fs_tool.create_dir(path=self.output_path, overwrite=c.OVERWRITE)


    def log_attributes(self):
        for attribute, value in self.__dict__.items():
            if attribute not in c.SKIP_ATTRIBUTE:
                exec(f'{logger.debug(f"{attribute}: {value}")}')



def process_video(source_path, output_path, file, annotation):
    extraction = ExtractionTask(
        source_path, output_path,
        file, annotation,
        c.OVERWRITE
    )

    extraction.read_annotation()
    extraction.create_output_dir()
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
            annotation)



if __name__ == '__main__':
    if c.ENABLE_DEBUG_LOGGER:
        logger = logging_tool.get_logger()

    generate_dataset(
        video_path=c.DATA_DIR_PATH,
        output_path=c.DATA_DIR_PATH)

    exit()
