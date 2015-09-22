from __future__ import print_function
import re
import os
import sys
import tempfile
import copy

from .attributes_fca import (Attribute, AttrEnum)
from .object_fca import Object
from .parser_fca import FormulaParser, ArffParser, DataParser
from .constants_fca import Bival, FileType
from .errors_fca import HeaderError, LineError, AttrError, InvalidValueError, FormulaKeyError


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

    def get_attrs_info(self, manager):

        # create header attributes and fill _header_attrs slot
        self.get_header_info(manager)

        # fill dictionary which is used for filtering attributes in prepare_line function,
        # keys are indexes and names of all attributes (given from header), values are indexes of attributes in line (object)
        for attr in self._header_attrs:
            self._template_attrs[str(attr.index)] = attr.index
            self._template_attrs[attr.name] = attr.index

        # create attributes from argument entered by the user, fill _attributes
        if self.str_attrs:
            parser = FormulaParser()
            parser.parse(self.str_attrs, (len(self._header_attrs)-1))
            self._attributes = parser.attributes

        # attributes argument is not set -> only infomations from header will be used
        if not self._attributes:
            self._attributes = self._header_attrs
        # merge header attributes with attributes from user
        else:
            merged = []
            for attr in self._attributes:

                try:
                    header_attr_index = self._template_attrs[attr.key]
                except KeyError:
                    raise FormulaKeyError(attr.key)
                header_attr = copy.copy(self._header_attrs[header_attr_index])

                # rename attributes to string names if has index names
                if attr.index is not None and str(attr.index) == attr.name:
                    attr.name = header_attr.name

                if type(attr) is Attribute:
                    header_attr.name = attr.name
                    merged.append(header_attr)
                else:
                    merged.append(attr)
            self._attributes = merged

    def get_header_info(self, manager=None):
        """
        Set attributes, objects, relation name and index_data_start.
        """
        pass

    def get_data_info(self, manager, read=False):
        """Get much as possible information about data"""

        self._attr_count = len(self._attributes)
        if read:
            for index, line in enumerate(self.source):
                if manager.stop or manager.skip_rest_lines(index):
                    break
                if manager.skip_line(index):
                    continue
                str_values = self.prepare_line(line, index, scale=False, update=True)
                if not str_values:  # current line is comment
                    continue
                self._obj_count += 1

                if self._temp_source:
                    self._temp_source.write(line)
                manager.update_counter(line, self.index_data_start)

            if self._temp_source:
                self._source = self._temp_source
            self._source.seek(0)
        else:
            self._index_data_start = 0  # Lines shouldn't be skipped in converter

    def prepare_line(self, values, line_i, scale=True, update=False):
        """If return empty list -> line is comment"""
        if not isinstance(values, list):
            values = self.ss_str(values, self.separator)
        if not values:
            return values
        result = []
        for attr in self._attributes:
            index = self._template_attrs[attr.key]

            try:
                new_value = attr.process(values[index], self._none_val, scale, update)
            except IndexError:
                raise LineError(self.FORMAT, line_i+1, index+1, ",".join(values), "Some of the attribute is missing.")
            except InvalidValueError as e:
                raise AttrError(line_i+1, ",".join(values), index+1, values[index], e)

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
        result = list(map(lambda x: x.strip(),
                          re.split(r'(?<!\\)' + separator, string, max_split)))
        if len(result) == 1 and not result[0]:
            return []
        return result

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

    FORMAT = FileType.ARFF

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='',
                 none_val=Data.NONE_VAL, **kwargs):
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

    def get_header_info(self, manager=None):
        header = self._get_header_str()
        self._parser.parse(header)
        self._relation_name = self._parser.relation_name
        self._index_data_start = self._parser.data_start
        self._header_attrs = self._parser.attributes

    def prepare_line(self, line, index, scale=True, update=False):
        return super().prepare_line(self._parser.parse_line(line), index,  scale, update)

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

    FORMAT = FileType.CSV

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', no_attrs_first_line=False,
                 none_val=Data.NONE_VAL, **kwargs):
        self._no_attrs_first_line = no_attrs_first_line
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val)

    def write_header(self, old_data):
        attrs_name = []
        for attr in old_data.attributes:
            attrs_name.append(attr.name)
        self.write_line_to_file(attrs_name)

    def get_header_info(self, manager=None):
        if not self._no_attrs_first_line:  # attributes are specified on first line
            self._index_data_start = 1
            line = self._get_first_line()
            str_values = self.ss_str(line, self.separator)
            self._header_attrs = [Attribute(i, name) for i, name in enumerate(str_values)]
        else:  # attributes aren't specified on first line
            line = self._get_first_line(False)
            str_values = self.ss_str(line, self.separator)
            self._attr_count = len(str_values)
            self._header_attrs = [Attribute(i, str(i)) for i in range(self._attr_count)]

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

    FORMAT = FileType.DATA

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', classes="", none_val=Data.NONE_VAL, **kwargs):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val)
        self._classes = list(reversed(self.ss_str(classes, self._separator)))

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

    def get_header_info(self, manager=None):
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


class DataCxt(Data):
    """Burmeister data format"""

    IDENT = 'B'
    FORMAT = FileType.CXT

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator='', relation_name='', none_val=Data.NONE_VAL, **kwargs):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val)

    sym_vals = {'X': Bival.true(), '.': Bival.false()}
    vals_sym = {Bival.true(): 'X', Bival.false(): '.'}

    def get_header_info(self, manager=None):
        self.current_line = 0  # it is needed for Error message, is incremented in get_not_empty_line()

        b = self.get_not_empty_line()  # skip B
        if b != self.IDENT:
            raise HeaderError(FileType.CXT, self.current_line, 1, b, "First non empty line must contain 'B'.")

        value = self.get_not_empty_line()
        try:
            rows = int(value)
        except ValueError:
            self._relation_name = value
            try:
                str_rows = self.get_not_empty_line()
                rows = int(str_rows)
            except ValueError:
                raise HeaderError(FileType.CXT, self.current_line, 1, str_rows, "After realation name must be specified count of objects.")

        try:
            str_columns = self.get_not_empty_line()
            columns = int(str_columns)
        except ValueError:
            raise HeaderError(FileType.CXT, self.current_line, 1, str_columns, "After objects count must be specified count of attributes.")

        for i in range(rows):
            obj_name = self.get_not_empty_line()
            self._objects.append(Object(obj_name))

        for k in range(columns):
            attr_name = self.get_not_empty_line()
            new = AttrEnum(k, attr_name)
            new.update(Bival.true(), self._none_val)
            new.update(Bival.false(), self._none_val)
            self._header_attrs.append(new)

        self._attr_count = columns
        self._obj_count = rows
        # no lines shoud be skipped, because skip was done by next() above!

    def get_data_info(self, manager, read=False):
        pass

    def prepare_line(self, line, index, scale=True, update=False):
        splitted = list(line.strip())
        result = []
        for val_i, val in enumerate(splitted):
            try:
                result.append(DataCxt.sym_vals[val])
            except KeyError:
                raise LineError(self.FORMAT, index+1, val_i+1, line, "Invalid value: '{}'. Value must be X (True) or . (False)".format(val))
        return super().prepare_line(result, index, scale, update)

    def write_header(self, old_data):
        target = self._source
        attrs_to_write = old_data.attributes
        if not self._objects:
            self._objects = [Object(str(i)) for i in range(old_data.obj_count)]

        target.write('{}\n'.format(self.IDENT))
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
            result.append(DataCxt.vals_sym[val])
        self.write_line_to_file(result)

    def get_not_empty_line(self):
        file_iter = iter(self.source)
        while True:
            line = next(file_iter).strip()
            self.current_line += 1
            if line:
                return line


class DataDat(Data):
    """Data format for FCALGS"""

    FORMAT = FileType.DAT
    ERROR_DESCRIPTION = "Invalid value: '{}'. Value must be integer."

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', **kwargs):
        super().__init__(source, str_attrs, str_objects,
                         ' ', relation_name)

    def get_data_header_info(self, manager):
        max_val = -1
        line_count = 0
        for i, line in enumerate(self.source):
            if manager.stop or manager.skip_rest_lines(i):
                break
            if manager.skip_line(i):
                continue
            line_count += 1
            splitted = super().ss_str(line, self.separator)
            for col, val in enumerate(splitted):
                try:
                    int_val = int(val)
                except ValueError:
                    raise LineError(self.FORMAT, i+1, col+1, line, self.ERROR_DESCRIPTION.format(val))
                if int_val > max_val:
                    max_val = int_val

            if self._temp_source:
                self._temp_source.write(line)
            manager.update_counter(line, self.index_data_start)

        if self._temp_source:
            self._source = self._temp_source
        self._source.seek(0)

        self._attr_count = max_val + 1
        self._obj_count = line_count

        self._header_attrs = [(AttrEnum(i, str(i)).update(
                              Bival.true(), self._none_val)).update(
                                  Bival.false(), self._none_val)
                              for i in range(self._attr_count)]

    def get_header_info(self, manager=None):
        self.get_data_header_info(manager)

    def get_data_info(self, manager, read=False):
        pass

    def prepare_line(self, line, index, scale=True, update=False):
        splitted = super().ss_str(line, self.separator)
        result = [Bival.false()] * (self._attr_count)
        for col, val in enumerate(splitted):
            try:
                result[int(val)] = Bival.true()
            except ValueError:
                raise LineError(self.FORMAT, index+1, col+1, line, self.ERROR_DESCRIPTION.format(val))
        return super().prepare_line(result, index, scale, update)

    def write_line(self, line):
        result = []
        for i, val in enumerate(line):
            if val == Bival.true():
                result.append(str(i))
        self.write_line_to_file(result)
