"""
Module for Video Extraction.
Contains class VideoDirector which creates ExtractionScript
"""

from msilib import sequence
from utils import constants as c



class TrackAnalyzer:
    def __init__(self, track, overlay_policy):
        self.track = track
        self.overlay_policy = overlay_policy
        self.is_depleted = False

        self.seqences = []
        self.stopped_frames = set()

        self.__load_track()


    def __load_track(self):
        #self.track_frames = (t for t in self.track[''])
        self.track_id = self.track['@id']
        self.track_lable = self.track['@label']

        self.track_frames = {}


    def __find_sequence(self):
        seqence_class = 'idle'
        sequence = tuple([x for x in range(15)])

        new_sequence = {
            'class':seqence_class,
            'sequence':sequence
        }

        return new_sequence


    def add_sequence(self):
        self.seqences.append(self.__find_sequence())

        self.sequence_number = len(self.seqences)
        self.is_depleted = True



def get_script(extraction):
    extraction_status = \
        extraction.info is not None and \
        extraction.annotation_tracks is not None
    assert extraction_status, "Extraction was not initialized properly"

    script = {}

    script['source_name'] = extraction.info['source_name']

    script['script_settings'] = read_script_settings()

    script['chunks'] = get_script_chunks(
        tracks=extraction.annotation_tracks,
        overlay_policy=script['script_settings']['classes_overlay']
    )

    return script



def read_script_settings():
    settings = {}

    labels_and_attributes = \
        {key:value for (key,value) in c.TARGET_ATTRIBUTES.items()}

    settings['target_attributes'] = labels_and_attributes
    settings['base_class'] = c.BASE_CLASS
    settings['classes_overlay'] = c.CLASS_OVERLAY
    settings['frame_step'] = c.FRAME_STEP

    return settings



def get_script_chunks(tracks, overlay_policy):
    chunks = []

    for track in tracks:
        analyst = TrackAnalyzer(
            track=track,
            overlay_policy=overlay_policy
        )

        while not analyst.is_depleted:
            analyst.add_sequence()

        for sequence in analyst.seqences:
            new_chunk = {
                'track':analyst.track_id,
                'lable':analyst.track_lable,
                'class':sequence['class'],
                'sequence':sequence['sequence']
            }
            chunks.append(new_chunk)

    test_chunk = {
        'track':0,
        'lable':'Vehicle',
        'class':'idle',
        'sequence':{
            'frame':1,
            'box':{
                'A':(100,100),
                'B':(150,150),
            }
        }
    }

    chunks.append(test_chunk)

    return tuple(chunks)





def write_video(file, script):
    pass
