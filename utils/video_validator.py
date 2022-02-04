"""Tool for collecting annotation for file.
"""
import os

from utils import constants as c



def search_annotation(video_filename, files_in_directory):
    """Finds first match of annotation pattern in video directory.

    Args:
        video_filename (str): Name of the video file
        files_in_directory (list): All files in directory

    Returns:
        str: Annotation filename
    """
    start_name, end_name = \
        f"{c.CVAT_STARTSWITH}{video_filename.lower()}", c.CVAT_ENDSWITH

    annotation = next(
        (file for file in files_in_directory
         if (file.startswith(start_name) and file.endswith(end_name))),
        None,
    )

    return annotation



def get_annotations(video_path, video_files, files_in_directory):
    """Looking for an annotation file for the video file. If there is no
    annotation - returns empty dict if none.

    Args:
        video_path (str): Path to the directory with video files
        video_files (list): Supported video files
        files_in_directory (list): All files in directory

    Returns:
        dict: Where: key - video name, value - annotation name
    """
    assert os.path.isdir(video_path), "Video path is not a directory."
    assert len(video_files) > 0, "No supported video files in directory"
    assert len(video_files) <= len(files_in_directory)

    annotations = {}
    for file in video_files:
        annotation = search_annotation(
            file,
            files_in_directory
        )

        if annotation is not None:
            annotations[file] = annotation

    return annotations
