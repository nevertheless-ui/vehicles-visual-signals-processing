"""
Module for Video Extraction.
Contains class VideoDirector which creates ExtractionScript
"""

from utils import constants as c



class TrackAnalyzer:
    def __init__(self, track):
        self.track_data = track
        self.overlay_policy = c.CLASS_OVERLAY
        self.chunk_size = c.CHUNK_SIZE
        self.is_depleted = False

        self.sequences = []
        self.stopped_frames = set()

        self.__load_track()
        self.__get_attribute_markers()


    def __len__(self):
         return len(self.sequences)


    def __load_track(self):
        self.track_id = self.track_data['@id']
        self.track_lable = self.track_data['@label']

        self.track_frames = {}

        for box in self.track_data['box']:
            frame_number = box['@frame']
            a_x, a_y = box['@xtl'], box['@ytl']
            b_x, b_y = box['@xbr'], box['@ybr']
            attributes = {}

            if 'attribute' in box.keys():
                attributes = {x['@name']:x['#text'] for x in box['attribute']}

            self.track_frames[frame_number] = {
                'A':{'x':a_x, 'y':a_y},
                'B':{'x':b_x, 'y':b_y},
                'attributes':attributes
            }


    def __get_attribute_markers(self):
        pass


    def __generate_next_sequence(self):
        sequence_class = c.BASE_CLASS
        sequence_frames = tuple([x for x in range(c.CHUNK_SIZE)])

        return sequence_class, sequence_frames


    def add_sequence(self):
        if self.is_depleted:
            pass

        else:
            self.sequences.append(self.__generate_next_sequence())
            self.is_depleted = True



def get_script(extraction):
    extraction_status = \
        extraction.info is not None and \
        extraction.annotation_tracks is not None
    assert extraction_status, "Extraction was not initialized properly"

    script = {}

    script['source_name'] = extraction.info['source_name']
    script['script_settings'] = read_script_settings()
    script['chunks'] = get_chunks(tracks=extraction.annotation_tracks)

    return script



def read_script_settings():
    settings = {}

    labels_and_attributes = \
        {key:value for (key,value) in c.TARGET_ATTRIBUTES.items()}

    settings['target_attributes'] = labels_and_attributes
    settings['base_class'] = c.BASE_CLASS
    settings['classes_overlay'] = c.CLASS_OVERLAY
    settings['chunks_size'] = c.CHUNK_SIZE

    return settings



def get_chunks(tracks):
    chunks = []

    for track in tracks:
        analyst = TrackAnalyzer(track)

        while not analyst.is_depleted:
            analyst.add_sequence()

        for sequence_class, sequence_frames in analyst.sequences:
            new_chunk = {
                'track':analyst.track_id,
                'lable':analyst.track_lable,
                'class':sequence_class,
                'sequence':sequence_frames
            }
            chunks.append(new_chunk)

    return tuple(chunks)



def write_video(input_path, output_path, script):
    pass
