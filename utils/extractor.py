# Module for extraction video data of objects from video files
# Author: Filippenko Artyom, 2021
# MISIS Master Degree Project
# Created: 2021.12.11
# Modified: 2021.12.14
# TODO - add FPS ratio for convertion


import cv2
import os
import shutil
import xmltodict

from tqdm.auto import tqdm
from zipfile import ZipFile
from glob import glob

import constants as c

def create_dir(dir_name):
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)


def generate_filename_suffix(track, f_counter=0):
    assert isinstance(f_counter, int), "No counter passed to func"

    track_num = str.zfill(str(track), 4)
    chunk_num = str.zfill(str(f_counter), 4)

    return f'{track_num}_{chunk_num}'


def capture_info(vid_capture):
    if (vid_capture.isOpened() == False):
        print("Error! File is not opened.")

    else:
        fps = int(vid_capture.get(5))
        frame_count = int(vid_capture.get(7))
        height_param = int(vid_capture.get(4))
        width_param = int(vid_capture.get(3))
        resolution = (width_param, height_param)
        file_duration = int(frame_count/fps)

        print(f"Video resolution: {width_param}x{height_param}")
        print(f"Frame rate: {fps} fps")
        print(f"Frame count: {frame_count} frames")
        print(f"File duration: {file_duration} sec.")

        return fps, resolution, frame_count


def update_output_file_param(f_name, f_format, f_name_suffix, fps, codec, resolution):
    output_file_name = (f'{f_name}_{f_name_suffix}.{f_format}')
    video_output = cv2.VideoWriter(
        output_file_name,
        codec,
        fps,
        resolution,
    )
    return video_output


def resize_image_with_fill(image, target_image_resolution):
    border_v = 0
    border_h = 0
    img_w, img_h = image.shape[0], image.shape[1]
    aspect_ratio = \
        target_image_resolution[0] / target_image_resolution[1]

    if aspect_ratio >= (img_w/img_h):
        border_v = int(((aspect_ratio*img_h)-img_w)/2)
    else:
        border_h = int(((aspect_ratio*img_w)-img_h)/2)

    image = cv2.copyMakeBorder(image, border_v, border_v,
                               border_h, border_h,
                               cv2.BORDER_CONSTANT, 0)
    image = cv2.resize(image, target_image_resolution)

    return image


def get_annotation(annotations):
    annotation_file_path = annotations[0]
    with ZipFile(annotation_file_path) as zipfile:
        with zipfile.open('annotations.xml') as xml_file:
            video_annotation = xmltodict.parse(xml_file.read())
    return video_annotation


def create_chunk_subdir(DATAPATH, VIDEO_FILE_NAME):
    NEW_DIR_NAME = f"{VIDEO_FILE_NAME}_chunks"
    NEW_CHUNK_NAME = f"{VIDEO_FILE_NAME}_chunk"
    NEW_DIR_PATH = os.path.join(DATAPATH, NEW_DIR_NAME)
    NEW_CHUNK_PATH = os.path.join(NEW_DIR_PATH, NEW_CHUNK_NAME)

    if os.path.exists(NEW_DIR_PATH) and os.path.isdir(NEW_DIR_PATH):
        shutil.rmtree(NEW_DIR_PATH)
    os.mkdir(NEW_DIR_PATH)
    return NEW_DIR_PATH, NEW_CHUNK_PATH


def extract_chunks_from_video(DATAPATH, VIDEO_FILE_NAME, annotations,
                              RESOLUTION=c.EXTRACTOR_RESOLUTION):
    _, NEW_CHUNK_PATH = create_chunk_subdir(DATAPATH, VIDEO_FILE_NAME)
    CHANGE_FPS_FLAG = False
    FPS_RATIO = 1.0

    video_capture = cv2.VideoCapture(os.path.join(DATAPATH, VIDEO_FILE_NAME))
    codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    FPS, _ , _ = capture_info(video_capture)
    VIDEO_CHUNK_DURATION = FPS * c.VIDEO_CHUNK_SIZE

    if FPS != c.TARGET_FPS:
        print('Source and target FPS are not the same')
        FPS_RATIO = c.TARGET_FPS / FPS


    video_annotation = get_annotation(annotations)

    for track in tqdm(video_annotation['annotations']['track'], desc='Tracks processing'):
        TRACK_LENGTH = len(track['box'])
        MAX_CHUNKS = TRACK_LENGTH//VIDEO_CHUNK_DURATION

        if MAX_CHUNKS == 0:
            print(f"Not enough data for cut from {VIDEO_FILE_NAME}" \
                  f" on track #{track['@id']}...")
            continue
        else:
            CHUNK_NUM = 0
            TMP_CHUNK_DURATION = 0
            EARLY_STOP = False

            for num, annotation_data in enumerate(track['box']):
                TMP_CHUNK_DURATION += 1

                assert TMP_CHUNK_DURATION <= VIDEO_CHUNK_DURATION, \
                    f"{VIDEO_FILE_NAME} - track {track} chunk size " \
                    f"{TMP_CHUNK_DURATION}. Must be less or equial {VIDEO_CHUNK_DURATION}"

                if len(track['box'][num:]) < VIDEO_CHUNK_DURATION:
                    EARLY_STOP = True

                if not EARLY_STOP:
                    if TMP_CHUNK_DURATION == 1:
                        chunk_suffix = generate_filename_suffix(track['@id'], CHUNK_NUM)

                        video_output = update_output_file_param(
                            NEW_CHUNK_PATH, 'mjpg', chunk_suffix,
                            FPS, codec, RESOLUTION)

                    PREVIOUS_FRAME_NUM = int(annotation_data['@frame']) - 1

                    FRAME_NUM = int(annotation_data['@frame'])
                    FRAMES_BREAK_FLAG = \
                        (abs(FRAME_NUM - PREVIOUS_FRAME_NUM) > c.SKIP_FRAME_NUM) and \
                        (TMP_CHUNK_DURATION < VIDEO_CHUNK_DURATION)
                    LAST_FRAME_FLAG = \
                        (TMP_CHUNK_DURATION == VIDEO_CHUNK_DURATION)

                    if FRAMES_BREAK_FLAG:
                        TMP_CHUNK_DURATION = 0
                        video_output.release()
                        shutil.rmtree(NEW_CHUNK_PATH)
                        continue
                    else:
                        box_coordinate_tags = ['@xtl', '@ytl',
                                               '@xbr', '@ybr']

                        # Box coordinates: (A[ax, ay], B[bx, by])
                        ax, ay, bx, by = \
                            tuple(round(float(annotation_data[i])) for i in box_coordinate_tags)

                        video_capture.set(1, int(annotation_data['@frame']))
                        _, frame = video_capture.read()

                        image_box = frame[ay:by, ax:bx]
                        image_box = resize_image_with_fill(image_box, c.EXTRACTOR_RESOLUTION)

                        video_output.write(image_box)

                    if LAST_FRAME_FLAG:
                        CHUNK_NUM += 1
                        TMP_CHUNK_DURATION = 0
                        video_output.release()

                else:
                    break
    video_capture.release()


def get_chunks_from_ts_data(DATAPATH, CHUNK_DURATION):
    print(f"Link to working directory:\n{DATAPATH}"
            f"\nChunk size: {CHUNK_DURATION} sec.")

    for video_file_path in tqdm(glob(os.path.join(DATAPATH, f'*.ts')),
                                desc='Video files processing'):
        if not os.path.isfile(video_file_path):
            continue

        else:
            VIDEO_FILE_NAME = os.path.basename(video_file_path)
            ANNOTATION_FILE_MASK = \
                os.path.join(DATAPATH, f'task_{os.path.basename(VIDEO_FILE_NAME)}*.zip')

            annotations = glob(ANNOTATION_FILE_MASK)

            assert len(annotations) < 2, \
                f"{VIDEO_FILE_NAME} has confisuing annotation archive name:" \
                f" {len(annotations)} files found."

            if len(annotations) == 0:
                print(f'No annotation for "{VIDEO_FILE_NAME}". Skipping...')
                pass

            else:
                extract_chunks_from_video(DATAPATH, VIDEO_FILE_NAME, annotations)

if __name__ == '__main__':
    get_chunks_from_ts_data(DATAPATH=c.DATA_DIR_PATH,
                            CHUNK_DURATION=c.VIDEO_CHUNK_SIZE)
