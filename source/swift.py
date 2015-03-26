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

    def prepare(self):
        """
        Prepare information about data.
        Create attributes and objects
        Set index of line where data start.
        Prepare data witch will be converted, get as much
        as possible information from data.
        Call this method if data file is not target in scaling and
        it is old_file.
        """

        if self._str_attrs:
            splitted = self._str_attrs.split(self._separator)
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
        return list(map(lambda s: s.strip(), line.split(self._separator)))

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

    def write_header(self, relation_name=''):
        pass


class DataArff(Data):
    pass


class DataCsv(Data):
    def write_header(self, target, relation_name=''):
        attrs_name = []
        for attr in self._attributes:
            attrs_name.append(attr.name)
        self.write_line_to_file(attrs_name, target, self._separator)


class DataBivalent(Data):
    def parse_old_attrs_for_scale(self, str_attrs):
        """
        Take into _attributes dictionary,
        where key are strings and values are indexes
        of attributes (this slot is rwritten).
        Call this method to use data object as pattern in scaling.
        """
        values = str_attrs.split(',')
        self._attributes_temp = {val: i for i, val in enumerate(values)}

    def parse_new_attrs_for_scale(self, str_attrs):
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
        values = attr_pattern.findall(str_attrs)
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
                                  attr_pattern,
                                  expr_pattern)
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

    def write_header(self, target, relation_name=''):
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
                 separator=','):
        super().__init__(source, str_attrs, str_objects, ' ')

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
    def __init__(self, old_data_file, new_data_file,
                 old_str_attrs=None, old_str_objects=None,
                 new_str_attrs=None, new_str_objects=None,
                 old_data_sep=',', new_data_sep=','):

        self._scaling = False
        # suffixes of input files
        old_suff = os.path.splitext(old_data_file)[1]
        new_suff = os.path.splitext(new_data_file)[1]

        self._old_data = Convertor.extensions[old_suff](old_data_file,
                                                        old_str_attrs,
                                                        old_str_objects,
                                                        old_data_sep)
        self._new_data = Convertor.extensions[new_suff](new_data_file,
                                                        new_str_attrs,
                                                        new_str_objects,
                                                        new_data_sep)
        # get information from source data
        self._old_data.get_info()

        # check if should scale
        if (old_suff == '.csv' or
            old_suff == '.arff') and (new_suff == '.dat' or
                                      new_suff == '.cxt'):
            self._scaling = True
            self._new_data.parse_old_attrs_for_scale(old_str_attrs)
            self._new_data.parse_new_attrs_for_scale(new_str_attrs)

    """class variables"""
    extensions = {'.csv': DataCsv,
                  '.arff': DataArff,
                  '.dat': DataDat,
                  '.cxt': DataCxt}

    def convert(self):
        target_file = open(self._new_data.source, 'w')
        # TODO přidat jako parametr old file, aby mohla metoda write_header
        # jeho využít atributů a aobjektů pokud bude chtít
        self._new_data.write_header(target_file)

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


old_attrs = 'age,note,sex'

# atributes for scaling
new_attrs = "AGE=age[x<50]n, NOTE=note[aaa]s, MAN=sex[man]e, WOMAN=sex[woman]e"

# obejcts
new_objects = 'Jan,Petr,Lucie,Jana,Aneta'

convertor = Convertor("test.cxt", "test_from_cxt.csv",
                      # old_str_attrs=old_attrs,
                      new_str_attrs='AGE,NOTE,MAN,WOMAN',
                      new_str_objects=new_objects,
                      old_data_sep=';')
convertor.convert()
"""


# Regular expression
pattern = re.compile("(\w+)=(\w+)" +
                     "((?:\((?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+\)i)|" +  # NOQA
                     "(?:\(.*\)r))?")

attrs = pattern.findall("a=b, novy1=puvodni1(10<=x<=100)i, novy2=puvodni2(x<=50)i, novy3=puvodni3(man)r")

"""
