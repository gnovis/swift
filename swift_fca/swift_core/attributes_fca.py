"""Attributes classes for swift"""

from __future__ import print_function
import re
from pyparsing import quotedString, removeQuotes
from .date_parser_fca import DateParser
from .grammars_fca import boolexpr


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


class Attribute:

    TRUE = '1'
    FALSE = '0'

    def __init__(self, index, name, attr_type=AttrType.NOT_SPECIFIED):
        self._name = name
        self._index = index
        self._attr_type = attr_type
        self._children = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def index(self):
        return self._index

    @property
    def attr_type(self):
        return self._attr_type

    @property
    def children(self):
        return self._children.copy()

    @children.setter
    def children(self, children):
        self._children = children

    def has_children(self):
        return bool(self._children)

    def print_self(self, out):
        print("\nname: {}\nindex: {}\ntype: {}".format(
            self.name,
            self.index, AttrType.STR_REPR[self.attr_type]), file=out)

    def update(self, value, none_val):
        pass

    def arff_repr(self, sep):
        return '{ ' + self.FALSE + sep + self.TRUE + ' }'

    def data_repr(self, sep):
        return self.FALSE + sep + self.TRUE


class AttrScale(Attribute):
    def __init__(self, index, name, attr_type=AttrType.NOT_SPECIFIED,
                 attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, attr_type)

        # name of atrribute, it is pattern to scaling
        self._attr_pattern = attr_pattern
        # expression to scaling
        self._expr_pattern = expr_pattern

    @property
    def key(self):
        if self._attr_pattern:
            return self._attr_pattern
        return str(self.index)

    def process(self, value, scale):
        if self._expr_pattern and scale:
            return self.scale(value)
        return value

    def scale(self, value):
        return value


class AttrScaleNumeric(AttrScale):
    def __init__(self, index, name, attr_type=AttrType.NUMERIC, attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, attr_type,
                         attr_pattern, expr_pattern)
        self._max_value = None
        self._min_value = None

    @property
    def max_value(self):
        return self._max_value

    @property
    def min_value(self):
        return self._min_value

    def scale(self, value):
        try:
            x = int(value)  # NOQA
        except ValueError:
            # if value is not integer(is string or undefined e.g None, "" or ?) =>
            # result of scaling is false
            return False
        replaced = re.sub(r"[^<>=0-9\s.]+", "x", self._expr_pattern)
        return eval(replaced)

    def update(self, str_value, none_val):
        if str_value != none_val:
            value = float(str_value)
            if not self._max_value:
                self._max_value = value
                return
            if not self._min_value:
                self._min_value = value
                return
            if value > self._max_value:
                self._max_value = value
            if value < self._min_value:
                self._min_value = value

    def print_self(self, out):
        super().print_self(out)
        print("max value: {}\nmin value: {}".format(
              self.max_value, self.min_value), file=out)

    def arff_repr(self, sep):
        return AttrType.STR_REPR[self.attr_type]

    def data_repr(self, sep):
        return "continuous"


class AttrScaleDate(AttrScaleNumeric):
    def __init__(self, index, name, date_format=DateParser.ISO_FORMAT,
                 attr_type=AttrType.DATE, attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, attr_type, attr_pattern, expr_pattern)
        self.parser = DateParser(date_format)
        if expr_pattern:
            self.substitute_date()

    @property
    def max_value(self):
        return self.parser.time_stamp_to_str(self._max_value)

    @property
    def min_value(self):
        return self.parser.time_stamp_to_str(self._min_value)

    def substitute_date(self):
        DATEXPR = quotedString.copy()
        EXPR = boolexpr(VAL=DATEXPR)
        DATEXPR.setParseAction(lambda s, loc, tokens: self.parser.get_time_stamp(removeQuotes(s, loc, tokens)))
        self._expr_pattern = EXPR.parseString(self._expr_pattern)[0]

    def scale(self, value):
        time_stamp = self.parser.get_time_stamp(value)
        return super().scale(time_stamp)

    def update(self, str_date, none_val):
        if str_date != none_val:
            time_stamp = self.parser.get_time_stamp(str_date)
            super().update(time_stamp, none_val)

    def arff_repr(self, sep):
        return "{} {}".format(AttrType.STR_REPR[self.attr_type], self.parser.get_format())

    def data_repr(self, sep):
        return "discrete n"


class AttrScaleEnum(AttrScale):
    def __init__(self, index, name, attr_pattern=None, expr_pattern=None, values=[]):
        super().__init__(index, name, AttrType.NOMINAL,
                         attr_pattern, expr_pattern)
        self._values = values.copy()

    def scale(self, value):
        return value == self._expr_pattern

    def update(self, value, none_val):
        if value not in self._values and value != none_val:
            self._values.append(value)
        return self

    def print_self(self, out):
        super().print_self(out)
        print(', '.join(self._values), file=out)

    def arff_repr(self, sep):
        return '{ ' + sep.join(self._values) + ' }'

    def data_repr(self, sep):
        return sep.join(self._values)


class AttrScaleString(AttrScale):
    def __init__(self, index, name, attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, AttrType.STRING,
                         attr_pattern, expr_pattern)
        if self._expr_pattern:
            self._regex = re.compile(self._expr_pattern)

    def scale(self, value):
        return bool(self._regex.search(value))

    def arff_repr(self, sep):
        return AttrType.STR_REPR[self.attr_type]

    def data_repr(self, sep):
        return "discrete n"
