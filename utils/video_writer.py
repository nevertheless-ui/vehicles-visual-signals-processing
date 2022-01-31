"""
Module for Video Writing.
Read video and generates chunks from script description.
"""
import os
import cv2

from utils import constants as c
from utils import filesystem_tool as fs



class ChunkWriter:
    def __init__(self, source, output, script):
        self.source_path = source
        self.output_path = output
        self.script = script

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

            #self.output =

        #iterate over chunks
        ## 1. create output
        ## 2. get frame
        ## 3. resize frame
        ## 4. write to output
        ## 5. release
        pass

    def __get_chunk_path(self, num, chunk):
        class_path = os.path.join(self.output_path, chunk['class'])
        pass



    def get_(f_name, f_format, f_name_suffix, fps, codec, resolution):
        output_file_name = (f'{f_name}_{f_name_suffix}.{f_format}')
        video_output = cv2.VideoWriter(
            output_file_name,
            codec,
            fps,
            resolution,
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



def start_writing_video_chunks(source, output, script):
    writer = ChunkWriter(source, output, script)

    print(f"Writing to {output}: {len(script['chunks'])} chunks in file")
