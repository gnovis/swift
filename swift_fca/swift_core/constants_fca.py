class RunParams:
    """Parameters which are used for runing app"""
    SOURCE = 'source'
    SOURCE_SEP = 'separator'
    SOURCE_ATTRS = 'str_attrs'
    NFL = 'no_attrs_first_line'
    TARGET = 'source'
    TARGET_SEP = 'separator'
    TARGET_OBJECTS = 'str_objects'
    RELATION_NAME = 'relation_name'
    CLASSES = 'classes'
    SOURCE_INFO = 'print_info'
    NONE_VALUE = 'none_val'
    FORMAT = 'format'
    LINE_COUNT = 'line_count'


class FileType:
    CSV = ".csv"
    ARFF = ".arff"
    DAT = ".dat"
    CXT = ".cxt"
    DATA = ".data"
    NAMES = ".names"


class ErrorMessage:
    UNKNOWN_ERROR = "\nSwift Unknown Error\nPlease report this bug with details below. Thank you.\n\n"
