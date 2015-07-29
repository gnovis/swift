from __future__ import print_function
import re
import os
import sys

from source_swift.attributes_fca import (Attribute, AttrScale, AttrScaleNumeric,
                                         AttrScaleEnum, AttrScaleString)
from source_swift.object_fca import Object


class Data:
    """Base class of all data"""

    """Class data"""
    attr_classes = {'n': AttrScaleNumeric,
                    'e': AttrScaleEnum,
                    's': AttrScaleString}
    LEFT_BRACKET = '['
    RIGHT_BRACKET = ']'
    NONE_VALUE = "None"  # TODO pridat jako volitelny parametr
    empty_vals = ["", "?", NONE_VALUE]

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name=''):
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
        self._index_data_start = 0
        self._obj_count = 0
        self._attr_count = 0

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
            splitted = self.ss_str(self._str_attrs, self.separator)
            attrs_names = []
            for i, str_attr in enumerate(splitted):
                attr_class = Attribute
                attr_name = str_attr
                if str_attr[-1] == Data.RIGHT_BRACKET:
                    attr_class = Data.attr_classes[str_attr[-2]]
                    attr_name = str_attr[:-3]
                self._attributes.append(attr_class(i, attr_name))
                attrs_names.append(attr_name)
            self._str_attrs = self.separator.join(attrs_names)

        if self.str_objects:
            splitted = self.ss_str(self._str_objects, self.separator)
            self._objects = [Object(name) for name in splitted]

    def get_header_info(self):
        """
        Set attributes, objects and index_data_start.
        """
        pass

    def get_data_info(self, manager=None):
        """Get much as possible information about data"""
        self._attr_count = len(self._attributes)
        with open(self.source, 'r') as f:
            Data.skip_lines(self.index_data_start, f)
            for i, line in enumerate(f):
                self._obj_count += 1
                str_values = self.ss_str(line, self.separator)
                if i == 0 and self._attr_count == 0:
                    self._attr_count = len(str_values)
                for i, attr in enumerate(self._attributes):
                    attr.update(str_values[i])
                if manager:
                    if manager.stop:
                        break
                    manager.next_line_prepared.emit(line, self.index_data_start)

    def prepare_line(self, line):
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
        return list(map(lambda x: self._prepare_value(x),
                    re.split(r'(?<!\\)' + separator, string, max_split)))

    def _prepare_value(self, val):
        stripped = val.strip()
        if stripped in self.empty_vals:
            return self.NONE_VALUE
        return stripped

    def get_not_empty_line(self, f, i_ref):
        while True:
            line = next(f)
            i_ref[0] = i_ref[0] + 1
            if line.strip():
                return line

    def print_info(self, out_file=sys.stdout):
        print("Relation name: {}".format(self.relation_name), file=out_file)
        print("Objects count: {}".format(self.obj_count), file=out_file)
        print("Attributes count: {}".format(self.attr_count), file=out_file)
        print("="*20, file=out_file)
        for attr in self._attributes:
            attr.print_self(out_file)

    def skip_lines(line_i, f):
        for i in range(line_i):
            next(f)


class DataArff(Data):
    """Attribute-Relation File Format"""

    PART_SYM = '@'
    IDENTIFIER = 0
    NAME = 1
    VALUE = 2

    NUMERIC = "numeric"
    STRING = "string"

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
        with open(self.source) as f:
            attr_index = 0
            attrs_names = []
            for i, line in enumerate(f):
                curr_line = line.strip()
                if curr_line.startswith(self.PART_SYM):
                    values = curr_line.split()
                    identifier = values[self.IDENTIFIER].lower()  # is case insensitive

                    # @relation
                    if identifier == self.RELATION and len(values) > 1:
                        self._relation_name = values[self.NAME]

                    # @attribute
                    elif identifier == self.ATTRIBUTE:
                        attr_type = values[self.VALUE].lower()  # is case insensitive
                        if (attr_type == self.NUMERIC
                                or attr_type == self.STRING):
                            cls = Data.attr_classes[attr_type[0]]
                        else:
                            cls = Data.attr_classes['e']
                        self._attributes.append(
                            cls(attr_index,
                                values[self.NAME]))
                        attr_index += 1
                        attrs_names.append(values[self.NAME])

                    # @data
                    elif identifier == self.DATA:
                        self._index_data_start = i + 1
                        break
            self._str_attrs = self.separator.join(attrs_names)


class DataCsv(Data):
    """Column seperated value format"""
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', no_attrs_first_line=False):
        self._no_attrs_first_line = no_attrs_first_line
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name)

    def write_header(self, target, old_data):
        attrs_to_write = super().write_header(target, old_data)
        attrs_name = []
        for attr in attrs_to_write:
            attrs_name.append(attr.name)
        self.write_line_to_file(attrs_name, target, self._separator)

    def get_header_info(self):
        if not self._no_attrs_first_line:
            self._index_data_start = 1
            if not self._str_attrs:
                self._str_attrs = self._get_first_line(self.source)
                self.prepare()

    def get_data_info(self, manager=None):
        super().get_data_info(manager)
        if not self._str_attrs:
            self._str_attrs = self._separator.join([str(x) for x in range(self._attr_count)])
            self.prepare()

    def _get_first_line(self, source):
        """Return first line from data file"""
        with open(source, 'r') as f:
            return next(f)


class DataData(Data):
    """C4.5 data file format"""

    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', classes=""):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name)
        self._classes = list(reversed(self.ss_str(classes, self._separator)))
        if self.NONE_VALUE in self._classes:
            self._classes.remove(self.NONE_VALUE)

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
        """
        This method must set _attributes(obejcts) and
        _str_attrs(coma seperated) names of attributes (this is used for scaling)
        """
        with open(self._get_name_file(self._source), 'r') as names:
            i = 0
            attr_names = []
            for j, line in enumerate(names):
                # ignore comments
                l = self._devide_two_part(line, self.COMMENT_SYM)[0]
                # on one line can be more entries seperated by "."
                entries = self.ss_str(l, self.LINE_SEP)
                for k, entry in enumerate(entries):
                    # on a first line are names of classes, seperated by commas
                    # others formats doesn't have classes => class is enum attribute!
                    if (j == 0 and k == 0) or entry is self.NONE_VALUE:
                        continue
                    else:
                        devided = self._devide_two_part(entry, self.ATTR_SEP)
                        attr_name = devided[0]
                        attr_type = devided[1]
                        if attr_type != self.IGNORE:
                            attr_names.append(attr_name)
                            if attr_type == self.CONTINUOUS:
                                self._attributes.append(AttrScaleNumeric(i, attr_name))
                            else:
                                self._attributes.append(AttrScaleEnum(i, attr_name))
                            i += 1

            # append class as last attribute
            attr_names.append(self.CLASS)
            self._attributes.append(AttrScaleEnum(i, self.CLASS))
            # set str_attrs slot
            self._str_attrs = self.separator.join(attr_names)

    def _get_class_occur(self):
        occur = []
        for c in self._classes:
            if c not in occur:
                occur.append(c)
        return self.separator.join(occur)

    def _devide_two_part(self, line, separator):
        return self.ss_str(line, separator, 1)

    """return file name with suffix .names"""
    def _get_name_file(self, source):
        return ".".join([os.path.splitext(source)[0], "names"])


class DataBivalent(Data):
    """Data represented only by bivalnet values e.g 1/0"""

    bi_vals = {'pos': '1', 'neg': '0'}

    def parse_old_attrs_for_scale(self, old_str_attrs, separator):
        """
        Take dictionary into _attributes_temp,
        where key are strings and values are indexes
        of attributes.
        Call this method to use data object as pattern in scaling.
        """
        values = self.ss_str(old_str_attrs, separator)
        self._attributes_temp = {val: i for i, val in enumerate(values)}

    def parse_new_attrs_for_scale(self):
        """
        Parse and create list of scale attributes,
        take it into _attributes (this slot is rewritten).
        Call this method to use data as target in scaling.
        """

        values = self.ss_str(self.str_attrs, ",")
        self._attributes = []
        for i, attr in enumerate(values):
            devided = self.ss_str(attr, "=", 1)
            new_name = devided[0]
            rest = devided[1]

            bracket_i = rest.find(self.LEFT_BRACKET)
            if bracket_i == -1:
                attr_class = AttrScale
                expr_pattern = ''
                attr_pattern = rest
            else:
                attr_class = Data.attr_classes[rest[-1]]
                expr_pattern = rest[bracket_i+1:-2]
                attr_pattern = rest[:bracket_i]

            new_attr = attr_class(i, new_name,
                                  attr_pattern=attr_pattern,
                                  expr_pattern=expr_pattern)
            self._attributes.append(new_attr)

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
        with open(self.source) as f:
            next(f)  # skip B
            self._relation_name = next(f).strip()
            index = [2]

            rows = int(self.get_not_empty_line(f, index).strip())
            columns = int(self.get_not_empty_line(f, index).strip())

            for i in range(rows):
                obj_name = self.get_not_empty_line(f, index).strip()
                self._objects.append(Object(obj_name))

            for k in range(columns):
                attr_name = self.get_not_empty_line(f, index).strip()
                new = AttrScaleEnum(k, attr_name)
                new.update(DataBivalent.bi_vals['pos'])
                new.update(DataBivalent.bi_vals['neg'])
                self._attributes.append(new)

            self._attr_count = columns
            self._obj_count = rows
            self._index_data_start = index[0]

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
        if not self.relation_name and old_data:
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
        with open(self._source, 'r') as f:
            for i, line in enumerate(f):
                line_count += 1
                splitted = super().prepare_line(line)
                for val in splitted:
                    int_val = int(val)
                    if int_val > max_val:
                        max_val = int_val
                if manager:
                    if manager.stop:
                        break
                    manager.next_line_prepared.emit(line, self.index_data_start)
        self._attr_count = max_val + 1
        self._obj_count = line_count
        # These attributes are used only if attrs for new file
        # are not specified
        self._attributes = [(AttrScaleEnum(i, str(i)).update(
                            self.bi_vals['pos'])).update(self.bi_vals['neg'])
                            for i in range(self._attr_count)]

    def prepare_line(self, line):
        splitted = super().prepare_line(line)
        result = ['0'] * (self._attr_count)
        for val in splitted:
            result[int(val)] = str(1)
        return result

    def write_data_scale(self, values, target_file):
        result = []
        for i, attr in enumerate(self._attributes):
            scaled = attr.scale(self._attributes_temp, values)
            if bool(int(scaled)):  # scaled value can be from Reals or True/False
                result.append(str(i))
        if result:
            self.write_line_to_file(result, target_file, self._separator)

    def write_line(self, line, target_file):
        result = []
        for i, val in enumerate(line):
            if bool(int(val)):
                result.append(str(i))
        if result:
            self.write_line_to_file(result, target_file, self._separator)
