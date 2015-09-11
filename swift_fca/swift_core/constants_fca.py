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
    SKIPPED_LINES = 'skipped_lines'


class FileType:
    CSV = ".csv"
    ARFF = ".arff"
    DAT = ".dat"
    CXT = ".cxt"
    DATA = ".data"
    NAMES = ".names"
    ALL = [CSV, ARFF, DAT, DATA, NAMES, CXT]


class ErrorMessage:
    UNKNOWN_ERROR = "\nSwift Unknown Error\nPlease report this bug with details below. Thank you.\n\n"
    MISSING_ARGS_ERROR = "Some of required arguments are missing or aren't specified correctly."


class Bival:
    true_val = '1'
    false_val = '0'

    @classmethod
    def true(cls):
        return cls.true_val

    @classmethod
    def false(cls):
        return cls.false_val

    @classmethod
    def set_true(cls, val):
        cls.true_val = str(val)

    @classmethod
    def set_false(cls, val):
        cls.false_val = str(val)

    @classmethod
    def convert(cls, val):
        if val == cls.true():
            return cls.true()
        if val == cls.false():
            return cls.false()
        if bool(int(val)):
            return cls.true()
        return cls.false()
