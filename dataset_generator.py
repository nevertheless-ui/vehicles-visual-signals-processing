# Main module of the project for vehicle signals recognition
# Author: Filippenko Artyom, 2021
# MISIS Master Degree Project

import os
import shutil

from utils import constants as c
from utils import video_validator
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
        create_dir(path=self.output_path, overwrite=c.OVERWRITE)




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

    video_files = video_validator.get_annotations(
        video_path,
        video_files,
        all_files
    )
    return video_files



def process_video(source_path, output_path, file, annotation):
    extraction_task = ExtractionTask(
        source_path, output_path,
        file, annotation,
        c.OVERWRITE
    )
    extraction_task.read_annotation()

    extraction_task.create_output_dir()

    extraction_task.show_info()



def create_dir(path, overwrite=False):
    try:
        os.mkdir(path)

    except FileExistsError:
        if overwrite:
            shutil.rmtree(path)
            os.mkdir(path)

        else:
            dir_counter = 0
            next_path = f"{path}_{str.zfill(str(dir_counter), 4)}"

            while os.path.isdir(next_path):
                dir_counter += 1
                next_path = f"{path}_{str.zfill(str(dir_counter), 4)}"

            os.mkdir(next_path)



def generate_dataset(video_path, output_path):
    assert os.path.isdir(video_path) != False, \
        f"Input path is not directory"

    supported_files = extract_video_from_path(video_path)
    for file, annotation in supported_files.items():
        print(file, annotation)
        process_video(source_path=video_path,
                      output_path=output_path,
                      file=file,
                      annotation=annotation)




if __name__ == '__main__':
    generate_dataset(
        video_path=c.DATA_DIR_PATH,
        output_path=c.DATA_DIR_PATH)

    exit()
