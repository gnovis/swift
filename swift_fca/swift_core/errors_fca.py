from .constants_fca import FileType, AttrType, RunParams, App
from enum import IntEnum, unique


@unique
class ErrorCode(IntEnum):
    unknown = 1
    arg_error = 2
    arff_header = 3
    data_header = 4
    csv_header = 5
    dat_header = 6
    cxt_header = 7
    arff_line = 8
    data_line = 9
    csv_line = 10
    dat_line = 11
    cxt_line = 12
    formula_syntax = 13
    formula_names = 14
    sequence_syntax = 15
    date_val = 16
    numeric_val = 17
    string_val = 18
    nominal_val = 19
    date_syntax = 20
    date_value_format = 21
    formula_regex = 22
    formula_key = 23
    keyboard_interrupt = 24
    missing_arg = 25
    bival = 26
    broken_pipe = 27


class ErrorMessage:
    UNKNOWN_ERROR = "\nSwift Unknown Error\nPlease report this bug with details below. Thank you.\n\n"
    MISSING_ARGS_ERROR = "Some of required arguments are missing or aren't specified correctly."
    SKIPPED_ERRORS = "Following errors were skipped: "
    SKIPPED_ERRORS_HEADER = "Skipped Errors"


class SwiftError(Exception):
    def __init__(self, ident, name, message):
        self._ident = ident
        self._name = "{} Error".format(name)
        self._message = message

    @property
    def ident(self):
        return self._ident

    @property
    def name(self):
        return self._name

    @property
    def message(self):
        return self._message

    def __str__(self):
        return "{}: [{}: {}]\n{}".format(App.NAME, self.name, self.ident, self.message)


class ParseError(SwiftError):
    def __init__(self, row_no, col_no, line, message,
                 ident, name):
        new_name = "Parse {}".format(name)
        new_message = "line: {}, column: {}\n'{}'\n{}".format(row_no, col_no, line, message)
        super().__init__(ident, new_name, new_message)


class HeaderError(ParseError):
    NAME = "Header"
    HEADER_FORMAT = "{} {}"

    TYPES = {FileType.ARFF: [ErrorCode.arff_header, HEADER_FORMAT.format(FileType.ARFF_REPR, NAME)],
             FileType.DATA: [ErrorCode.data_header, HEADER_FORMAT.format(FileType.DATA_REPR, NAME)],
             FileType.CSV: [ErrorCode.csv_header, HEADER_FORMAT.format(FileType.CSV_REPR, NAME)],
             FileType.DAT: [ErrorCode.dat_header, HEADER_FORMAT.format(FileType.DAT_REPR, NAME)],
             FileType.CXT: [ErrorCode.cxt_header, HEADER_FORMAT.format(FileType.CXT_REPR, NAME)]}

    def __init__(self, file_type, row_no, col_no, line, message):
        super().__init__(row_no, col_no, line, message, *self.TYPES[file_type])


class LineError(ParseError):
    NAME = "Line"
    HEADER_FORMAT = "{} {}"

    TYPES = {FileType.ARFF: [ErrorCode.arff_line, HEADER_FORMAT.format(FileType.ARFF_REPR, NAME)],
             FileType.DATA: [ErrorCode.data_line, HEADER_FORMAT.format(FileType.DATA_REPR, NAME)],
             FileType.CSV: [ErrorCode.csv_line, HEADER_FORMAT.format(FileType.CSV_REPR, NAME)],
             FileType.DAT: [ErrorCode.dat_line, HEADER_FORMAT.format(FileType.DAT_REPR, NAME)],
             FileType.CXT: [ErrorCode.cxt_line, HEADER_FORMAT.format(FileType.CXT_REPR, NAME)]}

    def __init__(self, file_type, row_no, col_no, line, message):
        super().__init__(row_no, col_no, line.strip(), message, *self.TYPES[file_type])


class InvalidValueError(SwiftError):
    NAME = "Value"
    HEADER_FORMAT = "{} {}"
    TYPES = {AttrType.NUMERIC: [ErrorCode.numeric_val, HEADER_FORMAT.format(AttrType.STR_REPR[AttrType.NUMERIC].capitalize(), NAME)],
             AttrType.NOMINAL: [ErrorCode.nominal_val, HEADER_FORMAT.format(AttrType.STR_REPR[AttrType.NOMINAL].capitalize(), NAME)],
             AttrType.STRING: [ErrorCode.string_val, HEADER_FORMAT.format(AttrType.STR_REPR[AttrType.STRING].capitalize(), NAME)],
             AttrType.DATE: [ErrorCode.date_val, HEADER_FORMAT.format(AttrType.STR_REPR[AttrType.DATE].capitalize(), NAME)]}

    def __init__(self, val_type, message):
        super().__init__(self.TYPES[val_type][0], self.TYPES[val_type][1], message)
        self._name = self.TYPES[val_type][1]


class AttrError(SwiftError):
    def __init__(self, line_no, line, attr_no, attr, value_error):
        message = "line: {}\n'{}'\nattribute: {}\n'{}'\n{}".format(line_no, line, attr_no, attr, value_error.message)
        super().__init__(value_error.ident, value_error.name, message)


class FormulaSyntaxError(ParseError):
    def __init__(self, row_no, col_no, line, message):
        super().__init__(row_no, col_no, line, message,
                         ErrorCode.formula_syntax, "Formula")


class SequenceSyntaxError(ParseError):
    def __init__(self, row_no, col_no, line, message):
        super().__init__(row_no, col_no, line, message,
                         ErrorCode.sequence_syntax, "Sequence")


class DateSyntaxError(ParseError):
    def __init__(self, row_no, col_no, line, message):
        super().__init__(row_no, col_no, line, message,
                         ErrorCode.date_syntax, "Date")


class DateValFormatError(SwiftError):
    def __init__(self, message):
        super().__init__(ErrorCode.date_value_format, "Formula Date Value/Format", message)


class FormulaNamesError(SwiftError):
    def __init__(self, old, new):
        msg = "Count of new names and count of old names must be equal.\nnew({}): {}\nold({}): {}".format(len(new), ", ".join(new), len(old), ", ".join(old))
        super().__init__(ErrorCode.formula_names, "Formula Names", msg)


class FormulaKeyError(SwiftError):
    def __init__(self, key):
        super().__init__(ErrorCode.formula_key, "Formula Attribute Key", "Attribute key used in Formula: '{}' doesn't exists.".format(key))


class FormulaRegexError(SwiftError):
    def __init__(self, message):
        super().__init__(ErrorCode.formula_regex, "Formula Regular Expression", message)


class ArgError(SwiftError):
    ARGS = {RunParams.FORMAT:
            "Argument: 'format' is missing.\nIf you are using standart input/output as source/target, argument source/target 'format' must be set."}

    def __init__(self, arg=None, message=""):
        if arg in self.ARGS:
            message = self.ARGS[arg]
        super().__init__(ErrorCode.arg_error, "Argument", message)


class BivalError(SwiftError):
    def __init__(self, val, true, false):
        super().__init__(ErrorCode.bival, "Bivalent",
                         "Invalid bivalent value in data - given: {}, expected: {}(=True) or {}(=False). Or scale formula is missing.".format(val, true, false))
