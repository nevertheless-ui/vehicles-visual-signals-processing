"""
Module for Video Writing.
Read video and generates chunks from script description.
"""

import os

from utils import constants as c



def write_chunks(output, script):
    print(f"Writing to {output}: {len(script['chunks'])} chunks in file")
