"""
Main Dataset Generator module of the project for vehicle signals
recognition.

Constants can be changed in: ./utils/constants.py

Author: Filippenko Artyom, 2021-2022
MISIS Master Degree Project
"""

import os
import argparse

from utils import constants as c
from utils import logging_tool
from utils import filesystem_tool as fs
from utils import annotation_parser
from utils import video_editor
from utils import video_writer



class ExtractionTask:
    def __init__(self, import_path, export_path,
                 filename, annotation, overwrite, mode):
        """Task for extraction from video file.

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
        self.mode = mode
        # Read internal constants
        self.base_class = c.BASE_CLASS
        self.class_overlay = c.CLASS_OVERLAY
        self.chunk_size = c.CHUNK_SIZE
        self.extend_with_reversed = c.ADD_REVERSED
        self.target_attributes = c.TARGET_ATTRIBUTES
        self.logger_skip_atributes = c.LOGGER_SKIP_ATTRIBUTES

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
            **annotation_parser.get_labels(self.annotation_meta, c.TARGET_ATTRIBUTES.keys())
        }

    def log_attributes(self):
        """Writes all instance attributes to the log file. Cuts off all
        long attributes. e.g. Chunks
        """
        long_attributes = ('script', 'info')
        for attribute, value in self.__dict__.items():
            if attribute not in self.logger_skip_atributes:
                # Makes logs shorter. Script contains too much data.
                if attribute in long_attributes:
                    for info_attribute in value.keys():
                        if info_attribute == 'chunks':
                            chunks_in_script = len(value[info_attribute])
                            log_msg = \
                                f"{attribute}: {info_attribute}: {chunks_in_script} chunks total"
                        elif info_attribute == 'statistics':
                            stats = value[info_attribute].items()
                            for stat_name, stat_data in stats:
                                log_msg = f"{attribute}: {stat_name}: {stat_data}"
                        else:
                            log_msg = f"{attribute}: {info_attribute}: {value[info_attribute]}"
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



def analyze_video(source_path, output_path, file, annotation, overwrite, mode):
    """Creates extraction task.

    Args:
        source_path (str): Path to the source directory
        output_path (str): Path to the dataset directory
        file (srt): Video name
        annotation (str): Annotation name
        mode (str): 'sequence' or 'singleshot'

    Returns:
        obj: ExtractionTask instance
    """
    if debug:
        logger.debug(f"Analyzing... {file}")
    extraction = ExtractionTask(
        source_path,
        output_path,
        file,
        annotation,
        overwrite,
        mode
    )
    extraction.read_annotation()
    extraction.is_supported = supported_labels_check(extraction)

    return extraction



def generate_dataset(video_path, output_path, mode, overwrite):
    """Runs generator. Analyzes files in 'video_path' and if finds some
    supported ones (with annotation)

    WARNING: Annotation file must meet the criteria:
    filename = 'task_{VIDEO_FILE_NAME}_cvat for video 1.1.zip'.
    This is default archive name in CVAT extraction tool.

    Args:
        video_path (str): Path to the video files and annotation
            directory
        output_path (str): Path to the output directory
        mode (str): 'sequence' or 'singleshot'
    """
    supported_files = fs.extract_video_from_path(video_path)
    for file, annotation in supported_files.items():
        extraction = analyze_video(
            video_path,
            output_path,
            file,
            annotation,
            overwrite,
            mode,
        )
        if extraction.is_supported:
            export_chunks_from_extraction(extraction)
        else:
            if debug:
                logger.debug("No supported labels for extraction")



def export_chunks_from_extraction(extraction):
    """Generate script data, and if script has at least one chunk -
    creates direc

    Args:
        extraction (obj): ExtractionTask instance
    """
    extraction.script = video_editor.get_script(extraction)
    chunks_are_availible_in_script = (len(extraction.script['chunks']) > 0)
    if chunks_are_availible_in_script:
        if debug:
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
        if debug:
            logger.debug("No chunks in script. Skip file...")



def log_writer_report(writer_report):
    """Writes to log file report from writer. Report is useful for
    understanding behaviour of writer and catching broken chunks.

    Args:
        writer_report (OrderedDict): Any key
    """
    if debug:
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
    assert c.GENERATOR_MODE in ('sequence', 'singleshot'), "Unknown write mode"
    if c.GENERATOR_MODE == 'sequence':
        assert c.CHUNK_SIZE > 1 and c.FRAME_STEP > 0, "Wrong chunk size"



def add_custom_arguments(parser):
    """Adding new optional arguments for parser to

    Args:
        parser (obj): Empty parser object

    Returns:
        obj: Parser object with custom arguments
    """
    parser.add_argument(
        '-i',
        '--input',
        type=str,
        default=c.DATA_DIR_PATH,
        help='Input directory with videos and annotation archive'
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default=c.DATASET_DIR_PATH,
        help='Output directory for dataset'
    )
    parser.add_argument(
        '-m',
        '--mode',
        type=str,
        default=c.GENERATOR_MODE,
        choices=['sequence','singleshot'],
        help='Dataset generator mode. Sequence for MJPG and singleshot for JPG'
    )
    parser.add_argument(
        '--overwrite',
        action="store_true",
        help='Overwrite current dataset directory if exists'
    )
    parser.add_argument(
        '--debug',
        action="store_true",
        help='Enable debug log writing'
    )

    return parser



if __name__ == '__main__':
    """Main module. Initializes dataset generator.
    """
    check_settings()
    parser = argparse.ArgumentParser()
    parser = add_custom_arguments(parser)
    args = parser.parse_args()
    input_path = args.input
    output_path = args.output
    generator_mode = args.mode
    # Some optional arguments - essential for script OVERWRITE data and DEBUG
    if args.overwrite:
        overwrite = args.overwrite
    else:
        overwrite = c.OVERWRITE
    if args.debug:
        debug = args.debug
    else:
        debug = c.ENABLE_DEBUG_LOGGER
    if debug:
        logger = logging_tool.get_logger()
    # Create directory for dataset
    output_path = fs.create_dir(
        path=output_path,
        overwrite=overwrite
    )
    generate_dataset(input_path, output_path, generator_mode, overwrite)
