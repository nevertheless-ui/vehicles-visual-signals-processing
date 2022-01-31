"""
Main Dataset Generator module of the project for vehicle signals recognition
Author: Filippenko Artyom, 2021-2022
MISIS Master Degree Project
"""

import os

from utils import constants as c
from utils import logging_tool
from utils import filesystem_tool as fs
from utils import annotation_parser
from utils import video_editor
from utils import video_writer



class ExtractionTask:
    def __init__(self, import_path, export_path,
                 filename, annotation, overwrite):
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
        fs.create_dir(self.output_path, c.OVERWRITE)


    def log_attributes(self):
        long_attributes = ('script', 'info')

        for attribute, value in self.__dict__.items():
            if attribute not in c.SKIP_ATTRIBUTE:

                # Makes logs shorter. Script contains all chunks data.
                if attribute in long_attributes:
                    for info_attribute in value.keys():
                        if info_attribute == 'chunks':
                            log_msg = \
                                f"{attribute}: {info_attribute}: " \
                                f"{len(value[info_attribute])} chunks in script total"
                            logger.debug(log_msg)

                        elif info_attribute == 'statistics':
                            for stat_name, stat_data in value[info_attribute].items():
                                log_msg = \
                                        f"{attribute}: {stat_name}: {stat_data}"
                                logger.debug(log_msg)

                        else:
                            log_msg = \
                                f"{attribute}: {info_attribute}: " \
                                f"{value[info_attribute]}"
                            logger.debug(log_msg)

                else:
                    logger.debug(f"{attribute}: {value}")



def supported_labels_check(extraction):
    extraction_status = False
    target_labels = c.TARGET_ATTRIBUTES.keys()
    extraction_labels = extraction.info['labels'].keys()

    if any(label in extraction_labels for label in target_labels):

        for label, attributes in c.TARGET_ATTRIBUTES.items():
            if label in extraction_labels:
                extration_label_attributes = extraction.info['labels'][label]

                if any(i in extration_label_attributes for i in attributes):
                    extraction_status = True
                    break

    return extraction_status



def analyze_video(source_path, output_path, file, annotation):
    if c.ENABLE_DEBUG_LOGGER:
        logger.debug(f"Analyzing... {file}")

    extraction = ExtractionTask(
        source_path,
        output_path,
        file,
        annotation,
        c.OVERWRITE
    )
    extraction.read_annotation()
    extraction.is_supported = supported_labels_check(extraction)

    return extraction



def generate_dataset(video_path, output_path):
    supported_files = fs.extract_video_from_path(video_path)

    for file, annotation in supported_files.items():
        extraction = analyze_video(video_path, output_path, file, annotation)

        if extraction.is_supported:
            extraction.create_output_dir()
            extraction.script = video_editor.get_script(extraction)

            if c.ENABLE_DEBUG_LOGGER:
                extraction.log_attributes()
                logger.debug(f"Writing chunks to: {extraction.output_path}")

            video_writer.start_writing_video_chunks(
                source=extraction.source_path,
                output=extraction.output_path,
                script=extraction.script,
                logger=logger
            )

        else:
            if c.ENABLE_DEBUG_LOGGER:
                logger.debug("No supported labels for extraction")



def check_settings():
    assert (c.CHUNK_SIZE % 2) != 0, 'Chunk size must be odd!'
    assert isinstance(c.CHUNK_SIZE, int), "Overwrite must be int type"
    assert isinstance(c.OVERWRITE, bool), "Overwrite must be boolean type"
    assert os.path.isdir(c.DATA_DIR_PATH) != False, "Source is not directory"



if __name__ == '__main__':
    if c.ENABLE_DEBUG_LOGGER:
        logger = logging_tool.get_logger()

    check_settings() # add asserts to check CONSTANTS

    generate_dataset(
        video_path=c.DATA_DIR_PATH,
        output_path=c.DATA_DIR_PATH
    )
