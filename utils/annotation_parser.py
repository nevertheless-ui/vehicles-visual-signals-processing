import os
import xmltodict

from zipfile import ZipFile



def get_annotation(annotation_path):
    assert os.path.isfile(annotation_path), f"No {annotation_path} in directory"
    
    with ZipFile(annotation_path) as zipfile:
        with zipfile.open('annotations.xml') as xml_file:
            video_annotation = xmltodict.parse(xml_file.read())
    return video_annotation
