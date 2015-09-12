from .constants_fca import FileType, AttrType
from enum import IntEnum, unique


@unique
class ErrorCode(IntEnum):
    arff_header = 1
    data_header = 2
    csv_header = 3
    dat_header = 4
    cxt_header = 5
    arff_line = 6
    data_line = 7
    csv_line = 8
    dat_line = 9
    cxt_line = 10
    formula_syntax = 11
    formula_names = 12
    sequence_syntax = 13
    date_val = 14
    numeric_val = 15
    string_val = 16
    nominal_val = 17
    date_syntax = 18
    date_value_format = 19
    formula_regex = 20
    formula_key = 21


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
        return "swift: [{}: {}]\n{}".format(self.name, self.ident, self.message)


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
