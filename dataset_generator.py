"""
Main Dataset Generator module of the project for vehicle signals
recognition.

Constants can be changed in: ./utils/constants.py

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
        """Task for extraction from video file..

        Args:
            import_path (str): Path to the source directory
            export_path (str): Path to the dataset directory
            filename (str): Video file
            annotation (str): Annotation file
            overwrite (bool): Overwrite existing dataset or not
        """
        self.source_path = os.path.join(import_path, filename)
        self.output_path = export_path
        self.annotation_path = os.path.join(import_path, annotation)
        self.overwrite = overwrite


    def read_annotation(self):
        """Reads annotation from annotation files and add it as
        attributes to the current instance.
        """
        self.annotation_meta, \
        self.annotation_tracks = \
            annotation_parser.get_annotation(self.annotation_path)

        self.info = {
            **annotation_parser.get_metadata(self.annotation_meta),
            **annotation_parser.get_trackdata(self.annotation_tracks),
            **annotation_parser.get_labels(self.annotation_meta,
                                           c.TARGET_ATTRIBUTES.keys())
        }


    def log_attributes(self):
        """Writes all instance attributes to the log file. Cuts off all
        long attributes. e.g. Chunks
        """
        long_attributes = ('script', 'info')

        for attribute, value in self.__dict__.items():
            if attribute not in c.SKIP_ATTRIBUTE:

                # Makes logs shorter. Script contains too much data.
                if attribute in long_attributes:

                    for info_attribute in value.keys():
                        if info_attribute == 'chunks':
                            log_msg = \
                                f"{attribute}: {info_attribute}: " \
                                f"{len(value[info_attribute])} " \
                                "chunks in script total"

                        elif info_attribute == 'statistics':
                            stats = value[info_attribute].items()

                            for stat_name, stat_data in stats:
                                log_msg = \
                                    f"{attribute}: {stat_name}: {stat_data}"

                        else:
                            log_msg = \
                                f"{attribute}: {info_attribute}: " \
                                f"{value[info_attribute]}"

                        logger.debug(log_msg)

                else:
                    logger.debug(f"{attribute}: {value}")



def supported_labels_check(extraction):
    """Checks if extraction contains attributes, which should be
    extracted to dataset.

    Args:
        extraction (obj): Instance of ExtractionTask

    Returns:
        bool: If annotation exists - True, else - False
    """
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
    """Creates extraction task.

    Args:
        source_path (str): Path to the source directory
        output_path (str): Path to the dataset directory
        file (srt): Video name
        annotation (str): Annotation name

    Returns:
        obj: ExtractionTask object
    """
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
    """Runs generator. Analyzes files in 'video_path' and if finds some
    supported ones (with annotation)

    WARNING: Annotation file must meet the criteria:
    filename = 'task_{VIDEO_FILE_NAME}_cvat for video 1.1.zip'.
    This is default archive name in CVAT extraction tool.

    Args:
        video_path (str): Path to the video files and annotation
            directory
        output_path (str): Path to the output directory
    """
    supported_files = fs.extract_video_from_path(video_path)

    for file, annotation in supported_files.items():
        extraction = analyze_video(video_path, output_path, file, annotation)

        if extraction.is_supported:
            export_chunks_from_extraction(extraction)

        else:
            if c.ENABLE_DEBUG_LOGGER:
                logger.debug("No supported labels for extraction")


def export_chunks_from_extraction(extraction):
    """Generate script data, and if script has at least one chunk -
    creates direc

    Args:
        extraction ([type]): [description]
    """
    extraction.script = video_editor.get_script(extraction)

    chunks_in_script = (len(extraction.script['chunks']) > 0)

    if chunks_in_script:
        if c.ENABLE_DEBUG_LOGGER:
            extraction.log_attributes()
            logger.debug(f"Writing chunks to: {extraction.output_path}")

        writer_report = video_writer.start_writing_video_chunks(
            source=extraction.source_path,
            output=extraction.output_path,
            script=extraction.script,
            logger=logger
        )

        log_writer_report(writer_report)

    else:
        if c.ENABLE_DEBUG_LOGGER:
            logger.debug("No chunks in script. Skip file...")



def log_writer_report(writer_report):
    """Writes to log file report from writer. Report is useful for
    understanding behaviour of writer and catching broken chunks.

    Args:
        writer_report (OrderedDict): Any key
    """
    if c.ENABLE_DEBUG_LOGGER:

        for name, value in writer_report.items():

            if name == 'Broken chunks list' and len(value) > 0:
                for record in value:
                    logger.debug(f"Report: {name}: {record}")

            else:
                logger.debug(f"Report: {name}: {value}")



def check_settings():
    """Checking constants for correct input format and values
    """
    assert (c.CHUNK_SIZE % 2) != 0, 'Chunk size must be odd!'
    assert isinstance(c.CHUNK_SIZE, int), "Overwrite must be int type"
    assert isinstance(c.OVERWRITE, bool), "Overwrite must be boolean type"
    assert os.path.isdir(c.DATA_DIR_PATH) != False, "Source is not directory"



if __name__ == '__main__':
    """Main module. Initializes dataset generator.
    """
    if c.ENABLE_DEBUG_LOGGER:
        logger = logging_tool.get_logger()

    check_settings()

    input_path = c.DATA_DIR_PATH
    output_path = c.DATASET_DIR_PATH
    overwrite = c.OVERWRITE

    # Create directory for dataset
    output_path = fs.create_dir(
        path=output_path,
        overwrite=overwrite
    )

    generate_dataset(
        video_path=input_path,
        output_path=output_path
    )
