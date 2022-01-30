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
        self.last_frame = 0

        self.min_track_size = self.__get_slice_size_for_chunk()

        self.sequences = []

        self.__load_track()
        self.__get_markers()

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
            if box['@outside'] != '1':
                attributes = OrderedDict()
                frame_number = int(box['@frame'])
                coordinates = self.__get_coordinates(box)

                if frame_number > self.last_frame:
                    self.last_frame = frame_number

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


    def __get_markers(self):
        self.markers = OrderedDict()
        previous_attrib_states = OrderedDict()

        for attribute in self.attributes:
            if attribute in self.target_attributes:
                self.markers[attribute] = OrderedDict()
                previous_attrib_states[attribute] = None

        self.markers[c.BASE_CLASS] = OrderedDict()
        previous_attrib_states[c.BASE_CLASS] = None

        self.__add_markers(previous_attrib_states)


    def __add_markers(self, previous_attrib_states):
        target_attribs = [attrib for attrib in self.target_attributes]
        target_attribs.append(c.BASE_CLASS)

        for frame_number, metadata in self.track_frames.items():
            states = metadata['attributes']
            if not any([state=='true' for state in states.values()]):
                states[c.BASE_CLASS] = 'true'
            else:
                states[c.BASE_CLASS] = 'false'

            self.__evaluate_frame(frame_number, states,
                                  previous_attrib_states,
                                  target_attribs)

            for attribute, state in states.items():
                previous_attrib_states[attribute] = state


    def __evaluate_frame(self, frame_number, states,
                         previous_attrib_states,
                         target_attribs):

        for attrib, state in states.items():
            if attrib in target_attribs:

                previous_state = previous_attrib_states[attrib]
                is_last_frame = (frame_number == self.last_frame)

                if (previous_state == state) and \
                   (frame_number != self.last_frame):
                    continue

                elif (previous_state != state) or is_last_frame:
                    self.__mark_frame(
                        attrib,
                        frame_number,
                        state,
                        previous_state
                    )


    def __mark_frame(self, attrib, frame_number, state, previous_state):

        first_frame = \
            (previous_state is None) and (state == 'true')
        last_frame = \
            (frame_number == self.last_frame) and (state == 'true')
        start_frame = \
            (previous_state == 'false') and (state == 'true')
        end_frame = \
            (previous_state == 'true') and (state == 'false')

        if first_frame or start_frame:
            self.markers[attrib][frame_number] = 'start_frame'
        elif end_frame:
            self.markers[attrib][frame_number - 1] = 'end_frame'
        elif last_frame:
            self.markers[attrib][frame_number] = 'end_frame'


    def generate_sequences(self, add_reversed):
        if len(self.track_frames) < self.min_track_size:
            self.is_depleted = True

        else:
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


    @staticmethod
    def __get_chunk_indexes(frame): # calculate sequence
        pass


    @staticmethod
    def __test_frame_availibility(frames): # test for availibility
        pass


    @staticmethod
    def __test_frame_status_integrity(frames): # test for availibility
        pass
