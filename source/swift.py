#!/bin/python3
"""Main file of swift - FCA data converter"""

import re
import os

from attributes import (Attribute, AttrType, AttrScale, AttrScaleNumeric,
                        AttrScaleEnum, AttrScaleString)


class Object:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


class Data:
    """Base class of all data"""
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=','):
        """
        str_ before param name means that it is
        string representation and must be parsed
        """
        self._objects = []
        self._attributes = []
        self._source = source
        self._str_attrs = str_attrs
        self._str_objects = str_objects
        self._separator = separator
        self._index_data_start = 0
        self.prepare()

    @property
    def source(self):
        return self._source

    @property
    def str_attrs(self):
        return self._str_attrs

    @property
    def str_objects(self):
        return self._str_objects

    @property
    def separator(self):
        return self._separator

    @property
    def index_data_start(self):
        return self._index_data_start

    @property
    def attributes(self):
        return list(self._attributes)

    def prepare(self):
        if self._str_attrs:
            splitted = Data.ss_str(self._str_attrs, self.separator)
            for i, str_attr in enumerate(splitted):
                attr_type = AttrType.NOT_SPECIFIED
                attr_name = str_attr
                if str_attr[-1] == ']':
                    attr_type = Attribute.types[str_attr[-2]]
                    attr_name = str_attr[:-3]
                self._attributes.append(Attribute(i, attr_name, attr_type))

        if self._str_objects:
            splitted = self._str_objects.split(self._separator)
            self._objects = [Object(name) for name in splitted]

    def get_info(self):
        pass

    def prepare_line(self, line):
        return Data.ss_str(line, self.separator)

    def write_line_to_file(self, line, target_file, separator):
        """
        Aux function for write_line, only add \n to line and
        write complitely prepared line to file"""
        line = separator.join(line)
        line += '\n'
        target_file.write(line)

    def write_line(self, prepered_line, target):
        """
        Will write data to output in new format
        based on old_values - list of string values
        """
        self.write_line_to_file(prepered_line, target, self._separator)

    def write_header(self, target, old_data=None, relation_name=''):
        pass

    def ss_str(string, separator):
        """
        Strip and split string by separator.
        Return list of values.
        """
        return list(map(lambda s: s.strip(), string.split(separator)))


class DataArff(Data):
    pass


class DataCsv(Data):
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', attrs_first_line=False):
        if attrs_first_line:
            str_attrs = self.get_first_line_attrs(source)
        self._attrs_first_line = attrs_first_line
        super().__init__(source, str_attrs, str_objects, separator)

    def get_first_line_attrs(self, source):
        """Set str_attrs to first line from data file"""
        with open(source, 'r') as f:
            return next(f)

    def write_header(self, target, old_data=None, relation_name=''):
        attrs_to_write = []
        if self._attributes:
            attrs_to_write = self._attributes
        elif old_data and old_data.attributes:
            attrs_to_write = old_data.attributes

        attrs_name = []
        for attr in attrs_to_write:
            attrs_name.append(attr.name)
        self.write_line_to_file(attrs_name, target, self._separator)

    def get_info(self):
        if self._attrs_first_line:
            self._index_data_start = 1


class DataBivalent(Data):
    def parse_old_attrs_for_scale(self, old_str_attrs, separator):
        """
        Take into _attributes dictionary,
        where key are strings and values are indexes
        of attributes (this slot is rwritten).
        Call this method to use data object as pattern in scaling.
        """
        values = Data.ss_str(old_str_attrs, separator)
        self._attributes_temp = {val: i for i, val in enumerate(values)}

    def parse_new_attrs_for_scale(self):
        """
        Parse and create list of scale attributes,
        take it into _attributes (this slot is rewritten).
        Call this method to use data as target in scaling.
        """
        attr_classes = {'n': AttrScaleNumeric,
                        'e': AttrScaleEnum,
                        's': AttrScaleString}
        attr_pattern = re.compile(
            "(\w+)=(\w+)" +
            "((?:\[(?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+\]n)" +
            "|(?:\[\w+\]e)|(?:\[.+\]s))?")
        values = attr_pattern.findall(self.str_attrs)
        self._attributes = []
        for i, attr in enumerate(values):
            new_name = attr[0]
            attr_pattern = attr[1]
            formula = attr[2]

            if formula == '':
                attr_class = AttrScale
                expr_pattern = ''
            else:
                attr_class = attr_classes[formula[-1]]
                expr_pattern = formula[1:-2]

            new_attr = attr_class(i, new_name,
                                  attr_pattern=attr_pattern,
                                  expr_pattern=expr_pattern)
            self._attributes.append(new_attr)

    def write_data_scale(self, old_values, output, dict_old_attrs):
        """
        Will write scaled data to output in new format
        based on old_values - list of string values
        dict_old_attrs = Dictionary where key is name of
        attribute and value is index of this attribute.
        """
        pass


class DataCxt(DataBivalent):
    sym_vals = {'X': 1, '.': 0}
    vals_sym = {1: 'X', 0: '.'}

    def get_info(self):
        with open(self._source) as f:
            next(f)  # skip B
            next(f)  # skip blank line
            rows = int(next(f).strip())
            columns = int(next(f).strip())
            next(f)  # skip blank line
            index = 5
            for i in range(rows):
                self._objects.append(Object(next(f).strip()))
                index += 1
            for k in range(columns):
                self._attributes.append(Attribute(k, next(f).strip()))
                index += 1
            self._index_data_start = index

    def prepare_line(self, line):
        splitted = list(line.strip())
        result = []
        for val in splitted:
            result.append(str(DataCxt.sym_vals[val]))
        return result

    def write_header(self, target, old_data=None, relation_name=''):
        if not self._attributes:
            self._attributes = old_data.attributes

        target.write('B\n\n')
        target.write(str(len(self._objects))+'\n')
        target.write(str(len(self._attributes))+'\n\n')
        for obj in self._objects:
            target.write(obj.name + '\n')
        for attr in self._attributes:
            target.write(attr.name + '\n')

    def write_data_scale(self, values, target_file):
        result = []
        for i, attr in enumerate(self._attributes):
            scaled = attr.scale(self._attributes_temp, values)
            result.append(DataCxt.vals_sym[int(scaled)])
        self.write_line_to_file(result, target_file, '')

    def write_line(self, prepared_line, target_file):
        result = []
        for val in prepared_line:
            result.append(DataCxt.vals_sym[int(val)])
        self.write_line_to_file(result, target_file, '')


class DataDat(DataBivalent):
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=' '):
        super().__init__(source, str_attrs, str_objects, separator)

    def get_info(self):
        max_val = -1
        line_count = 0
        with open(self._source, 'r') as f:
            for i, line in enumerate(f):
                line_count += 1
                splitted = super().prepare_line(line)
                for val in splitted:
                    int_val = int(val)
                    if int_val > max_val:
                        max_val = int_val
        self._attrs_count = max_val
        self._objects_count = line_count

    def prepare_line(self, line):
        splitted = super().prepare_line(line)
        result = ['0'] * (self._attrs_count + 1)
        for val in splitted:
            result[int(val)] = str(1)
        return result

    def write_data_scale(self, values, target_file):
        result = []
        for i, attr in enumerate(self._attributes):
            scaled = attr.scale(self._attributes_temp, values)
            if scaled:
                result.append(str(i))
        self.write_line_to_file(result, target_file, self._separator)

    def write_line(self, line, target_file):
        result = []
        for i, val in enumerate(line):
            if bool(int(val)):
                result.append(str(i))
        self.write_line_to_file(result, target_file, self._separator)


class Convertor:
    def __init__(self, old, new):

        # suffixes of input files
        old_suff = os.path.splitext(old['source'])[1]
        new_suff = os.path.splitext(new['source'])[1]

        self._old_data = Convertor.extensions[old_suff](**old)
        self._new_data = Convertor.extensions[new_suff](**new)

        # get information from source data
        self._old_data.get_info()

        # check if should scale
        self._scaling = False
        if (old_suff == '.csv' or
            old_suff == '.arff') and (new_suff == '.dat' or
                                      new_suff == '.cxt'):
            self._scaling = True
            self._new_data.parse_old_attrs_for_scale(self._old_data.str_attrs,
                                                     self._old_data.separator)
            self._new_data.parse_new_attrs_for_scale()

    """class variables"""
    extensions = {'.csv': DataCsv,
                  '.arff': DataArff,
                  '.dat': DataDat,
                  '.cxt': DataCxt}

    def convert(self):
        """Call this method to convert data"""

        target_file = open(self._new_data.source, 'w')
        # write header part
        self._new_data.write_header(target_file, old_data=self._old_data)
        with open(self._old_data.source, 'r') as f:
            # skip header lines
            for k in range(self._old_data.index_data_start):
                next(f)
            for i, line in enumerate(f):
                prepared_line = self._old_data.prepare_line(line)
                if self._scaling:
                    self._new_data.write_data_scale(prepared_line,
                                                    target_file)
                else:
                    self._new_data.write_line(prepared_line,
                                              target_file)
        target_file.close()


# Notes
#
# Testovano:
# csv -> dat
# csv -> cxt
# dat -> csv
# dat -> cxt
# cxt -> dat
# cxt -> csv


# Tests

old_str_attrs = 'age,note,sex'

# atributes for scaling
new_str_attrs = "AGE=age[x<50]n, NOTE=note[aaa]s, NUMBER=num, MAN=sex[man]e, WOMAN=sex[woman]e"  # NOQA

# obejcts
new_str_objects = 'Jan,Petr,Lucie,Jana,Aneta'

old = dict(source="test.csv",
           separator=";",
           attrs_first_line=True)
new = dict(source="csv.cxt",
           str_objects=new_str_objects,
           str_attrs=new_str_attrs)

convertor = Convertor(old, new)
convertor.convert()


"""
# Regular expression
pattern = re.compile("(\w+)=(\w+)" +
                     "((?:\((?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+\)i)|" +  # NOQA
                     "(?:\(.*\)r))?")

attrs = pattern.findall("a=b, novy1=puvodni1(10<=x<=100)i, novy2=puvodni2(x<=50)i, novy3=puvodni3(man)r")

"""