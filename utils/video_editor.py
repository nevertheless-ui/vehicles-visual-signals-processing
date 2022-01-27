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

        self.min_track_size = self.__get_slice_size_for_chunk()

        self.sequences = []
        self.used_frames = set()
        self.markers = OrderedDict()

        self.__load_track()

        if self.target_attributes:
            self.__get_attribute_markers()

        #for key, val in self.markers.items():
            #print(key, val)



    def __len__(self):
         return len(self.sequences)


    @staticmethod
    def __get_slice_size_for_chunk():
        return ((c.CHUNK_SIZE - 1) * c.FRAME_STEP) + 1


    def __load_track(self):
        self.track_id = self.track_data['@id']
        self.track_label = self.track_data['@label']
        self.attributes = self.labels[self.track_label]

        self.target_attributes = \
            self.settings['target_attributes'][self.track_label]

        self.track_frames = OrderedDict()

        for box in self.track_data['box']:
            attributes = OrderedDict()
            frame_number = box['@frame']
            coordinates = self.__get_coordinates(box)

            if 'attribute' in box.keys():
                attributes = {x['@name']:x['#text'] for x in box['attribute']}

            self.track_frames[frame_number] = {
                'coordinates':coordinates,
                'attributes':attributes,
            }


    @staticmethod
    def __get_coordinates(box):
        def convert_coordinate(coordinate):
            assert isinstance(coordinate, str)
            return int(float(coordinate))

        a_x, a_y, b_x, b_y = (
            convert_coordinate(box['@xtl']),
            convert_coordinate(box['@ytl']),
            convert_coordinate(box['@xbr']),
            convert_coordinate(box['@ybr']),
        )

        coordinates = {
            'tl':(a_x, a_y),
            'tr':(b_x, a_y),
            'bl':(a_x, b_y),
            'br':(b_x, b_y),
        }

        return coordinates


    def __get_attribute_markers(self):
        previous_attribute_states = OrderedDict()

        for attribute in self.attributes:
            if attribute in self.target_attributes:
                self.markers[attribute] = OrderedDict()
                previous_attribute_states[attribute] = None

        if self.markers:
            for frame_number, metadata in self.track_frames.items():
                self.__evaluate_frame(frame_number, metadata,
                                    previous_attribute_states)

                for attribute, state in metadata['attributes'].items():
                    previous_attribute_states[attribute] = state

        else:
            pass


    def __evaluate_frame(self, frame_number, metadata,
                         previous_attribute_states):

        for attribute, state in metadata['attributes'].items():
            if attribute in self.target_attributes:

                if previous_attribute_states[attribute] == state:
                    continue

                elif previous_attribute_states[attribute] != state:
                    self.__mark_frame(
                        attribute,
                        frame_number,
                        previous_attribute_states[attribute]
                    )


    def __mark_frame(self, attribute, frame_number, previous_state):

        if previous_state is not None:
            # WARNING: Default attribute's type in annotation is STRING.
            if previous_state == 'false':
                self.markers[attribute][frame_number] = 'start_frame'

            elif previous_state == 'true':
                self.markers[attribute][frame_number] = 'end_frame'

        else:
            pass


    def generate_sequences(self):
        if len(self.track_frames) < self.min_track_size:
            self.is_depleted = True

        else:
            sequence_class = c.BASE_CLASS
            sequence_frames = {}
            for x in [x for x in range(self.min_track_size)]:
                sequence_frames[str(x)] = {
                'tl':(1, 1),
                'tr':(2, 1),
                'bl':(1, 2),
                'br':(2, 2),
            }

            new_sequence = tuple((sequence_class, sequence_frames))

            self.sequences.append(new_sequence)

            self.is_depleted = True


    def __get_base_class(self):
        pass


    def __get_target_class(self):
        pass



def get_chunks(tracks, settings, labels):
    chunks = []

    for track in tracks:
        analyst = TrackAnalyzer(track, settings, labels)
        analyst.generate_sequences()

        for sequence_class, sequence_frames in analyst.sequences:
            new_chunk = {
                'track':analyst.track_id,
                'label':analyst.track_label,
                'class':sequence_class,
                'sequence':sequence_frames
            }
            chunks.append(new_chunk)

    return tuple(chunks)



def read_script_settings():
    settings = {}
    labels_and_attributes = \
        {key:value for (key,value) in c.TARGET_ATTRIBUTES.items()}

    settings['target_attributes'] = labels_and_attributes
    settings['base_class'] = c.BASE_CLASS
    settings['classes_overlay'] = c.CLASS_OVERLAY
    settings['chunks_size'] = c.CHUNK_SIZE

    return settings



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
