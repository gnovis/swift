"""Attributes classes for swift"""

from __future__ import print_function
import re
from collections import OrderedDict
from pyparsing import quotedString, removeQuotes, ParseException
from .date_parser_fca import DateParser
from .grammars_fca import boolexpr
from .constants_fca import Bival, AttrType
from .errors_fca import InvalidValueError, DateSyntaxError, DateValFormatError, FormulaRegexError


class Attribute:
    def __init__(self, index, name, attr_type=AttrType.NOT_SPECIFIED,
                 attr_pattern=None, expr_pattern=None):
        # name of atrribute, it is pattern to scaling
        self._attr_pattern = attr_pattern
        # expression to scaling
        self._expr_pattern = expr_pattern
        self._name = name
        self._index = index
        self._attr_type = attr_type
        self._children = []
        self._values_rate = OrderedDict()
        self._none_val = None
        self._none_val_count = 0
        self._true = Bival.true()
        self._false = Bival.false()
        self._unpack = False
        self._is_class = False

    @property
    def key(self):
        if self._attr_pattern:
            return self._attr_pattern
        if self._name:
            return self._name
        return str(self.index)

    @property
    def attr_pattern(self):
        return self._attr_pattern

    @property
    def all_vals(self):
        return list(self._values_rate.keys())

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def is_class(self):
        return self._is_class

    @is_class.setter
    def is_class(self, value):
        self._is_class = bool(value)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    @property
    def attr_type(self):
        return self._attr_type

    @property
    def children(self):
        return self._children.copy()

    @children.setter
    def children(self, children):
        self._children = children

    @property
    def true(self):
        return self._true

    @true.setter
    def true(self, value):
        self._true = value

    @property
    def false(self):
        return self._false

    @false.setter
    def false(self, value):
        self._false = value

    @property
    def unpack(self):
        return self._unpack

    @unpack.setter
    def unpack(self, value):
        self._unpack = value

    def process(self, value, none_val, scale, update):
        if self._expr_pattern and scale:
            if none_val and value == none_val:  # result of scaling none value is False
                return Bival.false()
            return self.scale(value)
        if update:
            self.update(value, none_val)
        return value

    def scale(self, value):
        return Bival.convert(value)

    def has_children(self):
        return bool(self._children)

    def print_self(self, out):
        print("\nname: {}\nindex: {}\ntype: {}".format(
            self.name,
            self.index, AttrType.STR_REPR[self.attr_type]), file=out)
        print(self.get_formated_rate(), file=out)

    def update(self, value, none_val, step=1):
        if value != none_val:
            if value in self._values_rate:
                self._values_rate[value] += step
            else:
                self._values_rate[value] = step
        else:
            self._none_val_count += 1
            self._none_val = none_val

    def get_formated_rate(self, aux_func=str):
        rate_sum = sum(self._values_rate.values()) + self._none_val_count
        rate_row = "    {}: {}/{} = {:.2%} {}\n"
        result = "values appearance:\n"
        if self._none_val_count:
            result += rate_row.format(self._none_val, self._none_val_count, rate_sum, self._none_val_count/rate_sum, "(none value)")
        sorted_rate = OrderedDict(sorted(self._values_rate.items(), key=lambda t: t[1]))
        for key, value in sorted_rate.items():
            result += rate_row.format(aux_func(key), value, rate_sum, value/rate_sum, "")
        return result.strip()

    def arff_repr(self, sep):
        return '{ ' + Bival.false() + sep + Bival.true() + ' }'

    def data_repr(self, sep):
        return Bival.false() + sep + Bival.true()


class AttrNumeric(Attribute):
    ERROR_MSG = "Value must be numeric (integer or real)"

    def __init__(self, index, name, attr_type=AttrType.NUMERIC, attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, attr_type,
                         attr_pattern, expr_pattern)
        if self._expr_pattern:
            subst_expr_pattern = re.sub(r"[^<>!=0-9\s.]+", "x", self._expr_pattern)
            self._evaled_expr_func = eval('lambda x:' + subst_expr_pattern)

    def scale(self, value):
        try:
            x = float(value)
        except ValueError:
            raise InvalidValueError(AttrType.NUMERIC, self.ERROR_MSG)
        return super().scale(self._evaled_expr_func(x))

    def update(self, value, none_val, step=1):
        if value != none_val:
            try:
                value = float(value)
            except ValueError:
                raise InvalidValueError(AttrType.NUMERIC, self.ERROR_MSG)

        super().update(value, none_val, step)

    def get_formated_rate(self, aux_func=str):
        max_val = max(self._values_rate.keys())
        min_val = min(self._values_rate.keys())
        result = "max: {}, min: {}\n".format(aux_func(max_val), aux_func(min_val))
        result += super().get_formated_rate(aux_func)
        return result

    def arff_repr(self, sep):
        return AttrType.STR_REPR[self.attr_type]

    def data_repr(self, sep):
        return "continuous"


class AttrDate(AttrNumeric):
    def __init__(self, index, name, date_format=DateParser.ISO_FORMAT,
                 attr_type=AttrType.DATE, attr_pattern=None, expr_pattern=None):
        self.parser = DateParser(date_format)
        self._expr_pattern = expr_pattern
        if expr_pattern:
            self.substitute_date()
        super().__init__(index, name, attr_type, attr_pattern, self._expr_pattern)

    @property
    def max_value(self):
        return self.parser.time_stamp_to_str(self._max_value)

    @property
    def min_value(self):
        return self.parser.time_stamp_to_str(self._min_value)

    def substitute_date(self):
        def action(s, loc, tokens):
            try:
                return self.parser.get_time_stamp(removeQuotes(s, loc, tokens))
            except ValueError as e:
                raise DateValFormatError(e)

        DATEXPR = quotedString.copy()
        EXPR = boolexpr(VAL=DATEXPR)
        DATEXPR.setParseAction(action)
        try:
            self._expr_pattern = EXPR.parseString(self._expr_pattern, parseAll=True)[0]
        except ParseException as e:
            raise DateSyntaxError(e.lineno, e.col, e.line, e)

    def scale(self, value):
        try:
            time_stamp = self.parser.get_time_stamp(value)
        except ValueError as e:
            raise InvalidValueError(AttrType.DATE, e)
        return super().scale(time_stamp)

    def update(self, str_date, none_val, step=1):
        if str_date != none_val:
            try:
                time_stamp = self.parser.get_time_stamp(str_date)
            except ValueError as e:
                raise InvalidValueError(AttrType.DATE, e)
            super().update(time_stamp, none_val, step)

    def get_formated_rate(self, aux_func=str):
        return super().get_formated_rate(aux_func=self.parser.time_stamp_to_str)

    def arff_repr(self, sep):
        return "{} {}".format(AttrType.STR_REPR[self.attr_type], self.parser.get_format())

    def data_repr(self, sep):
        return "discrete n"


class AttrEnum(Attribute):
    def __init__(self, index, name, attr_pattern=None, expr_pattern=None, values=[]):
        super().__init__(index, name, AttrType.NOMINAL,
                         attr_pattern, expr_pattern)
        self._values = values.copy()

    @property
    def values(self):
        return self._values.copy()

    def scale(self, value):
        return super().scale(value == self._expr_pattern)

    def update(self, value, none_val, step=1):
        if value not in self._values and value != none_val:
            self._values.append(value)
        super().update(value, none_val, step)
        return self

    def arff_repr(self, sep):
        return '{ ' + sep.join(self._values) + ' }'

    def data_repr(self, sep):
        return sep.join(self._values)


class AttrString(Attribute):
    def __init__(self, index, name, attr_pattern=None, expr_pattern=None):
        super().__init__(index, name, AttrType.STRING,
                         attr_pattern, expr_pattern)
        if self._expr_pattern:
            try:
                self._regex = re.compile(self._expr_pattern)
            except re.error as e:
                raise FormulaRegexError("{}: '{}'".format(e, self._expr_pattern))

    def scale(self, value):
        return super().scale(bool(self._regex.search(value)))

    def arff_repr(self, sep):
        return AttrType.STR_REPR[self.attr_type]

    def data_repr(self, sep):
        return "discrete n"
