"""Attributes classes for application swift"""

import re


class AttrType:
    NUMERIC = 0
    NOMINAL = 1
    STRING = 2
    NOT_SPECIFIED = 3


class Attribute:
    def __init__(self, index, name, attr_type=AttrType.NOT_SPECIFIED):
        self._name = name
        self._index = index
        self._attr_type = attr_type

    types = {'n': AttrType.NUMERIC,
             'e': AttrType.NOMINAL,
             's': AttrType.STRING}

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return self._index

    @property
    def attr_type(self):
        return self._attr_type


class AttrScale(Attribute):
    def __init__(self, index, name, attr_type,
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
    def __init__(self, index, name, attr_pattern, expr_pattern):
        super().__init__(index, name, AttrType.NUMERIC,
                         attr_pattern, expr_pattern)

    def scale(self, attrs, values):
        x = int(super().scale(attrs, values))  # NOQA
        return eval(self._expr_pattern)


class AttrScaleEnum(AttrScale):
    def __init__(self, index, name, attr_pattern, expr_pattern):
        super().__init__(index, name, AttrType.NOMINAL,
                         attr_pattern, expr_pattern)

    def scale(self, attrs, values):
        old_val = super().scale(attrs, values)
        return old_val == self._expr_pattern


class AttrScaleString(AttrScale):
    def __init__(self, index, name, attr_pattern, expr_pattern):
        super().__init__(index, name, AttrType.STRING,
                         attr_pattern, expr_pattern)
        self._regex = re.compile(self._expr_pattern)

    def scale(self, attrs, values):
        old_val = super().scale(attrs, values)
        if self._regex.search(old_val):
            return True
        else:
            return False
