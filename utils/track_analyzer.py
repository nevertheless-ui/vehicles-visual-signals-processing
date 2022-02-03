"""Analyzer for track in video annotation.
Do not use directly. Must be called from 'video_editor' module
"""
from collections import OrderedDict

from utils import constants as c



class TrackAnalyzer:
    def __init__(self, track, settings, labels, frames_total):
        """Analyzer class for track in video annotation.
        Do not use directly. Must be called from 'video_editor' module.
        Basic track analysis starts after initialization in automatic
        mode.

        DOESN'T WORK WITH VIDEO FILE.

        Basic workflow of class usage:

        - Initialize class:
            - track - track data from annotation parser
            - settings - script settings from video editor
            - labels - labels info from extraction task
            - frames_total - frames number in video
        1. Call method "generate_sequences()" to create attribute
            'sequences'
        2. Iterate over attribute 'sequences' to collect data for
            chunks
        """
        self.track_data = track
        self.overlay_policy = c.CLASS_OVERLAY
        self.chunk_size = c.CHUNK_SIZE
        self.is_depleted = False
        self.settings = settings
        self.labels = labels

        self.last_frame = 0
        self.first_frame = int(frames_total)
        self.frames_in_chunk = self.__get_slice_size_for_chunk()
        self.dynamic_types = ('start_frame', 'end_frame')
        self.static_types = ('static_frame')

        self.sequences = OrderedDict()

        self.__load_track()
        self.__find_dynamic_markers()
        self.__find_static_markers(c.BASE_CLASS)

        self.show_debug()


    def show_debug(self):
        print(self.track_id)
        for key, val in self.dynamic_markers.items():
            print(key, val)
        for key, val in self.static_markers.items():
            print(key, val)
        for key, val in self.sequences.items():
            print(key, val)


    def __len__(self) -> int:
        total_chunk_count = 0
        for chunks in self.sequences.values():
            total_chunk_count += len(chunks)

        return total_chunk_count


    @staticmethod
    def __get_slice_size_for_chunk() -> int:
        slice_size = ((c.CHUNK_SIZE - 1) * c.FRAME_STEP) + 1

        return slice_size


    @staticmethod
    def __get_side_size_for_chunk() -> int:
        slice_size = int(((c.CHUNK_SIZE - 1) / 2) * c.FRAME_STEP)

        return slice_size


    def __load_track(self):
        self.track_id = self.track_data['@id']
        self.track_label = self.track_data['@label']
        self.attributes = self.labels[self.track_label]

        self.target_attributes = \
            self.settings['target_attributes'][self.track_label]

        for attrib in self.target_attributes:
            self.sequences[attrib] = []
        self.sequences[c.BASE_CLASS] = []

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


    def __find_dynamic_markers(self):
        self.dynamic_markers = OrderedDict()
        previous_attrib_states = OrderedDict()

        for attribute in self.attributes:
            if attribute in self.target_attributes:
                self.dynamic_markers[attribute] = OrderedDict()
                previous_attrib_states[attribute] = None

        self.dynamic_markers[c.BASE_CLASS] = OrderedDict()
        previous_attrib_states[c.BASE_CLASS] = None

        self.__add_dynamic_markers(previous_attrib_states)


    def __add_dynamic_markers(self, previous_attrib_states):
        target_attribs = self.__get_attribs_list_with_base_class()

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


    def __get_attribs_list_with_base_class(self):
        attribs = [attrib for attrib in self.target_attributes]
        attribs.append(c.BASE_CLASS)

        return attribs


    def __evaluate_frame(self, frame_number, states,
                         previous_attrib_states,
                         target_attribs):

        for attrib, state in states.items():
            if attrib in target_attribs:

                previous_state = previous_attrib_states[attrib]
                is_last_frame = (frame_number == self.last_frame)

                if (previous_state == state) \
                        and (frame_number != self.last_frame):
                    continue

                elif (previous_state != state) or is_last_frame:
                    self.__mark_frame(
                        attrib,
                        frame_number,
                        state,
                        previous_state
                    )


    def __mark_frame(self, attrib, frame_number, state, previous_state):

        first_frame = (previous_state is None) and (state == 'true')
        last_frame = (frame_number == self.last_frame) and (state == 'true')
        start_frame = (previous_state == 'false') and (state == 'true')
        end_frame = (previous_state == 'true') and (state == 'false')

        if first_frame or start_frame:
            self.dynamic_markers[attrib][frame_number] = 'start_frame'
        elif end_frame:
            self.dynamic_markers[attrib][frame_number - 1] = 'end_frame'
        elif last_frame:
            self.dynamic_markers[attrib][frame_number] = 'end_frame'


    def generate_sequences(self, extend_with_reversed):
        if len(self.track_frames) >= self.frames_in_chunk:
            self.__add_sequences_from_markers(extend_with_reversed,
                                              self.dynamic_markers,
                                              self.static_markers)


    def __add_sequences_from_markers(self, extend_with_reversed,
                                     *general_marker_types):
        supported_marker_types = \
            list(self.dynamic_types) + list(self.static_types)

        supported_marker_types = []
        for marker_type in (self.dynamic_types, self.static_types):
            if isinstance(marker_type, tuple):
                supported_marker_types += list(marker_type)
            else:
                supported_marker_types.append(marker_type)

        print(supported_marker_types)

        for marker_category in general_marker_types:
            for attrib, frames in marker_category.items():

                for frame, marker_type in frames.items():

                    if marker_type in supported_marker_types:
                        new_sequence = self.__get_target_sequence(
                            frame,
                            marker_type,
                            attrib,
                            extend_with_reversed,
                        )

                    if new_sequence is not None:
                        self.sequences[attrib].append(new_sequence)


    def __get_target_sequence(self, frame, marker_type,
                              attrib, extend_with_reversed) -> tuple:
        new_sequence = None
        sequence_type = None
        sequence_status = 'failed'

        if marker_type in self.dynamic_types:
            sequence_type = 'dynamic'
        elif marker_type in self.static_types:
            sequence_type = 'static'

        sequence_indexes = self.__get_chunk_indexes(frame)
        indexes_are_avalible = \
            self.__test_frames_availibility(sequence_indexes)

        if indexes_are_avalible:
            sequence_status = self.__test_frame_status_integrity(
                frame,
                attrib,
                marker_type,
                sequence_indexes,
            )

        if sequence_status == 'passed':
            new_sequence = self.__get_sequence(
                attrib,
                sequence_type,
                sequence_indexes,
                extend_with_reversed,
                marker_type,
            )

            print (new_sequence)

        return new_sequence


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
        sequence_status = 'failed'

        start_frame = frames[0]
        end_frame = frames[-1]

        subframes = list(range(start_frame, end_frame + 1, 1))

        if attrib != c.BASE_CLASS:
            sequence_status = \
                self.__evaluate_attrib_frames(frame, attrib,
                                              marker_type, subframes)

        elif attrib == c.BASE_CLASS:
            status_is_stable = \
                self.__check_attrib_status(attrib, subframes, 'true')

            if status_is_stable: sequence_status = 'passed'

        return sequence_status


    def __evaluate_attrib_frames(self, frame, attrib,
                                 marker_type, frames) -> str:
        chunk_status = 'failed'

        left_frames, right_frames = \
                self.__get_attrib_slice(marker_type, frame, frames)

        if marker_type=='start_frame':
            left_is_false, right_is_true = (
                self.__check_attrib_status(attrib, left_frames, 'false'),
                self.__check_attrib_status(attrib, right_frames, 'true'),
            )

            if left_is_false and right_is_true: chunk_status = 'passed'

        elif marker_type=='end_frame':
            left_is_true, right_is_false = (
                self.__check_attrib_status(attrib, left_frames, 'true'),
                self.__check_attrib_status(attrib, right_frames, 'false'),
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


    def __check_attrib_status(self, attrib,
                              frames, target_value) -> bool:
        def compare_frame_status_with_target(frame):
            if self.track_frames[frame]['attributes'][attrib]==target_value:
                return True
            else:
                return False

        slice_status = \
            all([compare_frame_status_with_target(frame) for frame in frames])

        return slice_status


    def __get_sequence(self, attrib, sequence_type, sequence_indexes,
                       extend_with_reversed, marker_type) -> tuple:
        assert sequence_type is not None
        sequence_class = attrib
        sequence_frames = OrderedDict()

        if extend_with_reversed and (marker_type=='end_frame'):
            sequence_indexes = list(reversed(sequence_indexes))

        for frame in sequence_indexes:
            sequence_frames[frame] = self.track_frames[frame]['coordinates']

        new_sequence = tuple((sequence_class, sequence_type, sequence_frames))

        return new_sequence


    def __find_static_markers(self, *static_attribs):
        self.static_markers = OrderedDict()

        for attrib in static_attribs:
            self.static_markers[attrib] = OrderedDict()

            static_markers = self.__get_static_markers(
                attrib_name=attrib,
                dynamic_markers=self.dynamic_markers[attrib],
            )

            for marker in static_markers:
                self.static_markers[attrib][marker] = 'static_frame'


    def __get_static_markers(self, attrib_name, dynamic_markers):
        static_markers = []
        tmp_interval = []

        for frame, dynamic_type in dynamic_markers.items():
            if dynamic_type == 'start_frame':
                tmp_interval.append(frame)

            else:
                tmp_interval.append(frame)

                if len(tmp_interval) == 2:
                    static_range = self.__get_static_interval(attrib_name,
                                                              tmp_interval)

                    if static_range is not None:
                        static_markers += static_range

                tmp_interval = []

        return static_markers


    def __get_static_interval(self, attrib_name, interval):
        assert len(interval) == 2
        start_idx = interval[0]
        end_idx = interval[1]

        assert start_idx < end_idx
        static_range = None
        range_is_valid = False

        interval_frames = list(range(start_idx, end_idx))
        interval_size = len(interval_frames)

        # Check frames from full interval to avoid errors in borders
        frames_status_is_stable = self.__check_attrib_status(
            attrib_name,
            interval_frames,
            target_value='true'
        )

        if interval_size >= self.frames_in_chunk * c.CHUNK_BORDER_RATIO:
            interval_frames, interval_size = \
                self.__get_interval_slice(interval_frames)

            if frames_status_is_stable:
                range_is_valid = self.__test_interval_frames(interval_frames,
                                                             interval_size)

            # Slicer allows to skip subframes and reduce iterator length
            if range_is_valid:
                static_range = interval_frames[::self.frames_in_chunk]

        return static_range


    def __get_interval_slice(self, interval_frames):
        cut_size = self.__get_side_size_for_chunk() * c.CHUNK_BORDER_RATIO

        interval_frames = interval_frames[cut_size:-cut_size]
        interval_size = len(interval_frames)

        return interval_frames, interval_size


    def __test_interval_frames(self, interval_frames, interval_size):
        interval_is_valid = False

        frames_are_availible = self.__test_frames_availibility(interval_frames)
        frames_size_supported = (interval_size >= self.frames_in_chunk)

        if frames_are_availible and frames_size_supported:
            interval_is_valid = True

        return interval_is_valid
