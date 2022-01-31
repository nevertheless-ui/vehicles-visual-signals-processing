from collections import OrderedDict

from utils import constants as c



class TrackAnalyzer:
    def __init__(self, track, settings, labels, frames_total):
        self.track_data = track
        self.overlay_policy = c.CLASS_OVERLAY
        self.chunk_size = c.CHUNK_SIZE
        self.is_depleted = False
        self.settings = settings
        self.labels = labels

        self.last_frame = 0
        self.first_frame = int(frames_total)

        self.min_track_size = self.__get_slice_size_for_chunk()

        self.sequences = []

        self.__load_track()
        self.__get_markers()

        for key, val in self.markers.items():
            print(key, val)


    def __len__(self) -> int:
         return len(self.sequences)


    @staticmethod
    def __get_slice_size_for_chunk() -> int:
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

                if frame_number < self.first_frame:
                    self.first_frame = frame_number

                if 'attribute' in box.keys():
                    attributes = {x['@name']:x['#text']
                                  for x in box['attribute']}

                self.track_frames[frame_number] = {
                    'coordinates':coordinates,
                    'attributes':attributes,
                }


    @staticmethod
    def __get_coordinates(box) -> dict:

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
                        print(attrib, frame_number, (previous_state, '>', state))
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
                for frame, marker_type in frames.items():
                    if marker_type=='start_frame':
                        self.__get_target_class(frame, marker_type,
                                                attrib, add_reversed)

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


    def __get_target_class(self, frame, marker_type,
                           attrib, add_reversed):
        chunk_status = 'drop'

        chunk_indexes = \
            self.__get_chunk_indexes(frame)

        indexes_are_avalible = \
            self.__test_frames_availibility(chunk_indexes)

        if indexes_are_avalible:
            chunk_status = \
                self.__test_frame_status_integrity(frame, attrib, marker_type,
                                                   chunk_indexes)
            print(attrib, frame, marker_type, chunk_indexes, chunk_status)

        # check_status


        #self.track_frames[frame]

        #new_sequence = (sequence_class, sequence_frames)
        #new_sequence = tuple(new_sequence)

        #self.sequences.append(new_sequence)
        pass


    @staticmethod
    def __get_chunk_indexes(frame) -> list:
        def get_shifts(frame, steps):
            left, right = [], []
            for i in range(1, steps + 1):
                left.append(frame + (c.FRAME_STEP * -i))
            for i in range(1, steps + 1):
                right.append(frame + (c.FRAME_STEP * i))
            return sorted(left), sorted(right)

        added_size = c.CHUNK_SIZE - 1
        steps = int(added_size / 2)
        left, right = get_shifts(frame, steps)
        frames = left + [frame] + right

        return frames


    def __test_frames_availibility(self, frames) -> bool:
        return all([(idx in self.track_frames.keys()) for idx in frames])


    def __test_frame_status_integrity(self, frame, attrib,
                                      marker_type, frames):
        chunk_status = 'failed'

        start_frame, end_frame = \
            frames[0], frames[-1]
        subframes = list(range(start_frame, end_frame + 1, 1))
        print(subframes, len(subframes))

        if attrib != c.BASE_CLASS:
            chunk_status = \
                self.__evaluate_attrib_frames(frame, attrib,
                                              marker_type, subframes)

        elif attrib == c.BASE_CLASS:
            status_is_stable = \
                self.__check_slice_attrib_status(attrib, subframes, 'true')

            if status_is_stable: chunk_status = 'passed'

        return chunk_status


    def __evaluate_attrib_frames(self, frame, attrib,
                                 marker_type, frames) -> str:
        chunk_status = 'failed'

        if marker_type=='start_frame':
            left_frames, right_frames = \
                self.__get_attrib_slice(marker_type, frame, frames)

            left_is_false, right_is_true = (
                self.__check_slice_attrib_status(attrib, left_frames, 'false'),
                self.__check_slice_attrib_status(attrib, right_frames, 'true')
            )

            if left_is_false and right_is_true: chunk_status = 'passed'

        elif marker_type=='end_frame':
            left_frames, right_frames = \
                self.__get_attrib_slice(marker_type, frame, frames)

            left_is_true, right_is_false = (
                self.__check_slice_attrib_status(attrib, left_frames, 'true'),
                self.__check_slice_attrib_status(attrib, right_frames, 'false')
            )

            if left_is_true and right_is_false: chunk_status = 'passed'

        return chunk_status


    @staticmethod
    def __get_attrib_slice(marker_type, frame, frames) -> tuple:
        center_idx = frames.index(frame)

        if marker_type=='end_frame': center_idx += 1

        left_slice = frames[:center_idx]
        right_slice = frames[center_idx:]

        return left_slice, right_slice


    def __check_slice_attrib_status(self, attrib,
                                    frames, target_value) -> bool:
        slice_status = \
            all([self.track_frames[frame]['attributes'][attrib]==target_value
                 for frame in frames])

        return slice_status
