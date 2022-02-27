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
from utils import args_parser
from utils import logging_tool
from utils import filesystem_tool as fs
from utils import extractor
from utils import video_editor
from utils import video_writer



def analyze_video(source_path, output_path, file, annotation,
                  overwrite, mode, logger, allow_class_mixing):
    """Creates extraction task.

    Args:
        source_path (str): Path to the source directory
        output_path (str): Path to the dataset directory
        file (srt): Video name
        annotation (str): Annotation name
        overwrite (bool): Overwrite dataset if already exists
        mode (str): 'sequence' or 'singleshot'
        logger (obj): logging class object
        allow_class_mixing (bool): e.g. If True - One frame can be added to
            brake and turn_left classes at the same time. Else - mixed signals
            frames will be dropped as confusing.

    Returns:
        obj: ExtractionTask instance
    """
    if debug:
        logger.debug(f"Analyzing... {file}")
    extraction = extractor.ExtractionTask(
        source_path,
        output_path,
        file,
        annotation,
        overwrite,
        mode,
        logger,
        allow_class_mixing
    )
    extraction.read_annotation()
    extraction.is_supported = fs.supported_labels_check(extraction)

    return extraction



def generate_dataset(video_path, output_path, mode,
                     overwrite, logger, allow_class_mixing):
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
        overwrite (bool): Overwrite dataset if already exists
        logger (obj): logging class object
        allow_class_mixing (bool): e.g. If True - One frame can be added to
            brake and turn_left classes at the same time. Else - mixed signals
            frames will be dropped as confusing.
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
            logger,
            allow_class_mixing,
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
        if debug:
            logging_tool.log_writer_report(logger, writer_report)
    else:
        if debug:
            logger.debug("No chunks in script. Skip file...")



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



if __name__ == '__main__':
    """Main module. Initializes dataset generator.
    """
    check_settings()
    parser = argparse.ArgumentParser()
    parser = args_parser.add_custom_arguments(parser)
    args = parser.parse_args()
    input_path = args.input
    output_path = args.output
    generator_mode = args.mode
    allow_class_mixing = args.allow_class_mixing
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
    generate_dataset(input_path, output_path, generator_mode,
                     overwrite, logger, allow_class_mixing)
