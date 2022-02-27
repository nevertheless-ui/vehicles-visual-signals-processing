"""Custom module for parsing of the script arguments
"""
from utils import constants as c


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
    parser.add_argument(
        '--allow_class_mixing',
        action="store_true",
        help='Allows extraction of singleshot frames with mixed signals'
    )

    return parser
