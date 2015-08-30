from __future__ import print_function
import re
import os
import sys
import tempfile

from .attributes_fca import (AttrScale, AttrScaleEnum)
from .object_fca import Object
from .parser_fca import ArgsParser, ArffParser, DataParser


class Data:
    """Base class of all data"""

    """Class data"""

    NONE_VAL = "?"

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', none_val=NONE_VAL):
        """
        str_ before param name means that it is
        string representation and must be parsed
        """
        self._objects = []
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

        # attributes readed from data header
        self._header_attrs = []
        # attributes passed from user (parsed from str_attrs), this list will be iterated in prepare_line()
        self._attributes = []
        # dictionary where keys are keys of attribute (name (if possible read them from file) and index) and values are indexes of values in row data
        self._template_attrs = {}

        if self.str_objects:
            splitted = self.ss_str(self._str_objects, ',')
            self._objects = [Object(name) for name in splitted]

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

    def get_attrs_info(self, fill_header_attrs_func):

        # create header attributes and fill _header_attrs slot
        fill_header_attrs_func()

        # create attributes from argument entered by the user, fill _attributes
        if self.str_attrs:
            parser = ArgsParser()
            parser.parse(self.str_attrs, (len(self._header_attrs)-1))
            self._attributes = parser.attributes

        if not self._attributes:
            self._attributes = self._header_attrs  # reference will be point to the same list, but it should be ok
        else:
            # rename attributes to string names if has index names
            for attr in self._attributes:
                if attr.index is not None and str(attr.index) == attr.name:
                    attr.name = self._header_attrs[attr.index].name

        # fill dictionary which is used for filtering attributes in prepare_line function,
        # keys are indexes and names of all attributes (given from header), values are indexes of attributes in line (object)
        for attr in self._header_attrs:
            self._template_attrs[str(attr.index)] = attr.index
            self._template_attrs[attr.name] = attr.index

    def get_header_info(self):
        """
        Set attributes, objects, relation name and index_data_start.
        """
        pass

    def get_data_info(self, manager=None, read=False):
        """Get much as possible information about data"""

        self._attr_count = len(self._attributes)
        if read:
            for index, line in enumerate(self.source):
                str_values = self.prepare_line(line, scale=False)
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
        else:
            self._index_data_start = 0  # Lines shouldn't be skipped in converter

    def get_data_info_for_browse(self, manager=None):
        pass

    def prepare_line(self, values, scale=True):
        """If return empty list -> line is comment"""
        if not isinstance(values, list):
            values = self.ss_str(values, self.separator)
        if not values:
            return values
        result = []
        for attr in self._attributes:
            index = self._template_attrs[attr.key]
            new_value = attr.process(values[index], scale)
            result.append(new_value)
        return result

    def write_line_to_file(self, line):
        """
        Aux function for write_line, only add \n to line and
        write complitely prepared line to file"""
        line = self.separator.join(line)
        line += '\n'
        self._source.write(line)

    def write_line(self, prepered_line):
        """
        Will write data to output in new format
        based on old_values - list of string values
        """
        self.write_line_to_file(prepered_line)

    def write_header(self, old_data):
        """This method should be rewritten in child class"""
        pass

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

    @staticmethod
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

    def write_header(self, old_data):
        if not self.relation_name:
            self._relation_name = old_data.relation_name

        # write relation name
        self._source.write(self.RELATION + ' ' + self.relation_name + '\n\n')

        for attr in old_data.attributes:
            line = (self.ATTRIBUTE + ' ' + str(attr.name) + ' '
                    + attr.arff_repr(self.separator) + '\n')
            self._source.write(line)

        # write data symbol
        self._source.write('\n' + self.DATA + '\n')

    def get_header_info(self):
        header = self._get_header_str()
        self._parser.parse(header)
        self._relation_name = self._parser.relation_name
        self._index_data_start = self._parser.data_start
        self._header_attrs = self._parser.attributes

    def prepare_line(self, line, scale=True):
        return super().prepare_line(self._parser.parse_line(line), scale)

    def _get_header_str(self):
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

    def write_header(self, old_data):
        attrs_name = []
        for attr in old_data.attributes:
            attrs_name.append(attr.name)
        self.write_line_to_file(attrs_name)

    def get_header_info(self):
        if not self._no_attrs_first_line:  # attributes are specified on first line
            self._index_data_start = 1
            line = self._get_first_line()
            str_values = self.ss_str(line, self.separator)
            self._header_attrs = [AttrScale(i, name) for i, name in enumerate(str_values)]
        else:  # attributes aren't specified on first line
            line = self._get_first_line(False)
            str_values = self.ss_str(line, self.separator)
            self._attr_count = len(str_values)
            self._header_attrs = [AttrScale(i, str(i)) for i in range(self._attr_count)]

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

    def write_line(self, prepared_line):
        if self._classes:
            prepared_line.append(self._classes.pop())
        super().write_line(prepared_line)

    def write_header(self, old_data):
        names_file = self._get_name_file(self._source.name)

        with open(names_file, 'w') as f:
            f.write(self._get_class_occur() + ".\n")
            for attr in old_data.attributes:
                line = (str(attr.name) + ': '
                        + attr.data_repr(self.separator) + '.\n')
                f.write(line)

    def get_header_info(self):
        parser = DataParser()
        parser.parse(self._get_name_file(self._source.name))
        self._header_attrs = parser.attributes

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


class DataCxt(DataBivalent):
    """Burmeister data format"""

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator='', relation_name='', none_val=Data.NONE_VAL):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val)

    sym_vals = {'X': 1, '.': 0}
    vals_sym = {1: 'X', 0: '.'}

    def get_header_info(self):
        self.get_not_empty_line(self.source)  # skip B
        self._relation_name = next(self.source)

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
            self._header_attrs.append(new)

        self._attr_count = columns
        self._obj_count = rows
        # no lines shoud be skipped, because skip was done by next() above!

    def get_data_info(self, manager=None, read=False):
        pass

    def prepare_line(self, line, scale=True):
        splitted = list(line.strip())
        result = []
        for val in splitted:
            result.append(str(DataCxt.sym_vals[val]))
        return super().prepare_line(result, scale)

    def write_header(self, old_data):
        target = self._source
        attrs_to_write = old_data.attributes
        if not self._objects:
            self._objects = [Object(str(i)) for i in range(old_data.obj_count)]

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

    def write_line(self, prepared_line):
        result = []
        for val in prepared_line:
            result.append(DataCxt.vals_sym[int(val)])
        self.write_line_to_file(result)


class DataDat(DataBivalent):
    """Data format for FCALGS"""
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name=''):
        super().__init__(source, str_attrs, str_objects,
                         ' ', relation_name)

    def get_data_info(self, manager=None, read=False):
        max_val = -1
        line_count = 0
        for i, line in enumerate(self.source):
            line_count += 1
            splitted = super().ss_str(line, self.separator)
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

        def fill_header_attrs():
            self._header_attrs = [(AttrScaleEnum(i, str(i)).update(
                                  self.bi_vals['pos'], self._none_val)).update(
                                      self.bi_vals['neg'], self._none_val)
                                  for i in range(self._attr_count)]

        self.get_attrs_info(fill_header_attrs)

    def get_data_info_for_browse(self, manager=None):
        self.get_data_info(manager)

    def prepare_line(self, line, scale=True):
        splitted = super().ss_str(line, self.separator)
        result = ['0'] * (self._attr_count)
        for val in splitted:
            if val:
                result[int(val)] = str(1)
        return super().prepare_line(result, scale)

    def write_line(self, line):
        result = []
        for i, val in enumerate(line):
            if bool(int(val)):
                result.append(str(i))
        self.write_line_to_file(result)
