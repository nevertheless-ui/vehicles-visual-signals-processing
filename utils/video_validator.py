import os

from utils import constants as c



def search_annotation(video_file, dir_files):
    start_name = f"{c.CVAT_STARTSWITH}{video_file.lower()}"
    end_name = c.CVAT_ENDSWITH
    annotation = next(
        (x for x in dir_files if (x.startswith(start_name) and x.endswith(end_name))),
        None,
    )
    return annotation



def get_annotations(video_path, video_files, dir_files):
    assert os.path.isdir(video_path), 'Video path is not a directory.'
    assert len(video_files) > 0, "No supported video files in directory."
    assert len(video_files) <= len(dir_files)

    annotations = {}
    for file in video_files:
        annotation = search_annotation(video_file=file,
                                       dir_files=dir_files)

        if annotation is not None:
            annotations[file] = annotation

    return annotations
