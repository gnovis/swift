"""Attributes classes for swift"""

from __future__ import print_function
import re
from pyparsing import quotedString
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
    def __init__(self, index, name, attr_type=AttrType.NOT_SPECIFIED):
        self._name = name
        self._index = index
        self._attr_type = attr_type

    types = {'n': AttrType.NUMERIC,
             'e': AttrType.NOMINAL,
             's': AttrType.STRING,
             'd': AttrType.DATE}

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return self._index

    @property
    def attr_type(self):
        return self._attr_type

    def print_self(self, out):
        print("\nname: {}\nindex: {}\ntype: {}".format(
            self.name,
            self.index, AttrType.STR_REPR[self.attr_type]), file=out)

    def update(self, value):
        pass

    def arff_repr(self, sep, bi_val1='0', bi_val2='1'):
        return '{ ' + bi_val1 + sep + bi_val2 + ' }'

    def data_repr(self, sep, bi_val1='0', bi_val2='1'):
        return bi_val1 + sep + bi_val2


class AttrScale(Attribute):
    def __init__(self, index, name, attr_type=AttrType.NOT_SPECIFIED,
                 attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, attr_type)

        # name of atrribute, it is pattern to scaling
        self._attr_pattern = attr_pattern
        # expression to scaling
        self._expr_pattern = expr_pattern

    def scale(self, attrs, values):
        """
        Scale value according pattern.
        attrs - dict with names(keys) and indexes(values)
        values - values of current procces row
        """
        val_index = attrs[self._attr_pattern]
        return values[val_index]


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

    def scale(self, attrs, values):
        try:
            x = int(super().scale(attrs, values))  # NOQA
        except ValueError:
            # if value is not integer(is string or undefined e.g None, "" or ?) =>
            # result of scaling is false
            return False
        replaced = re.sub(r"[^<>=0-9\s.]+", "x", self._expr_pattern)
        return eval(replaced)

    def update(self, str_value):
        try:
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
        except ValueError:
            pass

    def print_self(self, out):
        super().print_self(out)
        print("max value: {}\nmin value: {}".format(
              self.max_value, self.min_value), file=out)

    def arff_repr(self, sep, bi_val1='0', bi_val2='1'):
        return AttrType.STR_REPR[self.attr_type]

    def data_repr(self, sep, bi_val1='0', bi_val2='1'):
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
        DATEXPR.setParseAction(lambda tokens: self.parser.get_time_stamp(tokens[0][1:-1]))
        self._expr_pattern = EXPR.parseString(self._expr_pattern)[0]

    def scale(self, attrs, values):
        val_i = attrs[self._attr_pattern]
        str_date = values[val_i]
        time_stamp = self.parser.get_time_stamp(str_date)
        new_values = values.copy()
        new_values[val_i] = time_stamp
        return super().scale(attrs, new_values)

    def update(self, str_date):
        time_stamp = self.parser.get_time_stamp(str_date)
        super().update(time_stamp)

    def arff_repr(self, sep, bi_val1='0', bi_val2='1'):
        return "{} {}".format(AttrType.STR_REPR[self.attr_type], self.parser.get_format())

    def data_repr(self, sep, bi_val1='0', bi_val2='1'):
        return "discrete n"


class AttrScaleEnum(AttrScale):
    def __init__(self, index, name, attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, AttrType.NOMINAL,
                         attr_pattern, expr_pattern)
        self._values = []

    def scale(self, attrs, values):
        old_val = super().scale(attrs, values)
        return old_val == self._expr_pattern

    def update(self, value):
        if value not in self._values:
            self._values.append(value)
        return self

    def print_self(self, out):
        super().print_self(out)
        print(', '.join(self._values), file=out)

    def arff_repr(self, sep, bi_val1='0', bi_val2='1'):
        return '{ ' + sep.join(self._values) + ' }'

    def data_repr(self, sep, bi_val1='0', bi_val2='1'):
        return sep.join(self._values)


class AttrScaleString(AttrScale):
    def __init__(self, index, name, attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, AttrType.STRING,
                         attr_pattern, expr_pattern)
        if self._expr_pattern:
            self._regex = re.compile(self._expr_pattern)

    def scale(self, attrs, values):
        old_val = super().scale(attrs, values)
        if self._regex.search(old_val):
            return True
        else:
            return False

    def arff_repr(self, sep, bi_val1='0', bi_val2='1'):
        return AttrType.STR_REPR[self.attr_type]

    def data_repr(self, sep, bi_val1='0', bi_val2='1'):
        return "discrete n"
