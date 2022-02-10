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

        DOES NOT WORK WITH VIDEO FILE. ONLY WITH ANNOTATION.

        Basic workflow of class usage:

        - Initialize class:
            - track - Track data from annotation parser
            - settings - Script settings from video editor
            - labels - Labels info from extraction task
            - frames_total - Frames number in video
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

        # Will be used to change sequence generator behaviour
        # BASE_CLASS usually is a static type and more common in track
        self.activation_name = c.ACTIVATION_NAME
        self.deactivation_name = c.DEACTIVATION_NAME
        self.static_name = c.STATIC_NAME
        self.dynamic_types = (self.activation_name, self.deactivation_name)
        self.static_types = (self.static_name)

        self.sequences = OrderedDict()

        # Loader of the attributes
        self.__load_track_info()
        self.__load_track_data()

        if self.mode == 'sequence':
            self.__add_dynamic_markers()
            self.__add_static_markers(c.BASE_CLASS)

        #self.show_debug()                 # For developing process only


    def generate_sequences(self, extend_with_reversed):
        """Initialize process of sequence yielding from existing
        markers.

        Args:
            - extend_with_reversed (book): Experimental. Enables adding
                reversed sequences to augment and extend dataset.
        """
        if self.mode == 'singleshot':
            self.__add_singleshot_sequences_from_attributes()

        elif self.mode == 'sequence':
            enough_frames_in_track = (len(self.track_frames) >= self.frames_in_chunk)

            if enough_frames_in_track:
                self.__add_sequences_from_markers(
                    extend_with_reversed,
                    self.dynamic_markers,
                    self.static_markers,
                )


    def show_debug(self):
        """Debug method to show current instance state
        """
        print(self.track_id)
        for property in (self.dynamic_markers,
                         self.static_markers,
                         self.sequences):

            for key, val in property.items():
                print(key, val)


    def __len__(self) -> int:
        """Number of sequences

        Returns:
            - int: Number of sequences
        """
        total_chunk_count = 0
        for chunks in self.sequences.values():
            total_chunk_count += len(chunks)

        return total_chunk_count


    @staticmethod
    def __get_slice_size_for_chunk() -> int:
        """Calculates number of frames, which should be used to generate
        chunks of target size and spaces between subframes.
        It uses constants from settings.

        Requires chunk size and step between each frame. For example:
        - 5 frames with step 5 returns 21 as a result

        o----o----o----o----o = 21 frames total, where 'o' - key frames

        Returns:
            - int: Number of frames in chunk
        """
        slice_size = ((c.CHUNK_SIZE - 1) * c.FRAME_STEP) + 1

        return slice_size


    @staticmethod
    def __get_side_size_for_chunk() -> int:
        """This method is used to get slice size for slicing range of
        frames. For example, if chunk is generated from 21 frames, it
        returns 10. To slice 10 from left and 10 from right, so there
        will be only 1 frame left.

        Returns:
            - int: Number of frames to trim from left and right
        """
        slice_size = int(((c.CHUNK_SIZE - 1) / 2) * c.FRAME_STEP)

        return slice_size


    def __load_track_info(self):
        """Loads basic parameters of the class instance. Reads track
        data, such as track id, label, track atributes.
        """
        self.track_id = self.track_data['@id']
        self.track_label = self.track_data['@label']
        self.attributes = self.labels[self.track_label]

        self.target_attributes = self.settings['target_attributes'][self.track_label]
        self.mode = self.settings['mode']

        for attrib in self.target_attributes:
            self.sequences[attrib] = []
        self.sequences[c.BASE_CLASS] = []

        self.track_frames = OrderedDict()


    def __load_track_data(self):
        """Iterates over valid (not outside) frames and collect:
        - frame number
        - object box coordinate
        - attributes of an object in the box
        """
        for box in self.track_data['box']:
            try:
                if box['@outside'] != '1':
                    attributes = OrderedDict()
                    frame_number = int(box['@frame'])
                    coordinates = self.__get_coordinates(box)

                    if frame_number > self.last_frame:
                        self.last_frame = frame_number

                    if frame_number < self.first_frame:
                        self.first_frame = frame_number

                    if 'attribute' in box.keys():
                        attributes = {x['@name']:x['#text'] for x in box['attribute']}

                    self.track_frames[frame_number] = {
                        'coordinates':coordinates,
                        'attributes':attributes,
                    }
            except TypeError:
                pass


    @staticmethod
    def __get_coordinates(box) -> dict:
        """Parse coordinates from default CVAT annotation format.

        Args:
            - box (OrderedDict): Annotation info about object on frame

        Returns:
            - tuple: Coordinates of object box in frame
        """
        def convert_str_to_int(*coordinates):
            """Converter for coordinates. Takes STR and returns INT.

            Returns:
                - int: Coordinate of point in some dimension
            """
            assert len(coordinates) == 4, "Too many points"

            converted_coordinates = tuple(
                int(float(coordinate)) for coordinate in coordinates
            )

            return converted_coordinates

        coordinates = convert_str_to_int(
            box['@xtl'], box['@ytl'], box['@xbr'], box['@ybr']
        )

        return coordinates


    def __add_dynamic_markers(self):
        """Initializes process of collecting data about starting and
        ending points of dynamically changing attribute.

        Search process is based on comparison current attribute states
        with the previous ones. So for the first step previous states
        are considered as 'None'.

        For example: BRAKE. It may have one or more starting and ending
        frame pairs. There must be ending marker for every starting one.
        """
        self.dynamic_markers = OrderedDict()
        previous_attrib_states = OrderedDict()
        previous_frame_number = None

        for attribute in self.attributes:
            if attribute in self.target_attributes:
                self.dynamic_markers[attribute] = OrderedDict()
                previous_attrib_states[attribute] = None

        # While 'BASE_CLASS' is static by default, we should process it
        # like the dynamic ones. Markers of 'BASE_CLASS' will be used
        # to make searching pf static ranges easier.
        self.dynamic_markers[c.BASE_CLASS] = OrderedDict()
        previous_attrib_states[c.BASE_CLASS] = None

        self.__find_dynamic_markers(previous_attrib_states, previous_frame_number)


    def __find_dynamic_markers(self, previous_attrib_states, previous_frame_number):
        """Iterates over frames and mark all suitable markers. Updates
        previous states with current state each step.

        Args:
            - previous_attrib_states (OrderedDict): Information about
                attribute state on the previouse step
            - previous_frame_number (int) : Number of previous frame
        """
        target_attribs = self.__get_attribs_list_with_base_class()

        for frame_number, metadata in self.track_frames.items():

            states = self.__add_base_class_attribute(metadata['attributes'])

            self.__evaluate_frame(
                frame_number,
                states,
                previous_attrib_states,
                previous_frame_number,
                target_attribs
            )

            previous_frame_number = frame_number
            for attribute, state in states.items():
                previous_attrib_states[attribute] = state


    @staticmethod
    def __add_base_class_attribute(attribute_states):
        """As far as 'BASE_CLASS' has no initial attribute - method adds
        base attribute to metadata. (Base class is 'true' when all
        other classes are 'false')

        Args:
            - states (OrderedDict): Attribute states of the current
                frame

        Returns:
            - OrderedDict: Updated attribute states of the current frame
        """
        any_attribute_state_is_active = any([state=='true' for state in attribute_states.values()])

        if not any_attribute_state_is_active:
            attribute_states[c.BASE_CLASS] = 'true'
        else:
            attribute_states[c.BASE_CLASS] = 'false'

        return attribute_states


    def __get_attribs_list_with_base_class(self):
        """Wrapper for getting atributes with 'BASE_CLASS' without
        implementing changes to the original variable.

        Returns:
            - list: Target classes with 'BASE_CLASS' name added
        """
        attributes = [attribute for attribute in self.target_attributes]
        attributes.append(c.BASE_CLASS)

        return attributes


    def __evaluate_frame(self, frame_number, states,
                         previous_attrib_states,
                         previous_frame_number,
                         target_attribs):
        """Makes evaluation of attribute states on the frame in
        comparison with previous frame.

        Calls marking method if conditions can be applied.

        Args:
            - frame_number (int): Current frame number
            - states (OrderedDict): Current frame's attributes states
            - previous_attrib_states (OrderedDict): Previous frame's
                attributes states
            - previous_frame_number (int | None): Previous frame number
            - target_attribs (list): Attributes which will be marked
        """
        # Initial 'track_with_cuts' is 'None', so exception can be
        # raised and need to be treated
        # What is cut? It is a case where status is the same, but some
        # frames are skipped. For example: frames=[1,2,3,10,11,12]
        try:
            track_with_cuts = (frame_number != previous_frame_number + 1)
        except TypeError:
            track_with_cuts = False

        for attribute, state in states.items():
            if attribute in target_attribs:

                previous_state = previous_attrib_states[attribute]

                # Basic checks for changing of attribute status
                is_last_frame = (frame_number == self.last_frame)
                attribute_state_changed = (previous_state != state)

                # More common case where nothing changes
                if not attribute_state_changed and is_last_frame:
                    continue

                elif attribute_state_changed or track_with_cuts or is_last_frame:
                    self.__mark_frame(
                        attribute,
                        frame_number,
                        state,
                        previous_state,
                        track_with_cuts,
                        is_last_frame
                    )


    def __mark_frame(self, attribute, frame_number, state,
                     previous_state, track_with_cuts, is_last_frame):
        """Marks input frame according to initial condition. There are
        4 ways of resolving marking task:
        1. First frame in track or attribute is activated
        2. There are one or more missing frames between current and
            previous
        3. Attribute is deactivated
        4. Current frame is the last one in track

        Args:
            - attribute (str): Name of the marking attribute
            - frame_number (int): Current name number
            - state (str): 'true' or 'false' (Default CVAT values)
            - previous_state (OrderedDict): Records of attributes states
                from the previous step
            - track_with_cuts (bool): Whether cut is spotted or not
            - is_last_frame (bool): Whether frame is last one or not
        """
        # Simple events
        no_previous = (previous_state is None)
        previous_is_true = (previous_state == 'true')
        previous_is_false = (previous_state == 'false')
        current_is_true = (state == 'true')
        current_is_false = (state == 'false')

        # Markers type conditions - all 5 types of outcomes
        first_frame = (no_previous and current_is_true)
        last_frame = (is_last_frame and current_is_true)
        start_frame = (previous_is_false and current_is_true)
        end_frame = (previous_is_true and current_is_false)
        cut_frame = (previous_is_true and current_is_true and track_with_cuts)

        if first_frame or start_frame:
            self.dynamic_markers[attribute][frame_number] = self.activation_name
        elif cut_frame:
            self.dynamic_markers[attribute][frame_number - 1] = self.deactivation_name
            self.dynamic_markers[attribute][frame_number] = self.activation_name
        elif end_frame:
            self.dynamic_markers[attribute][frame_number - 1] = self.deactivation_name
        elif last_frame:
            self.dynamic_markers[attribute][frame_number] = self.deactivation_name


    def __add_singleshot_sequences_from_attributes(self):
        """Simple case where only one shot should be written. Writes
        sequences but only with lenght of 1. May produce mixing of
        classes, as currently no support single attribute chech.
        """
        # Initialize all
        self.single_markers = OrderedDict()
        self.single_markers[c.BASE_CLASS] = OrderedDict()
        for attribute in self.attributes:
            if attribute in self.target_attributes:
                self.single_markers[attribute] = OrderedDict()

        # Collecting all attributes in one pass over all frames
        # TODO: Add param for mixing classes
        for frame, metadata in self.track_frames.items():
            attribute_states = self.__add_base_class_attribute(metadata['attributes'])

            coordinates = metadata['coordinates']

            for attribute, state in attribute_states.items():
                state_is_positive = (state == 'true')
                attribute_is_target = (attribute in self.single_markers.keys())

                if state_is_positive and attribute_is_target:
                    sequence_frame = OrderedDict()
                    sequence_frame[frame] = coordinates

                    new_sequence = tuple((attribute, self.mode, sequence_frame))

                    self.sequences[attribute].append(new_sequence)


    def __add_sequences_from_markers(self, extend_with_reversed,
                                     *general_marker_types):
        """Iterates over dynamic and static markers and append new
        sequences.

        Args:
            - extend_with_reversed (book): Experimental. Enables adding
                reversed sequences to augment and extend dataset.
        """
        target_marker_types = self.__merge_marker_types(
            self.dynamic_types,
            self.static_types
        )

        for marker_category in general_marker_types:
            for attribute, frames in marker_category.items():

                for frame, marker_type in frames.items():

                    if marker_type in target_marker_types:
                        new_sequence = self.__get_target_sequence(
                            frame,
                            marker_type,
                            attribute,
                            extend_with_reversed,
                        )

                    if new_sequence is not None:
                        self.sequences[attribute].append(new_sequence)


    @staticmethod
    def __merge_marker_types(*marker_types):
        """Merge different objects which contain marker types in one
        general tuple. Solves case where one list is a STR, so adding
        can not be performed properly by default magic methods.

        Returns:
            - tuple: Markers which will be added to sequences
        """
        supported_marker_types = []

        for marker_type in marker_types:
            if isinstance(marker_type, tuple):
                supported_marker_types += list(marker_type)
            else:
                supported_marker_types.append(marker_type)

        return tuple(supported_marker_types)


    def __get_target_sequence(self, frame, marker_type, attribute, extend_with_reversed) -> tuple:
        """Creates new sequence from the initial frame. Calculates all
        subframes, test its availibility, doublecheck attribute status
        and collects metadata.

        Args:
            - frame (int): Frame number
            - marker_type (str): Dynamic or static type
            - attribute (str): Attribute name for the sequence
            - extend_with_reversed (book): Experimental. Enables adding
                reversed sequences to augment and extend dataset.

        Returns:
            tuple: Sequence(class, type, frames((num, coordinates),...))
        """
        new_sequence = None
        sequence_type = None
        sequence_status = 'failed'

        if marker_type in self.dynamic_types:
            sequence_type = f'dynamic_{marker_type}'
        elif marker_type in self.static_types:
            sequence_type = 'static'

        # Testing frames
        sequence_indexes = self.__get_chunk_indexes(frame)
        indexes_are_avalible = self.__test_frames_availibility(sequence_indexes)

        if indexes_are_avalible:
            sequence_status = self.__test_frame_status_integrity(
                frame,
                attribute,
                marker_type,
                sequence_indexes,
            )

        if sequence_status == 'passed':
            new_sequence = self.__get_sequence(
                attribute,
                sequence_type,
                sequence_indexes,
                extend_with_reversed,
                marker_type,
            )

        return new_sequence


    @staticmethod
    def __get_chunk_indexes(frame) -> list:
        """Constructs keyframes list from center frame index. Adds
        frames from the left and from the right. Uses global constants.

        Example for CHUNK_SIZE=5 - list of 5 frames, where central frame
        is predefined by call method.

        Args:
            frame (int): Central frame index to be wrapped with ranges

        Returns:
            list: All keyframes of the chunk
        """
        def get_shifts(frame, steps):
            """Submethod to add simmetric appendixes for left and right

            Args:
                - frame (int): Index of center frame
                - steps (int): Number of steps from center frame

            Returns:
                tuples: Sorted indexes of the appendixes
            """
            left = []
            right = []

            for i in range(1, steps + 1):
                left.append(frame + (c.FRAME_STEP * -i))
                right.append(frame + (c.FRAME_STEP * i))

            return sorted(left), sorted(right)

        added_size = c.CHUNK_SIZE - 1
        steps = int(added_size / 2)
        left, right = get_shifts(frame, steps)

        frames = left + [frame] + right

        return frames


    def __test_frames_availibility(self, frames) -> bool:
        """Checks accessibility of all frames in list on track. If not -
        data can not be correctly collected for this chunk.

        Args:
            - frames (list): All frames of the chunk

        Returns:
            bool: True if all frames in track data, else - False
        """
        all_indexes_are_availible_in_track_status = \
            all([(idx in self.track_frames.keys()) for idx in frames])

        return all_indexes_are_availible_in_track_status


    def __test_frame_status_integrity(self, frame, attribute,
                                      marker_type, frames):
        """Final check of all conditions of a good chunk. There are:
        - For dynamic types: left and right frames have different state
        - For static types: all frames have the same state

        Args:
            - frame (int): Frame number
            - attribute (str): Attribute name
            - marker_type (str): 'dynamic' or 'static' type
            - frames (list): Chunk with all subframes

        Returns:
            str: Sequence status: 'passed' or 'failed'(default)
        """
        sequence_status = 'failed'

        start_frame = frames[0]
        end_frame = frames[-1]

        subframes = list(range(start_frame, end_frame + 1, 1))

        if attribute != c.BASE_CLASS:
            sequence_status = self.__evaluate_attrib_frames(
                frame,
                attribute,
                marker_type,
                subframes
            )

        elif attribute == c.BASE_CLASS:
            status_is_stable = self.__check_attrib_status(
                attribute,
                subframes,
                'true'
            )

            if status_is_stable:
                sequence_status = 'passed'

        if len(subframes) != self.frames_in_chunk:
            sequence_status = 'failed'

        return sequence_status


    def __evaluate_attrib_frames(self, frame, attribute, marker_type, frames) -> str:
        """Evaluates dynamic event types. Marker type names for activation and
        deactivation are in constants. Checks status of activation in the left
        and the right part of chunk slices.

        Args:
            - frame (int): Frame number
            - attribute (str): Attribute name
            - marker_type (str): 'dynamic' or 'static' type
            - frames (list): Chunk with all subframes

        Returns:
            str: Check status - 'passed' or 'failed'(dafault)
        """
        chunk_status = 'failed'

        left_frames, right_frames = self.__get_attrib_slice(marker_type, frame, frames)

        if marker_type==self.activation_name:
            left_is_false, right_is_true = (
                self.__check_attrib_status(attribute, left_frames, 'false'),
                self.__check_attrib_status(attribute, right_frames, 'true'),
            )

            if left_is_false and right_is_true:
                chunk_status = 'passed'

        elif marker_type==self.deactivation_name:
            left_is_true, right_is_false = (
                self.__check_attrib_status(attribute, left_frames, 'true'),
                self.__check_attrib_status(attribute, right_frames, 'false'),
            )

            if left_is_true and right_is_false:
                chunk_status = 'passed'

        return chunk_status


    def __get_attrib_slice(self, marker_type, frame, frames) -> tuple:
        """Get slices from left and right for status checking.

        Args:
            marker_type (str): Type of marker
            frame (int): Frame number
            frames (list): All frames in chunk

        Returns:
            tuples: Left and right slices
        """
        center_idx = frames.index(frame)

        if marker_type==self.deactivation_name:
            center_idx += 1

        left_slice = frames[:center_idx]
        right_slice = frames[center_idx:]

        return left_slice, right_slice


    def __check_attrib_status(self, attrib, frames, target_value) -> bool:
        """Checks if all frames have target attibute status.

        Args:
            attrib (str): Name of the attribute
            frames (list): Frames of tested sequence
            target_value (str): 'true' or 'false'

        Returns:
            bool: If all frames have target value - True, else - False
        """
        def compare_frame_status_with_target(frame):
            """Submethod. Checks status of target attribute on frame.

            Args:
                frame (int): Frame number

            Returns:
                bool: True if arrtib==target_value, else - False
            """
            try:
                attribute_has_same_value = \
                    self.track_frames[frame]['attributes'][attrib]==target_value

                if attribute_has_same_value:
                    return True
                else:
                    return False

            except KeyError:
                return False

        slice_status = all([compare_frame_status_with_target(frame) for frame in frames])

        return slice_status


    def __get_sequence(self, attribute, sequence_type, sequence_indexes,
                       extend_with_reversed, marker_type) -> tuple:
        """Collects validated sequence data in one tuple.

        Args:
            attribute (str): Name of the attribute
            sequence_type (str): 'dynamic_{marker}' or 'static'
            sequence_indexes (list): All keyframes of the sequence
            extend_with_reversed (bool): Experimental. Add reversed
                sequence for signal deactivation and add it as an activation
            marker_type (str): Type of marker. ex.: 'activation'

        Returns:
            tuple: (
                sequence_class (str),
                sequence_type (str),
                sequence_frames (
                    {frame: {'coordinates': (ax, ay, bx, by)}},
                    ...
                )
            )
        """
        assert sequence_type is not None
        sequence_class = attribute
        sequence_frames = OrderedDict()

        if extend_with_reversed and (marker_type==self.deactivation_name):
            sequence_indexes = list(reversed(sequence_indexes))

        for frame in sequence_indexes:
            sequence_frames[frame] = self.track_frames[frame]['coordinates']

        new_sequence = tuple((sequence_class, sequence_type, sequence_frames))

        return new_sequence


    def __add_static_markers(self, *static_attributes):
        """Iterates over static attributes and initialize process of
        collecting static markers based on its dynamic markers.

        Args:
            - *static_attributes (tuples): Names of static attributes
        """
        self.static_markers = OrderedDict()

        for attribute in static_attributes:
            self.static_markers[attribute] = OrderedDict()

            static_markers = self.__get_static_markers(
                attribute_name=attribute,
                dynamic_markers=self.dynamic_markers[attribute],
            )

            for marker in static_markers:
                self.static_markers[attribute][marker] = self.static_name


    def __get_static_markers(self, attribute_name, dynamic_markers):
        """Iterate over attribute markers and combines start and end
        frames. After combining - tests availibility and adds to markers
        list.

        Args:
            - attribute_name (str): Name of the attribute
            - dynamic_markers (OrderedDict): Dynamic markers for attrib

        Returns:
            list: Frame numbers of static markers
        """
        static_markers = []

        # Collects pairs of start and end frames
        tmp_interval = []

        # There MUST be activation and deactivation marker on the track
        # So this iterator combines them into pairs and collect inner centers
        # for the markers, to skip all overlapping frames and speed up yielding
        for frame, dynamic_type in dynamic_markers.items():
            if dynamic_type == self.activation_name:
                tmp_interval.append(frame)

            elif dynamic_type == self.deactivation_name:
                tmp_interval.append(frame)

                if len(tmp_interval) == 2:
                    static_range = self.__get_static_interval(
                        attribute_name,
                        tmp_interval,
                    )

                    static_markers += static_range

                tmp_interval = []

        return static_markers


    def __get_static_interval(self, attribute_name, interval):
        """Analyze input interval and return keyframes for static
        markers. If inteval is too short - returns empty list.

        All center frames will be shifted to the left border of the
        interval as a more straight forward way.

        WARNING:
        Initial interval will be cutted from both sides to avoid
        inaccuracies in borders of activation or deactivation events.
        You may refer to 'self.__get_interval_slice()' to get more
        details of this process.

        Args:
            attribute_name (str): Name of the attribute (e.g. 'idle')
            interval (list): [start_frame_index, end_frame_index]

        Returns:
            list: Indexes of frames with shifting.
        """
        assert len(interval) == 2, f"Wrong interval shape of {attribute_name}"

        start_idx = interval[0]
        end_idx = interval[1]

        assert start_idx < end_idx, f"Mixed indexes at {attribute_name}"

        static_range = []
        range_is_valid = False

        interval_frames = list(range(start_idx, end_idx))
        interval_size = len(interval_frames)

        # Check frames from full interval to avoid errors in borders
        frames_status_is_stable = self.__check_attrib_status(
            attribute_name,
            interval_frames,
            target_value='true'
        )

        interval_has_enough_frames_for_slicing = \
            (interval_size >= (self.frames_in_chunk * c.CHUNK_BORDER_RATIO))

        if interval_has_enough_frames_for_slicing:
            interval_frames, interval_size = \
                self.__get_interval_slice(interval_frames)

            if frames_status_is_stable:
                range_is_valid = self.__test_interval_frames(
                    interval_frames,
                    interval_size
                )

            # Slicer allows to skip subframes and reduce iterator length
            if range_is_valid:
                static_range = interval_frames[::self.frames_in_chunk]

        return static_range


    def __get_interval_slice(self, interval_frames):
        """Cut interval range to make it shorter from each side. This
        mathod is aimed to achive more stable classes, fix mixing of
        classas because of probable inaccuracies in annotation.

        e.g. Brake signal stays activated on the frame, but annotator
        marked it as 'false' on several previous frames. So chunk will
        be marked as 'idle' but there is a switchin action event on it.
        To avoid this behaviour we decrease usable frames in static
        sequences and as a result get more stable and accurate classes.

        Uses ratio coefficent to change slice size from constants.

        Args:
            interval_frames (list): All frames in interval

        Returns:
            tuple: (all sliced frames, size of the resulting interval)
        """
        cut_size = (self.__get_side_size_for_chunk() * c.CHUNK_BORDER_RATIO)

        interval_frames = interval_frames[cut_size:-cut_size]
        interval_size = len(interval_frames)

        return interval_frames, interval_size


    def __test_interval_frames(self, interval_frames, interval_size):
        """Final test of candidate interval frames. Checks avalibility
        of frames and general interval size.

        Args:
            interval_frames (list): All frames in interval
            interval_size (int): Size of the onterval

        Returns:
            bool: If interval is valid - True, else - False
        """
        interval_is_valid = False

        frames_are_availible = self.__test_frames_availibility(interval_frames)
        frames_size_supported = (interval_size >= self.frames_in_chunk)

        if frames_are_availible and frames_size_supported:
            interval_is_valid = True

        return interval_is_valid
