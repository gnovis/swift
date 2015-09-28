class App:
    NAME = 'swift'


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
    SKIP_ERRORS = 'skip_errors'


class FileType:
    CSV = 0
    ARFF = 1
    DAT = 2
    CXT = 3
    DATA = 4
    NAMES = 5

    CSV_EXT = ".csv"
    ARFF_EXT = ".arff"
    DAT_EXT = ".dat"
    CXT_EXT = ".cxt"
    DATA_EXT = ".data"
    NAMES_EXT = ".names"

    CSV_REPR = "csv"
    ARFF_REPR = "arff"
    DAT_REPR = "dat"
    CXT_REPR = "cxt"
    DATA_REPR = "data"
    NAMES_REPR = "names"

    ALL_EXT = [CSV_EXT, ARFF_EXT, DAT_EXT, DATA_EXT, NAMES_EXT, CXT_EXT]
    ALL_REPR = [CSV_REPR, ARFF_REPR, DAT_REPR, DATA_REPR, NAMES_REPR, CXT_REPR]


class AttrType:
    NUMERIC = 0
    NOMINAL = 1
    STRING = 2
    DATE = 3
    NOT_SPECIFIED = 4
    STR_REPR = {NUMERIC: "numeric",
                NOMINAL: "nominal",
                STRING: "string",
                DATE: "date",
                NOT_SPECIFIED: "not specified"}


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
