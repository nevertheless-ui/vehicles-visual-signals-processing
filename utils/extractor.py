"""General extractor task Class module
"""
import os

from utils import constants as c
from utils import annotation_parser



class ExtractionTask:
    def __init__(self, import_path, export_path,
                 filename, annotation, overwrite, mode, logger):
        """Task for extraction from video file.

        Args:
            import_path (str): Path to the source directory
            export_path (str): Path to the dataset directory
            filename (str): Video file
            annotation (str): Annotation file
            overwrite (bool): Overwrite existing dataset or not
        """
        self.source_path = os.path.join(import_path, filename)
        self.output_path = export_path
        self.annotation_path = os.path.join(import_path, annotation)
        self.overwrite = overwrite
        self.mode = mode
        self.logger = logger
        # Read internal constants
        self.base_class = c.BASE_CLASS
        self.class_overlay = c.CLASS_OVERLAY
        self.chunk_size = c.CHUNK_SIZE
        self.extend_with_reversed = c.ADD_REVERSED
        self.target_attributes = c.TARGET_ATTRIBUTES
        self.logger_skip_atributes = c.LOGGER_SKIP_ATTRIBUTES

    def read_annotation(self):
        """Reads annotation from annotation files and add it as
        attributes to the current instance.
        """
        self.annotation_meta, \
        self.annotation_tracks = \
            annotation_parser.get_annotation(self.annotation_path)
        self.info = {
            **annotation_parser.get_metadata(self.annotation_meta),
            **annotation_parser.get_trackdata(self.annotation_tracks),
            **annotation_parser.get_labels(self.annotation_meta, c.TARGET_ATTRIBUTES.keys())
        }

    def log_attributes(self):
        """Writes all instance attributes to the log file. Cuts off all
        long attributes. e.g. Chunks
        """
        long_attributes = ('script', 'info')
        for attribute, value in self.__dict__.items():
            if attribute not in self.logger_skip_atributes:
                # Makes logs shorter. Script contains too much data.
                if attribute in long_attributes:
                    for info_attribute in value.keys():
                        if info_attribute == 'chunks':
                            chunks_in_script = len(value[info_attribute])
                            log_msg = \
                                f"{attribute}: {info_attribute}: {chunks_in_script} chunks total"
                        elif info_attribute == 'statistics':
                            stats = value[info_attribute].items()
                            for stat_name, stat_data in stats:
                                log_msg = f"{attribute}: {stat_name}: {stat_data}"
                        else:
                            log_msg = f"{attribute}: {info_attribute}: {value[info_attribute]}"
                        self.logger.debug(log_msg)
                else:
                    self.logger.debug(f"{attribute}: {value}")
