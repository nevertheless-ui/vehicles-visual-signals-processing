"""
Module for Video Extraction.
Contains class TrackAnalyzer which generates script for video chunks extractions
Each chunk contains data of source, lable, class and attributes
"""

from collections import OrderedDict
from utils import constants as c



class TrackAnalyzer:
    def __init__(self, track, settings, labels):
        print("***")
        self.track_data = track
        self.overlay_policy = c.CLASS_OVERLAY
        self.chunk_size = c.CHUNK_SIZE
        self.is_depleted = False
        self.settings = settings
        self.labels = labels

        self.min_track_size = self.__get_slice_size_for_chunk()

        self.sequences = []
        self.markers = OrderedDict()

        self.__load_track()

        if self.target_attributes:
            self.__get_attribute_markers()
        self.__get_base_markers()

        for key, val in self.markers.items():
            print(key, val)


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
            if box['@outside'] != '1':
                attributes = OrderedDict()
                frame_number = int(box['@frame'])
                coordinates = self.__get_coordinates(box)

                if 'attribute' in box.keys():
                    attributes = {x['@name']:x['#text']
                                  for x in box['attribute']}

                self.track_frames[frame_number] = {
                    'coordinates':coordinates,
                    'attributes':attributes,
                }


    @staticmethod
    def __get_coordinates(box):

        def convert_str_to_int(*args):
            assert len(args) == 4

            converted_coordinates = \
                tuple(int(float(coordinate)) for coordinate in args)

            return converted_coordinates

        a_x, a_y, b_x, b_y = convert_str_to_int(
            box['@xtl'], box['@ytl'], box['@xbr'], box['@ybr']
        )

        coordinates = {
            'tl':(a_x, a_y), 'tr':(b_x, a_y),
            'bl':(a_x, b_y), 'br':(b_x, b_y),
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


    def __get_base_markers(self):
        markers = OrderedDict()
        print("Get base", self.track_frames.keys())

        track_frames = list(self.track_frames.keys())
        if not any(len(markers) > 0 for markers in self.markers.values()):
            self.__add_base_markers_for_empty_track(markers, track_frames)

        else:
            self.__add_base_markers_for_complex_track(markers, track_frames)

        self.markers[c.BASE_CLASS] = markers


    def __add_base_markers_for_empty_track(self, markers, track_frames):
        if track_frames:
            start_frame_idx, end_frame_idx = \
                track_frames[0], track_frames[-1]

            markers[start_frame_idx] = 'start_frame'
            markers[end_frame_idx] = 'end_frame'


    def __add_base_markers_for_complex_track(self, markers, track_frames):
        non_empty_classes = set(
            class_label for class_label, records in self.markers.items() \
            if len(records) > 0
        )
        self.__drop_frames_with_signals(track_frames, non_empty_classes)

        track_frames.sort()

        if track_frames:
            self.__mark_base_frames(markers, track_frames)


    def __drop_frames_with_signals(self, track_frames, non_empty_classes):
        for frame_num, metadata in self.track_frames.items():
            if any(tuple(value=='true' for attrib, value
                         in metadata['attributes'].items()
                         if attrib in non_empty_classes)
                ):
                idx_to_pop = track_frames.index(frame_num)
                track_frames.pop(idx_to_pop)


    def __mark_base_frames(self, markers, track_frames):
        start_frame_idx = track_frames[0]
        end_frame_idx = track_frames[-1]

        for num, frame_idx in enumerate(track_frames):
            if track_frames[num] == start_frame_idx:
                markers[start_frame_idx] = 'start_frame'

            elif track_frames[num] == end_frame_idx:
                markers[end_frame_idx] = 'end_frame'

            elif frame_idx != (track_frames[num - 1] + 1):
                previouse_frame_idx = track_frames[num - 1]
                markers[previouse_frame_idx] = 'end_frame'
                markers[frame_idx] = 'start_frame'


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
                self.markers[attribute][frame_number - 1] = 'end_frame'

        else:
            pass


    def generate_sequences(self, add_reversed):
        if len(self.track_frames) < self.min_track_size:
            self.is_depleted = True

        else:
            print(self.markers.items())
            for attrib, frames in self.markers.items():
                for frame, frame_type in frames.items():
                    if frame_type=='start_frame':
                        self.__get_target_class(frame, attrib, add_reversed)

            #while not self.is_depleted:

            sequence_class = c.BASE_CLASS
            sequence_frames = OrderedDict()
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


    def __get_target_class(self, frame, attrib, add_reversed):
        # calculate sequence
        # test for availibility
        # check_status


        #self.track_frames[frame]

        #new_sequence = (sequence_class, sequence_frames)
        #new_sequence = tuple(new_sequence)

        #self.sequences.append(new_sequence)
        pass


    def __get_base_class(self, frame, attrib, add_reversed):
        pass


    @staticmethod
    def __get_chunk_indexes(frame): # calculate sequence
        pass


    @staticmethod
    def __test_frame_availibility(frames): # test for availibility
        pass


    @staticmethod
    def __test_frame_status_integrity(frames): # test for availibility
        pass


def get_chunks(tracks, settings, labels):
    chunks = []

    for track in tracks:
        analyst = TrackAnalyzer(track, settings, labels)
        analyst.generate_sequences(add_reversed=c.ADD_REVERSED)

        print(analyst.track_id)

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
