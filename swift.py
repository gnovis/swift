#!/bin/python3
"""Main file of swift - FCA data converter"""

import re


class Attribute:
    def __init__(self, index, name, attr_type):
        self._name = name
        self._index = index
        self._attr_type = attr_type

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return self._index

    @property
    def attr_type(self):
        return self._attr_type

    class AttrType:
        NUMERIC = 0
        NOMINAL = 1
        STRING = 2


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
        super().__init__(index, name, self.AttrType.NUMERIC,
                         attr_pattern, expr_pattern)

    def scale(self, attrs, values):
        x = super().scale(attrs, values)  # NOQA
        return eval(self._expr_pattern)  # int cast, because want 0 or 1


class AttrScaleEnum(AttrScale):
    def __init__(self, index, name, attr_pattern, expr_pattern):
        super().__init__(index, name, self.AttrType.NOMINAL,
                         attr_pattern, expr_pattern)

    def scale(self, attrs, values):
        old_val = super().scale(attrs, values)
        return old_val == self._expr_pattern


class AttrScaleString(AttrScale):
    def __init__(self, index, name, attr_pattern, expr_pattern):
        super().__init__(index, name, self.AttrType.STRING,
                         attr_pattern, expr_pattern)
        self._regex = re.compile(self._expr_pattern)

    def scale(self, attrs, values):
        old_val = super().scale(attrs, values)
        if self._regex.search(old_val):
            return True
        else:
            return False


class Object:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


class DataFile:
    attr_pattern = re.compile(
        "(\w+)=(\w+)((?:\((?:[0-9]+(?:>=|<=|>|<))?x" +
        "(?:>=|<=|>|<)[0-9]+\)i)|(?:\(.*\)r))?")

    def __init__(self, str_attrs, str_objects):
        pass

    def make_attrs(self, str_attrs):
        pass
        # attributes = []
        # for attr in attr_pattern.findall(str_attrs):


# Tests
attrs_old = {val: i for i, val in enumerate(['age', 'note', 'sex'])}
values = [50, '00000ah21jky', "woman"]

attr = AttrScaleNumeric(0, 'scale-age', 'age', '(x<70)')
print(attr.scale(attrs_old, values))

attr2 = AttrScaleEnum(2, 'scale-sex', 'sex', 'man')
print(attr2.scale(attrs_old, values))

attr3 = AttrScaleString(1, 'scale-note', 'note', 'ah[123]j')
print(attr3.scale(attrs_old, values))


"""
#create dict from list
#{val : i for i, val in enumerate(l)}

pattern = re.compile("(\w+)=(\w+)" +
                     "((?:\((?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+\)i)|" +  # NOQA
                     "(?:\(.*\)r))?")

attrs = pattern.findall("a=b, novy1=puvodni1(10<=x<=100)i, novy2=puvodni2(x<=50)i, novy3=puvodni3(man)r")

for at in attrs:
    print at

m = "(a[ho?j]ky)r"
new = m[1:-2]
print new
"""
