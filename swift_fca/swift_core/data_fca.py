from __future__ import print_function
import re
import os
import sys
import tempfile

from .attributes_fca import (Attribute, AttrScaleEnum)
from .object_fca import Object
from .parser_fca import ArgsParser, ArffParser, DataParser


class Data:
    """Base class of all data"""

    """Class data"""

    LEFT_BRACKET = '['
    RIGHT_BRACKET = ']'
    NONE_VAL = "?"

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', none_val=NONE_VAL):
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
        self._relation_name = relation_name
        self._none_val = none_val
        self._index_data_start = 0
        self._obj_count = 0
        self._attr_count = 0

        self._temp_source = None
        if not self.source.seekable():
            self._temp_source = tempfile.TemporaryFile(mode='w+t', dir='./')

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
        return self._attributes.copy()

    @property
    def relation_name(self):
        return self._relation_name

    @property
    def obj_count(self):
        """Does not depends on objects property"""
        return self._obj_count

    @property
    def attr_count(self):
        """Does not depends on attributes property"""
        return self._attr_count

    def prepare(self):
        if self.str_attrs:
            parser = ArgsParser()
            parser.parse(self.str_attrs)
            self._attributes = parser.attributes

        if self.str_objects:
            splitted = self.ss_str(self._str_objects, self.separator)
            self._objects = [Object(name) for name in splitted]

    def get_header_info(self):
        """
        Set attributes, objects, relation name and index_data_start.
        """
        pass

    def get_data_info(self, manager=None):
        """Get much as possible information about data"""
        # self._attr_count = len(self._attributes)
        # with open(self.source, 'r') as f:
        #     Data.skip_lines(self.index_data_start, f)
        #     for index, line in enumerate(f):
        #         str_values = self.prepare_line(line)
        #         if not str_values:  # current line is comment
        #             continue
        #         self._obj_count += 1
        #         for i, attr in enumerate(self._attributes):
        #             attr.update(str_values[i], self._none_val)
        #         if manager:
        #             if manager.stop:
        #                 break
        #             manager.update_counter(line, self.index_data_start)

        self._attr_count = len(self._attributes)
        for index, line in enumerate(self.source):
            str_values = self.prepare_line(line)
            if not str_values:  # current line is comment
                continue
            self._obj_count += 1
            for i, attr in enumerate(self._attributes):
                attr.update(str_values[i], self._none_val)

            if self._temp_source:
                self._temp_source.write(line)

            if manager:
                if manager.stop:
                    break
                manager.update_counter(line, self.index_data_start)

        if self._temp_source:
            self._source = self._temp_source
        self._source.seek(0)

    def get_data_info_for_browse(self, manager=None):
        pass

    def prepare_line(self, line):
        """If return empty list -> line is comment"""
        return self.ss_str(line, self.separator)

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

    def write_header(self, target, old_data):
        """This method should be rewritten in child class"""
        # write attributes
        if self._attributes:  # attributes are passed as parameter
            attrs_to_write = self._attributes
        else:
            attrs_to_write = old_data.attributes  # attributes are readed from source(old) file
        return attrs_to_write

    def ss_str(self, string, separator, max_split=0):
        """
        Strip and split string by separator. Ignore escaped separators.
        Return list of values.
        """
        return list(map(lambda x: x.strip(),
                    re.split(r'(?<!\\)' + separator, string, max_split)))

    def get_not_empty_line(self, f):
        file_iter = iter(f)
        while True:
            line = next(file_iter).strip()
            if line:
                return line

    def print_info(self, out_file=sys.stdout):
        print("Relation name: {}".format(self.relation_name), file=out_file)
        print("Objects count: {}".format(self.obj_count), file=out_file)
        print("Attributes count: {}".format(self.attr_count), file=out_file)
        print("="*20, file=out_file)
        for attr in self._attributes:
            attr.print_self(out_file)

    def skip_lines(line_i, f):
        file_iter = iter(f)
        for i in range(line_i):
            next(file_iter)


class DataArff(Data):
    """
    Attribute-Relation File Format

    Pattern:
    ========
    @RELATION <relation-name>
    @ATTRIBUTE <attribute-name> <attribute-type>
    @DATA
    <obj1-attr1>, <obj2-attr2> ....

    Sample:
    =======
    @RELATION iris
    @ATTRIBUTE sepallength  NUMERIC
    @ATTRIBUTE petalwidth   STRING
    @ATTRIBUTE class        {Iris-setosa,Iris-versicolor,Iris-virginica}
    @ATTRIBUTE timestamp DATE yyyy-MM-dd HH:mm:ss
    @DATA
    5, lot, Iris-versicolor, 2001-04-03 12:12:12

    """

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='',
                 none_val=Data.NONE_VAL):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val)
        self._parser = ArffParser(separator)

    NUMERIC = "numeric"
    STRING = "string"
    DATE = "date"

    ATTRIBUTE = "@attribute"
    RELATION = "@relation"
    DATA = "@data"

    def write_header(self, target, old_data):
        if not self.relation_name and old_data:
            self._relation_name = old_data.relation_name

        # write relation name
        target.write(self.RELATION + ' ' + self.relation_name + '\n\n')

        attrs_to_write = super().write_header(target, old_data)
        for attr in attrs_to_write:
            line = (self.ATTRIBUTE + ' ' + str(attr.name) + ' '
                    + attr.arff_repr(self.separator,
                                     DataBivalent.bi_vals['neg'],
                                     DataBivalent.bi_vals['pos']) + '\n')
            target.write(line)

        # write data symbol
        target.write('\n' + self.DATA + '\n')

    def get_header_info(self):
        header = self._get_header_str()
        self._parser.parse(header)
        self._relation_name = self._parser.relation_name
        self._index_data_start = self._parser.data_start
        self._attributes = self._parser.attributes

    def prepare_line(self, line):
        return self._parser.parse_line(line)

    def _get_header_str(self):
        # with open(self.source, 'r') as f:
        #     header_to_parse = ''
        #     for line in f:
        #         header_to_parse += line
        #         if line.strip() == '@data':
        #             break

        header_to_parse = ''
        for line in self.source:
            header_to_parse += line
            if self._temp_source:
                self._temp_source.write(line)
            if line.strip() == '@data':
                break
        return header_to_parse


class DataCsv(Data):
    """Column seperated value format"""
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', no_attrs_first_line=False,
                 none_val=Data.NONE_VAL):
        self._no_attrs_first_line = no_attrs_first_line
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val)

    def write_header(self, target, old_data):
        attrs_to_write = super().write_header(target, old_data)
        attrs_name = []
        for attr in attrs_to_write:
            attrs_name.append(attr.name)
        self.write_line_to_file(attrs_name, target, self._separator)

    def get_header_info(self):
        if not self._no_attrs_first_line:  # attrs are on first line
            self._index_data_start = 1
            if not self._str_attrs:
                line = self._get_first_line()
                str_values = self.ss_str(line, self.separator)
                self._attributes = [Attribute(i, name) for i, name in enumerate(str_values)]
            else:
                next(self._source)  # skip first line with attributes
        elif not self._str_attrs:  # attrs are not of first line and are not passed as parameter
            line = self._get_first_line(False)
            str_values = self.ss_str(line, self.separator)
            self._attr_count = len(str_values)
            self._attributes = [Attribute(i, 'attr_' + str(i)) for i in range(self._attr_count)]

    def _get_first_line(self, move=True):
        """Return first line from data file"""
        line = next(self._source)
        if self._temp_source:
            self._temp_source.write(line)
        elif not move:
            self._source.seek(0)
        return line


class DataData(Data):
    """C4.5 data file format"""

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', classes="", none_val=Data.NONE_VAL):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val)
        self._classes = list(reversed(self.ss_str(classes, self._separator)))

    COMMENT_SYM = "\|"
    ATTR_SEP = ":"
    LINE_SEP = "\."
    IGNORE = "ignore"
    CONTINUOUS = "continuous"
    CLASS = "class"

    def write_line(self, prepared_line, target):
        if self._classes:
            prepared_line.append(self._classes.pop())
        super().write_line(prepared_line, target)

    def write_header(self, target, old_data):
        attrs_to_write = super().write_header(target, old_data)
        names_file = self._get_name_file(target.name)

        with open(names_file, 'w') as f:
            f.write(self._get_class_occur() + ".\n")
            for attr in attrs_to_write:
                line = (str(attr.name) + ': '
                        + attr.data_repr(self.separator,
                                         DataBivalent.bi_vals['neg'],
                                         DataBivalent.bi_vals['pos']) + '.\n')
                f.write(line)

    def get_header_info(self):
        parser = DataParser()
        parser.parse(self._get_name_file(self._source.name))
        self._attributes = parser.attributes

    def _get_class_occur(self):
        occur = []
        for c in self._classes:
            if c not in occur:
                occur.append(c)
        return self.separator.join(occur)

    """return file name with suffix .names"""
    def _get_name_file(self, source):
        return ".".join([os.path.splitext(source)[0], "names"])


class DataBivalent(Data):
    """Data represented only by bivalnet values e.g 1/0"""

    bi_vals = {'pos': '1', 'neg': '0'}

    def parse_old_attrs_for_scale(self, old_attrs):
        """
        Take dictionary into _attributes_temp,
        where key are strings and values are indexes
        of attributes.
        Call this method to use data object as pattern in scaling.
        """
        self._attributes_temp = {attr.name: i for i, attr in enumerate(old_attrs)}

    def write_data_scale(self, values, target_file):
        """
        Will write scaled data to output in new format
        based on old_values - list of string values
        dict_old_attrs = Dictionary where key is name of
        attribute and value is index of this attribute.
        """
        pass


class DataCxt(DataBivalent):
    """Burmeister data format"""
    sym_vals = {'X': 1, '.': 0}
    vals_sym = {1: 'X', 0: '.'}

    def get_header_info(self):
        self.get_not_empty_line(self.source)  # skip B
        self._relation_name = self.get_not_empty_line(self.source)

        rows = int(self.get_not_empty_line(self.source))
        columns = int(self.get_not_empty_line(self.source))

        for i in range(rows):
            obj_name = self.get_not_empty_line(self.source)
            self._objects.append(Object(obj_name))

        for k in range(columns):
            attr_name = self.get_not_empty_line(self.source)
            new = AttrScaleEnum(k, attr_name)
            new.update(DataBivalent.bi_vals['pos'], self._none_val)
            new.update(DataBivalent.bi_vals['neg'], self._none_val)
            self._attributes.append(new)

        self._attr_count = columns
        self._obj_count = rows
        # no lines shoud be skipped, because skip was done by next() above!

    def get_data_info(self, manager=None):
        pass

    def prepare_line(self, line):
        splitted = list(line.strip())
        result = []
        for val in splitted:
            result.append(str(DataCxt.sym_vals[val]))
        return result

    def write_header(self, target, old_data):
        attrs_to_write = super().write_header(target, old_data)

        target.write('B\n')
        if not self.relation_name:
            self._relation_name = old_data.relation_name
        target.write(self.relation_name + '\n')
        target.write(str(len(self._objects))+'\n')
        target.write(str(len(attrs_to_write))+'\n')
        for obj in self._objects:
            target.write(obj.name + '\n')
        for attr in attrs_to_write:
            target.write(attr.name + '\n')

    def write_data_scale(self, values, target_file):
        result = []
        for i, attr in enumerate(self._attributes):
            scaled = attr.scale(self._attributes_temp, values)
            result.append(DataCxt.vals_sym[int(scaled)])  # scaled val is converted to 0/1
        self.write_line_to_file(result, target_file, '')

    def write_line(self, prepared_line, target_file):
        result = []
        for val in prepared_line:
            result.append(DataCxt.vals_sym[int(val)])
        self.write_line_to_file(result, target_file, '')


class DataDat(DataBivalent):
    """Data format for FCALGS"""
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name=''):
        super().__init__(source, str_attrs, str_objects,
                         ' ', relation_name)

    def get_data_info(self, manager=None):
        max_val = -1
        line_count = 0
        for i, line in enumerate(self.source):
            line_count += 1
            splitted = super().prepare_line(line)
            for val in splitted:
                if val:
                    int_val = int(val)
                    if int_val > max_val:
                        max_val = int_val

            if self._temp_source:
                self._temp_source.write(line)

            if manager:
                if manager.stop:
                    break
                manager.update_counter(line, self.index_data_start)

        if self._temp_source:
            self._source = self._temp_source
        self._source.seek(0)

        self._attr_count = max_val + 1
        self._obj_count = line_count
        # These attributes are used only if attrs for new file
        # are not specified
        if self._attributes:
            names = [attr.name for attr in self._attributes]
        else:
            names = [str(i) for i in range(self._attr_count)]
        self._attributes = [(AttrScaleEnum(i, name).update(
                            self.bi_vals['pos'], self._none_val)).update(
                                self.bi_vals['neg'], self._none_val)
                            for i, name in enumerate(names)]

    def get_data_info_for_browse(self, manager=None):
        self.get_data_info(manager)

    def prepare_line(self, line):
        splitted = super().prepare_line(line)
        result = ['0'] * (self._attr_count)
        for val in splitted:
            if val:
                result[int(val)] = str(1)
        return result

    def write_data_scale(self, values, target_file):
        result = []
        for i, attr in enumerate(self._attributes):
            scaled = attr.scale(self._attributes_temp, values)
            if bool(int(scaled)):  # scaled value can be from Reals or True/False
                result.append(str(i))
        self.write_line_to_file(result, target_file, self._separator)

    def write_line(self, line, target_file):
        result = []
        for i, val in enumerate(line):
            if bool(int(val)):
                result.append(str(i))
        self.write_line_to_file(result, target_file, self._separator)
