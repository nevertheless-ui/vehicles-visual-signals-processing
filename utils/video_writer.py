"""Module reads video, creates output dir and exports chunks.
"""

import os
import cv2

from collections import OrderedDict

from utils import constants as c



class ChunkWriter:
    def __init__(self, source, output, script, logger):
        """Writer loads capture from video file and yield video chunks from
        it. It uses script from ExtractionTask class to define chunks and
        labels.

        Args:
            source (str): Path to source video file
            output (str): Path to root output directory
            script (dict): property of ExtractionTask from dataset
                generator main module
            logger (obj): logger object from main module
        """
        self.source_path = source
        self.output_path = output

        self.script = script
        self.logger = logger
        self.mode = self.script['script_settings']['mode']

        if self.mode == 'singleshot':
            self.fps = 1
            self.chunk_size = 1

        elif self.mode == 'sequence':
            self.chunk_size = self.script['script_settings']['chunk_size']
            self.fps = self.chunk_size

        self.resolution = c.EXTRACTOR_RESOLUTION
        self.broken_chunks = []

        self.source_name = self.script['source_name']
        self.chunks = self.script['chunks']

        # Loads capture to the memory and prepares output directories
        self.capture = self.__read_video(self.source_path)
        self.codec = self.__load_codec()

        self.__create_subdirs_for_each_class()


    def write_chunks(self):
        """Iterate over all chunks in script and write it to the output.
        Writing process stages:
        1. Creates output file
        2. Add frames from script sequence
        3. Test chunk integrity
        4. If passed - continue. Else - delete chunk.
        """
        self.valid_chunks_counter = 0

        for num, chunk in enumerate(self.chunks):
            try:
                if len(chunk['sequence'].keys()) > 3:
                    center_index = (self.chunk_size - 1) // 2
                    frame_num = list(chunk['sequence'].keys())[center_index]

                else:
                    frame_num = list(chunk['sequence'].keys())[0]

            except IndexError:
                frame_num = 'ERROR'

            chunk_path = self.__get_chunk_path(num, frame_num, chunk)
            log_msg = f"Writing: {chunk_path}"

            output = self.__get_output(chunk_path)

            for frame, coordinates in chunk['sequence'].items():
                self.__add_frame_to_chunk(output, frame, coordinates)

            output.release()

            if self.mode == 'sequence':
                chunk_validation_passed = self.__validate_chunk(chunk_path)

            if self.mode!='singleshot' and not chunk_validation_passed:
                self.broken_chunks.append(chunk_path)

                try:
                    os.remove(chunk_path)
                    log_msg = f"WARNING: BROKEN_CHUNK: {chunk_path}"
                except OSError:
                    log_msg = f"FAILED TO REMOVE: {chunk_path}"
                    pass

            else:
                self.valid_chunks_counter += 1

            if c.ENABLE_DEBUG_LOGGER:
                self.logger.debug(log_msg)


    def get_report(self):
            """Creates report from writer. Report content:
            - valid chunks counter
            - broken chunks counter
            - list of broken chunks

            Returns:
                OrderedDict: Availible keys: [
                    'Valid chunks total',
                    'Broken chunks total',
                    'Broken chunks list'
                    ]
            """
            report = OrderedDict()

            report['Valid chunks total'] = self.valid_chunks_counter
            report['Broken chunks total'] = len(self.broken_chunks)
            report['Broken chunks list'] = self.broken_chunks

            return report


    @staticmethod
    def __read_video(source_path):
        """Reads video source file.

        Args:
            source_path (str): Path to the source video

        Returns:
            cv2.VideoCapture: cv2 capture object
        """
        assert os.path.isfile(source_path), f'{source_path} is missing'

        video_capture = cv2.VideoCapture(source_path)

        return video_capture


    @staticmethod
    def __load_codec():
        """Loads codec for MJPG format.

        Returns:
            cv2.Codec: cv2 codec object
        """
        codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

        return codec


    def release(self):
        """Releases video capture to finish the job safely
        """
        self.capture.release()


    def __create_subdirs_for_each_class(self):
        """Creates output directories for every label class in script
        """
        available_classes = self.script['statistics']['classes'].keys()

        for label_class in available_classes:
            class_dir_path = os.path.join(self.output_path, label_class)

            if os.path.isdir(class_dir_path):
                pass
            else:
                os.mkdir(class_dir_path)


    def __get_chunk_path(self, num, frame_num, chunk):
        """Generates path to save new chunk. Filename format:
        {file}_{label_name}_{class_type}_{class_name}_tr{track_num}_
        seq{chunk_num}_fr{frame_num}.mjpg

        Args:
            num (int): Number of iterator step - unique for chunk
            frame_num (int): Number of center frame of sequence
            chunk (dict): Dict from extraction task script.

        Returns:
            str: Full path to file with class subdirectory
        """
        class_path = os.path.join(self.output_path, chunk['class'])

        file = self.source_name
        extension = 'mjpg'
        label_name = chunk['label']
        class_name = chunk['class']
        class_type = chunk['type']
        track_num = str.zfill(str(chunk['track']), 4)
        chunk_num = str.zfill(str(num), 4)
        frame_num = str.zfill(str(frame_num), 6)
        if class_type == 'singleshot':
            extension = 'jpg'

        chunk_name = \
            f"{file}_{label_name}_{class_type}_{class_name}_" \
            f"tr{track_num}_seq{chunk_num}_fr{frame_num}"

        chunk_path = os.path.join(class_path, f"{chunk_name}.{extension}")

        return chunk_path


    def __get_output(self, chunk_path):
        """Creates empty video output job to write chunk to.

        Args:
            chunk_path (str): Full path to new chunk

        Returns:
            cv2.VideoWriter: cv2 writer object
        """
        video_output = cv2.VideoWriter(
            chunk_path,
            self.codec,
            self.fps,
            self.resolution,
        )
        return video_output


    def __add_frame_to_chunk(self, output, frame, coordinates):
        """Adds specific frame from video capture to the cv2.VideoWriter
        object.

        Args:
            output (cv2.VideoWriter): cv2 writer object to write to
            frame (int): Target frame number
            coordinates (dict): Coordinates of box to crop image
        """
        self.capture.set(1, frame)
        _, image = self.capture.read()

        # Box coordinates from two points: (A[ax, ay], B[bx, by])
        ax, ay, bx, by = coordinates

        image_crop = image[ay:by, ax:bx]

        image_crop = self.__resize_image_with_fill(
            input_image=image_crop,
            output_image_resolution=c.EXTRACTOR_RESOLUTION
        )

        output.write(image_crop)


    def __validate_chunk(self, chunk_path) -> bool:
        """Chunk validator. Tries to read every frame from chunk and
        tests its availibility.

        Args:
            chunk_path (str): Full path to the tested chunk

        Returns:
            bool: If chunk is valid - True; else - False
        """
        capture = cv2.VideoCapture(chunk_path)

        for _ in range(self.chunk_size):
            frame_is_valid, __ = capture.read()

            if not frame_is_valid:
                break

        chunk_has_no_errors = frame_is_valid

        return chunk_has_no_errors


    @staticmethod
    def __resize_image_with_fill(input_image, output_image_resolution):
        """Resize image to the target resolution with saving aspect
        ratio and filling with black borders unknown parts.

        Args:
            input_image (array): Image to resize
            output_image_resolution (tuple): Width and heights in pixels

        Returns:
            array: Cropped and resized image. If needed - with borders.
        """
        assert all([dimension > 0 for dimension in input_image.shape])

        def get_image_borders(image_shape, output_image_resolution) -> tuple:
            """Subtask. Calculate borders size for cropped image.

            Args:
                image_shape (tuple): Image width and heights
                output_image_resolution (tuple): Width and heights in
                    pixels

            Returns:
                tuple: New borders for vertical and horizontal parts
            """
            vertical_border = 0
            horizontal_border = 0

            input_img_w = image_shape[0]
            input_img_h = image_shape[1]

            output_img_w = output_image_resolution[0]
            output_img_h = output_image_resolution[1]

            input_img_aspect_ratio = \
                input_img_w / input_img_h
            output_img_aspect_ratio = \
                output_img_w / output_img_h

            if output_img_aspect_ratio >= input_img_aspect_ratio:
                vertical_border = int(
                    ((output_img_aspect_ratio * input_img_h) - input_img_w) / 2
                )
            else:
                horizontal_border = int(
                    ((output_img_aspect_ratio * input_img_w) - input_img_h) / 2
                )

            borders = (vertical_border, horizontal_border)

            return borders

        border_v, border_h = \
            get_image_borders(input_image.shape, output_image_resolution)

        output_image = cv2.copyMakeBorder(
            input_image,
            border_v, border_v,
            border_h, border_h,
            cv2.BORDER_CONSTANT, 0
        )

        output_image = cv2.resize(output_image, output_image_resolution)

        return output_image



def start_writing_video_chunks(source, output, script, logger):
    """Starts process of writing video chunks from source file to output
    directory.

    Args:
        source (str): Path to source video file
        output (str): Path to root output directory
        script (dict): property of ExtractionTask from dataset
            generator main module
        logger (obj): logger object from main module
    """
    if c.ENABLE_DEBUG_LOGGER:
        log_msg = f"Writing to '{output}': " \
                  f"{len(script['chunks'])} chunks in file"
        logger.debug(log_msg)

    writer = ChunkWriter(source, output, script, logger)

    writer.write_chunks()
    writer.release()

    writer_report = writer.get_report()

    return writer_report
