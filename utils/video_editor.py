"""
Module for Video Extraction.
Contains class TrackAnalyzer which generates script for video chunks extractions
Each chunk contains data of source, lable, class and attributes
"""

from collections import OrderedDict
from utils import constants as c



class TrackAnalyzer:
    def __init__(self, track, settings, labels):
        self.track_data = track
        self.overlay_policy = c.CLASS_OVERLAY
        self.chunk_size = c.CHUNK_SIZE
        self.is_depleted = False
        self.settings = settings
        self.labels = labels

        self.sequences = []
        self.stopped_frames = set()
        self.markers = OrderedDict()

        self.__load_track()

        if self.target_attributes:
            self.__get_attribute_markers()

        #for key, val in self.markers.items():
            #print(key, val)



    def __len__(self):
         return len(self.sequences)


    def __load_track(self):
        self.track_id = self.track_data['@id']
        self.track_label = self.track_data['@label']
        self.attributes = self.labels[self.track_label]

        self.target_attributes = \
            self.settings['target_attributes'][self.track_label]

        self.track_frames = OrderedDict()

        for box in self.track_data['box']:
            attributes = {}
            frame_number = box['@frame']
            a_x, a_y = box['@xtl'], box['@ytl']
            b_x, b_y = box['@xbr'], box['@ybr']

            if 'attribute' in box.keys():
                attributes = {x['@name']:x['#text'] for x in box['attribute']}

            self.track_frames[frame_number] = {
                'A':{'x':a_x, 'y':a_y},
                'B':{'x':b_x, 'y':b_y},
                'attributes':attributes
            }


    def __get_attribute_markers(self):
        previous_attribute_state = OrderedDict()

        for attribute in self.attributes:
            if attribute in self.target_attributes:
                self.markers[attribute] = OrderedDict()
                previous_attribute_state[attribute] = None

        if self.markers:
            for frame_number, metadata in self.track_frames.items():
                self.__evaluate_frame(frame_number, metadata,
                                    previous_attribute_state)

                for attribute, state in metadata['attributes'].items():
                    previous_attribute_state[attribute] = state

        else:
            pass


    def __evaluate_frame(self, frame_number, metadata,
                         previous_attribute_state):
        for attribute, state in metadata['attributes'].items():

            if attribute in self.target_attributes:

                if previous_attribute_state[attribute] == state:
                    continue

                elif previous_attribute_state[attribute] != state:

                    if previous_attribute_state[attribute] is not None:

                        # WARNING: Default attribute's type in annotation is STRING. Be advised!
                        if previous_attribute_state[attribute] == 'false':
                            self.markers[attribute][frame_number] = 'start_frame'
                        if previous_attribute_state[attribute] == 'true':
                            self.markers[attribute][frame_number] = 'end_frame'

                    else:
                        continue


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
    script['chunks'] = get_chunks(
        tracks=extraction.annotation_tracks,
        settings=script['script_settings'],
        labels=extraction.info['labels']
    )

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



def get_chunks(tracks, settings, labels):
    chunks = []

    for track in tracks:
        analyst = TrackAnalyzer(track, settings, labels)

        while not analyst.is_depleted:
            analyst.add_sequence()

        for sequence_class, sequence_frames in analyst.sequences:
            new_chunk = {
                'track':analyst.track_id,
                'label':analyst.track_label,
                'class':sequence_class,
                'sequence':sequence_frames
            }
            chunks.append(new_chunk)

    return tuple(chunks)



def write_video(input_path, output_path, script):
    pass
