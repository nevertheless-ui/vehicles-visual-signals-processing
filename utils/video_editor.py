"""
Module for Video Extraction.
Contains class VideoDirector which creates ExtractionScript
"""

from utils import constants as c



class TrackAnalyzer:
    def __init__(self, track, overlay_policy):
        self.track = track
        self.overlay_policy = overlay_policy
        self.is_depleted = False

        self.__load_track()


    def __load_track(self):
        #self.track_frames = (t for t in self.track[''])
        print(self.track['frame'])
        self.is_depleted = True
        pass



    def search_sequence(self):
        pass



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
            analyst.search_sequence()

    test_chunk = {
        'track':0,
        'lable':'Vehicle',
        'class':'idle',
        'sequence':tuple({
            'frame':1,
            'box':{
                'A':(100,100),
                'B':(150,150),
            },
            'attributes':{
                'alarm':False,
                'brake':False,
                'turn_left':False,
                'turn_right':False,
            }
        })
    }

    chunks.append(test_chunk)

    return tuple(chunks)





def write_video(file, script):
    pass
