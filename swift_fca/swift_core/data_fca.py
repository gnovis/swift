from __future__ import print_function
import re
import os
import sys
import tempfile
import copy
from collections import OrderedDict

from .attributes_fca import (Attribute, AttrEnum)
from .object_fca import Object
from .parser_fca import FormulaParser, ArffParser, DataParser, parse_sequence
from .constants_fca import Bival, FileType
from .errors_fca import HeaderError, LineError, AttrError, InvalidValueError, FormulaKeyError, BivalError, NamesFileError, NotEnoughLinesError, ClassKeyError


class Class:
    def __init__(self, key):
        self._key = key
        self._values = []

    @property
    def key(self):
        return self._key

    @property
    def values(self):
        return self._values.copy()

    def update_values(self, val):
        val = str(val)
        if val not in self._values:
            self._values.append(val)


class Data:
    """Base class of all data"""

    """Class data"""

    NONE_VAL = "?"
    # bool_true, bool_false and prepared_val are indexes of
    # proccesed value and specific bool value owned by attribute

    PREPARED_VAL = 0
    BOOL_TRUE = 1
    BOOL_FALSE = 2

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', none_val=NONE_VAL, classes=""):
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
        self._attr_count_no_classes = 0
        self._temp_source = None
        if not self.source.seekable():
            self._temp_source = tempfile.TemporaryFile(mode='w+t', dir='./')

        # attributes readed from data header
        self._header_attrs = []
        # attributes passed from user (parsed from str_attrs), this list will be iterated in prepare_line()
        self._attributes = []
        # dictionary where keys are keys of attribute (name (if possible read them from file) and index) and values are indexes of values in row data
        self._template_attrs = {}
        # list of attributes, which are marked as classes
        self._classes = []
        # list if identifiers of attributes which are classes, sequence is parsed in get_attrs_info e.g "2-5, foo" -> [2, 3, 4, 5, foo]
        self._classes_keys_sequence = classes

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
        return self._obj_count

    @property
    def attr_count(self):
        """is counted in method: get_header_info or get_attrs_info"""
        return self._attr_count

    @property
    def attr_count_no_classes(self):
        """is counted in method: get_header_info or get_attrs_info"""
        return self._attr_count_no_classes

    @property
    def classes(self):
        return self._classes.copy()

    def update_classes_by_values_from_attrs(self):
        """
        This method is defined only in DataDtl class for updating classes values.
        """
        pass

    def get_attrs_info(self, manager):

        # create header attributes and fill _header_attrs slot
        self.get_header_info(manager)
        self._classes_keys_sequence = parse_sequence(self._classes_keys_sequence, len(self._header_attrs)-1)
        for key in self._classes_keys_sequence:
            self._classes.append(Class(key))

        # Just for Dtl classes update
        self.update_classes_by_values_from_attrs()

        # fill dictionary which is used for filtering attributes in prepare_line function,
        # keys are indexes and names of all attributes (given from header), values are indexes of attributes in line (object)
        for attr in self._header_attrs:
            str_index = str(attr.index)
            self._template_attrs[attr.name] = attr.index
            if str_index not in self._template_attrs:
                self._template_attrs[str_index] = attr.index

        # create attributes from argument entered by the user, fill _attributes
        if self.str_attrs:
            parser = FormulaParser()
            parser.parse(self.str_attrs, (len(self._header_attrs)-1))
            self._attributes = parser.attributes

        must_read_data = False
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

                attr.is_class = header_attr.is_class

                if (type(header_attr) is AttrEnum) and (type(attr) is AttrEnum):
                    attr_header_values = header_attr.values
                    if attr_header_values and not attr.values:
                        for val in attr_header_values:
                            attr.update(val, self._none_val)

                merged.append(attr)
                if attr.unpack:
                    attr.clear_values()
                    must_read_data = True
            self._attributes = merged

        self._attr_count = len(self._attributes)
        for ha in self._header_attrs:
            if not ha._is_class:
                self._attr_count_no_classes += 1

        return must_read_data

    def get_header_info(self, manager=None):
        """
        Set attributes, objects, relation name and index_data_start.
        """
        pass

    def get_data_info(self, manager, read=False):
        """Get much as possible information about data"""

        if read:
            for index, line in enumerate(self.source):
                if manager.stop or manager.skip_rest_lines(index):
                    break
                if manager.skip_line(index):
                    continue
                try:
                    str_values = self.prepare_line(line, index, scale=False, update=True)
                except (LineError, AttrError) as e:
                    if manager.skip_errors:
                        manager.add_error(e)
                        continue
                    raise e
                if not str_values[0]:  # current line is comment
                    continue
                self._obj_count += 1

                if self._temp_source:
                    self._temp_source.write(line)
                if manager.gui:
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
            return values, None
        result = []
        for attr in self._attributes:
            index = self._template_attrs[attr.key]
            try:
                new_value = attr.process(values[index], self._none_val, scale, update)
            except IndexError:
                raise LineError(self.FORMAT, line_i+1, index+1, ",".join(values), "Some of the attribute is missing.")
            except InvalidValueError as e:
                raise AttrError(line_i+1, ",".join(values), index+1, values[index], e)

            result.append([new_value, attr.true, attr.false])

        classes_values = []
        for cls in self._classes:
            try:
                index = self._template_attrs[cls.key]
            except KeyError:
                raise ClassKeyError(cls.key)
            val = values[index]
            cls.update_values(val)
            classes_values.append(val)
        return result, classes_values

    def unpack_attrs(self):
        unpacked = []
        for attr in self._attributes:
            if attr.unpack:
                i = 0
                for v in attr.values:
                    new = AttrEnum(attr.index, '{}_{}_{}'.format(attr.name, i, v),
                                   attr_pattern=attr.attr_pattern,
                                   expr_pattern=v)
                    unpacked.append(new)
                    i += 1
            else:
                unpacked.append(attr)
        self._attributes = unpacked
        self._attr_count = len(self._attributes)

    def write_line_to_file(self, line):
        """
        Aux function for write_line, only add \n to line and
        write complitely prepared line to file"""
        line = self.separator.join(line)
        line += '\n'
        self._source.write(line)

    def write_line(self, prepered_line, classes=None):
        """
        Will write data to output in new format
        based on old_values - list of string values
        """
        vals = list(map(lambda l: l[self.PREPARED_VAL], prepered_line))
        self.write_line_to_file(vals)

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

    def check_value_bival(self, values):
        prepared_val = values[self.PREPARED_VAL]
        true_val = values[self.BOOL_TRUE]
        false_val = values[self.BOOL_FALSE]
        if not ((prepared_val == true_val) or
                (prepared_val == false_val)):
            raise BivalError(prepared_val, true_val, false_val)


class DataArff(Data):
    """ Attribute-Relation File Format """

    FORMAT = FileType.ARFF

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='',
                 none_val=Data.NONE_VAL, classes="", **kwargs):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val, classes)
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
        return super().prepare_line(self._parser.parse_line(line, index), index, scale, update)

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
                 separator=',', relation_name='', attrs_first_line=True,
                 none_val=None, classes="", **kwargs):
        self._attrs_first_line = attrs_first_line
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val, classes)

    def write_header(self, old_data):
        if self._attrs_first_line:
            attrs_name = []
            for attr in old_data.attributes:
                attrs_name.append(attr.name)
            self.write_line_to_file(attrs_name)

    def get_header_info(self, manager=None):
        if self._attrs_first_line:  # attributes are specified on first line
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
        try:
            line = next(self._source)
        except StopIteration:
            raise NotEnoughLinesError(self.source.name)
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
                 separator=',', relation_name='', none_val=Data.NONE_VAL, classes="", **kwargs):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, none_val, classes)
        self._class = None

    def write_header(self, old_data):
        if old_data.classes:
            self._class = old_data.classes[0]  # only first class is excepted by c4.5 format

        names_file = self._get_name_file(self._source.name)
        with open(names_file, 'w') as f:
            cls_to_write = []
            if self._class:
                cls_to_write = self._class.values
            f.write(self.separator.join(cls_to_write) + ".\n")
            for attr in old_data.attributes:
                attr_name = str(attr.name)
                if attr_name == "class":
                    attr_name += "_prev"
                line = (attr_name + ': '
                        + attr.data_repr(self.separator) + '.\n')
                f.write(line)

    def get_header_info(self, manager=None):
        parser = DataParser()
        names_file = self._get_name_file(self._source.name)
        if not os.path.isfile(names_file):
            raise NamesFileError(names_file)
        parser.parse(names_file)
        self._header_attrs = parser.attributes

    def write_line(self, prepered_line, classes=None):
        vals = list(map(lambda l: l[self.PREPARED_VAL], prepered_line))
        if classes:
            vals.extend(classes)
        self.write_line_to_file(vals)

    """return file name with suffix .names"""
    def _get_name_file(self, source):
        return ".".join([os.path.splitext(source)[0], "names"])


class DataCxt(Data):
    """Burmeister data format"""

    IDENT = 'B'
    FORMAT = FileType.CXT
    DOT = '.'
    CROSS = 'X'

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator='', relation_name='', classes="", **kwargs):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, None, classes)

    sym_vals = {CROSS: Bival.true(), DOT: Bival.false()}
    vals_sym = {Bival.true(): CROSS, Bival.false(): DOT}

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
            self._header_attrs.append(new)

        self._attr_count = columns
        self._index_data_start = self.current_line

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

    def write_line(self, prepared_line, classes=None):
        result = []
        for vals in prepared_line:
            self.check_value_bival(vals)
            if vals[self.PREPARED_VAL] == vals[self.BOOL_TRUE]:
                result.append(self.CROSS)
            else:
                result.append(self.DOT)
        self.write_line_to_file(result)

    def get_not_empty_line(self):
        file_iter = iter(self.source)
        while True:
            try:
                line = next(file_iter).strip()
            except StopIteration:
                raise NotEnoughLinesError(self.source.name)
            self.current_line += 1
            if line:
                return line


class DataDatBase(Data):
    """Data format for FCALGS"""

    FORMAT = FileType.DAT
    ERROR_DESCRIPTION = "Invalid value: '{}'. Value must be integer."

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=' ', relation_name='', classes="", **kwargs):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name, None, classes)

    def get_data_header_info(self, manager):
        max_val = -1
        line_count = 0
        attributes = OrderedDict()
        for i, line in enumerate(self.source):
            if manager.stop or manager.skip_rest_lines(i):
                break
            if manager.skip_line(i):
                continue
            line_count += 1
            splitted = self.parse_line(line)
            updated_attrs = {}
            for col, val in enumerate(splitted):
                try:
                    int_val = int(val)
                except ValueError:
                    e = LineError(self.FORMAT, i+1, col+1, line, self.ERROR_DESCRIPTION.format(val))
                    if manager.skip_errors:
                        manager.add_error(e)
                        continue
                    raise e
                if int_val > max_val:
                    max_val = int_val

                if int_val not in attributes:
                    attributes[int_val] = AttrEnum(int_val, str(int_val)).update(Bival.false(), self._none_val, step=line_count-1)
                attributes[int_val].update(Bival.true(), self._none_val)
                updated_attrs[int_val] = attributes[int_val]

            for i in range(max_val + 1):
                if i not in attributes:
                    attributes[i] = AttrEnum(i, str(i)).update(Bival.false(), self._none_val, step=line_count-1)
                if i not in updated_attrs:
                    attributes[i].update(Bival.false(), self._none_val)

            if self._temp_source:
                self._temp_source.write(line)

            if manager.gui:
                manager.update_counter(line, self.index_data_start)

        if self._temp_source:
            self._source = self._temp_source
        self._source.seek(0)

        self._attr_count = max_val + 1
        self._obj_count = line_count

        sorted_attrs = OrderedDict(sorted(attributes.items(), key=lambda t: t))
        self._header_attrs = list(sorted_attrs.values())

    def get_header_info(self, manager=None):
        self.get_data_header_info(manager)

    def get_data_info(self, manager, read=False):
        for cls in self._classes:
            cls.update_values(Bival.true())
            cls.update_values(Bival.false())

    def get_prepared_indexes(self, str_indexes, index, line):
        splitted = self.split_line(str_indexes)
        result = [Bival.false()] * (self._attr_count_no_classes)
        for col, val in enumerate(splitted):
            try:
                result[int(val)] = Bival.true()
            except ValueError:
                raise LineError(self.FORMAT, index+1, col+1, line, self.ERROR_DESCRIPTION.format(val))
        return result

    def prepare_line(self, values, index, scale=True, update=False):
        return super().prepare_line(values, index, scale, update)

    def write_line(self, line, classes=None):
        result = []
        for i, vals in enumerate(line):
            self.check_value_bival(vals)
            if vals[self.PREPARED_VAL] == vals[self.BOOL_TRUE]:
                result.append(str(i))
        return result

    def split_line(self, line):
        result = []
        splitted = line.split(self.separator)
        for val in splitted:
            val = val.strip()
            if val:
                result.append(val)
        return result


class DataDat(DataDatBase):
    def parse_line(self, line):
        return self.split_line(line)

    def prepare_line(self, line, index, scale=True, update=False):
        result = self.get_prepared_indexes(line, index, line)
        return super().prepare_line(result, index, scale, update)

    def write_line(self, line, classes=None):
        to_write = super().write_line(line, classes)
        self.write_line_to_file(to_write)


class DataDtl(DataDatBase):
    FORMAT = FileType.DTL
    """
    DAT format with classes defined behind the char '|' (default, can be changed)
    example:

    0 1 2 3 4|a bb
    1 2 3 4|b bb
    2 3 4|a aa
    3 4|a bb
    4|b aa

    """
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=' ', relation_name='', classes="", cls_separator='|', **kwargs):
        super().__init__(source, str_attrs, str_objects, separator, relation_name, classes)
        self._classes_from_source_file = OrderedDict()
        self._class_sep = cls_separator

    def parse_line(self, line):
        indexes, classes = self.get_indexes_classes(line)
        for i, cls in enumerate(self.split_line(classes)):
            if i not in self._classes_from_source_file:
                self._classes_from_source_file[i] = AttrEnum(None, "class{}".format(i+1))
                self._classes_from_source_file[i].is_class = True
            # All classes must be on every line, otherwise update won't work correctly
            self._classes_from_source_file[i].update(cls, self._none_val)

        splitted_indexes = self.split_line(indexes)
        return splitted_indexes

    def get_indexes_classes(self, line):
        indexes, sep, classes = line.partition(self._class_sep)
        return indexes, classes.strip()

    def prepare_line(self, line, index, scale=True, update=False):
        str_indexes, classes = self.get_indexes_classes(line)
        result = self.get_prepared_indexes(str_indexes, index, line)
        result.extend(self.split_line(classes))
        return super().prepare_line(result, index, scale, update)

    def write_line(self, line, classes=None):
        indexes = super().write_line(line, classes)
        str_line = self.separator.join(indexes) + self._class_sep
        if classes:
            str_line += self.separator.join(classes)
        str_line += '\n'
        self._source.write(str_line)

    def get_data_info(self, manager, read=False):
        pass

    def update_classes_by_values_from_attrs(self):
        for cls in self._classes:
            for attr in self._header_attrs:
                if cls.key == attr.name or cls.key == str(attr.index):
                    for val in attr.values:
                        cls.update_values(val)

    def get_data_header_info(self, manager):
        super().get_data_header_info(manager)
        next_index = self._attr_count
        for cls in self._classes_from_source_file.values():
            cls.index = next_index
            next_index += 1
            self._header_attrs.append(cls)
