"""
Module for Video Writing.
Read video and generates chunks from script description.
"""

import cv2

from utils import constants as c



class ChunkWriter:
    def __init__(self, source, output, script):
        self.source = source
        self.output = output

        self.source_name = script['source_name']
        self.chunks = script['chunks']


    def write_chunks(self):
        pass


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
