# Main module of the project for vehicle signals recognition
# Author: Filippenko Artyom, 2021
# MISIS Master Degree Project
# Created: 2021.12.11
# Modified: 2021.12.11

from utils import extractor
from utils import constants as c


def main():
    extractor.get_chunks_from_ts_data(DATAPATH=c.DATA_DIR_PATH, СHUNK_DURATION=c.VIDEO_CHUNK_SIZE)


if __name__ == '__main__':
    main()
