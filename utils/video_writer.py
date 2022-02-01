"""
Module for Video Writing.
Read video and generates chunks from script description.
"""
import os
import cv2

from utils import constants as c
from utils import filesystem_tool as fs



class ChunkWriter:
    def __init__(self, source, output, script, logger):
        self.source_path = source
        self.output_path = output
        self.script = script
        self.logger = logger

        self.fps = c.CHUNK_SIZE
        self.resolution = c.EXTRACTOR_RESOLUTION

        self.source_name = self.script['source_name']
        self.chunks = self.script['chunks']

        self.__read_video()
        self.__make_classes_subdirs()


    def __read_video(self):
        assert os.path.isfile(self.source_path), \
            f'{self.source_path} is missing'

        self.capture = cv2.VideoCapture(self.source_path)
        self.codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')


    def __make_classes_subdirs(self):
        available_classes = self.script['statistics']['classes'].keys()

        for label_class in available_classes:
            class_dir_path = os.path.join(self.output_path, label_class)
            fs.create_dir(class_dir_path, overwrite=True)


    def write_chunks(self):
        for num, chunk in enumerate(self.chunks):
            chunk_path = self.__get_chunk_path(num, chunk)

            output = self.__get_output(chunk_path)

            if c.ENABLE_DEBUG_LOGGER:
                self.logger.debug(f"Write: {chunk_path}")

        #iterate over chunks
        ## 1. create output
        ## 2. get frame
        ## 3. resize frame
        ## 4. write to output
        ## 5. release
        pass

    def __get_chunk_path(self, num, chunk):
        class_path = os.path.join(self.output_path, chunk['class'])

        file = self.source_name
        label_name = chunk['label']
        class_name = chunk['class']
        track_num = str.zfill(str(chunk['track']), 4)
        chunk_num = str.zfill(str(num), 4)

        chunk_name = \
            f"{file}_{label_name}_{class_name}_tr{track_num}_seq{chunk_num}"

        chunk_path = os.path.join(class_path, f"{chunk_name}.mjpg")

        return chunk_path


    def __get_output(self, chunk_path):
        video_output = cv2.VideoWriter(
            chunk_path,
            self.codec,
            self.fps,
            self.resolution,
        )
        return video_output





    def __resize_image_with_fill(image, target_image_resolution):
        border_v = 0
        border_h = 0
        img_w, img_h = image.shape[0], image.shape[1]
        aspect_ratio = \
            target_image_resolution[0] / target_image_resolution[1]

        if aspect_ratio >= (img_w/img_h):
            border_v = int(((aspect_ratio*img_h)-img_w)/2)
        else:
            border_h = int(((aspect_ratio*img_w)-img_h)/2)

        image = cv2.copyMakeBorder(image,
                                   border_v, border_v,
                                   border_h, border_h,
                                   cv2.BORDER_CONSTANT, 0)
        image = cv2.resize(image, target_image_resolution)

        return image


    def release(self):
        self.capture.release()



def start_writing_video_chunks(source, output, script, logger):
    if c.ENABLE_DEBUG_LOGGER:
        log_msg = f"Writing to '{output}': " \
                  f"{len(script['chunks'])} chunks in file"
        logger.debug(log_msg)

    writer = ChunkWriter(source, output, script, logger)

    writer.write_chunks()
    writer.release()
