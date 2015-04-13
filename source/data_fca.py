import re

from source.attributes_fca import (Attribute, AttrScale, AttrScaleNumeric,
                                   AttrScaleEnum, AttrScaleString)
from source.object_fca import Object


class Data:
    """Base class of all data"""

    """Class data"""
    attr_classes = {'n': AttrScaleNumeric,
                    'e': AttrScaleEnum,
                    's': AttrScaleString}
    LEFT_BRACKET = '['
    RIGHT_BRACKET = ']'

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
            for i, str_attr in enumerate(splitted):
                attr_class = Attribute
                attr_name = str_attr
                if str_attr[-1] == Data.RIGHT_BRACKET:
                    attr_class = Data.attr_classes[str_attr[-2]]
                    attr_name = str_attr[:-3]
                self._attributes.append(attr_class(i, attr_name))

        if self.str_objects:
            splitted = self.ss_str(self._str_objects, self.separator)
            self._objects = [Object(name) for name in splitted]

    def get_header_info(self):
        """
        Set attributes, objects and index_data_start.
        """
        pass

    def get_data_info(self):
        """Get much as possible information about data"""
        self._attr_count = len(self._attributes)
        with open(self.source, 'r') as f:
            Data.skip_lines(self.index_data_start, f)
            for line in f:
                self._obj_count += 1
                str_values = self.ss_str(line, self.separator)
                for i, attr in enumerate(self._attributes):
                    attr.update(str_values[i])

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

    def write_header(self, target, old_data=None):
        pass

    def ss_str(self, string, separator):
        """
        Strip and split string by separator.
        Return list of values.
        """
        return list(map(lambda s: s.strip(), string.split(separator)))

    def get_not_empty_line(self, f, i_ref):
        while True:
            line = next(f)
            i_ref[0] = i_ref[0] + 1
            if line.strip():
                return line

    def print_info(self):
        print("Relation name: {}".format(self.relation_name))
        print("Objects count: {}".format(self.obj_count))
        print("Attributes count: {}".format(self.attr_count))
        print("="*20)
        for attr in self._attributes:
            attr.print_self()

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

    def write_header(self, target, old_data=None):
        if not self.relation_name and old_data:
            self._relation_name = old_data.relation_name

        # write relation name
        target.write(self.RELATION + ' ' + self.relation_name + '\n\n')

        # write attributes
        if self._attributes:  # attributes are passed as parameter
            attrs_to_write = self._attributes
        else:
            attrs_to_write = old_data.attributes  # attributes are readed from source(old) file

        for attr in attrs_to_write:
            line = (self.ATTRIBUTE + ' ' + str(attr.name) + ' '
                    + attr.arff_repr(self.separator) + '\n')
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
                    identifier = values[self.IDENTIFIER]

                    # @relation
                    if identifier == self.RELATION:
                        self._relation_name = values[self.NAME]

                    # @attribute
                    elif identifier == self.ATTRIBUTE:
                        attr_type = values[self.VALUE]
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
                else:
                    continue
            self._str_attrs = self.separator.join(attrs_names)


class DataCsv(Data):
    """Column seperated value format"""
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=',', relation_name='', attrs_first_line=False):
        self._attrs_first_line = attrs_first_line
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name)

    def write_header(self, target, old_data=None):
        attrs_to_write = []
        if self._attributes:
            attrs_to_write = self._attributes
        elif old_data and old_data.attributes:
            attrs_to_write = old_data.attributes

        attrs_name = []
        for attr in attrs_to_write:
            attrs_name.append(attr.name)
        self.write_line_to_file(attrs_name, target, self._separator)

    def get_header_info(self):
        if self._attrs_first_line:
            self._index_data_start = 1
            if not self._str_attrs:
                self._str_attrs = self.get_first_line(self.source)
                self.prepare()

    def get_first_line(self, source):
        """Set str_attrs to first line from data file"""
        with open(source, 'r') as f:
            return next(f)


class DataBivalent(Data):
    """Data represented only by bivalnet values e.g 1/0"""

    bi_vals = {'pos': '1', 'neg': '0'}

    def parse_old_attrs_for_scale(self, old_str_attrs, separator):
        """
        Take into _attributes dictionary,
        where key are strings and values are indexes
        of attributes (this slot is rwritten).
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
                attr_class = Data.attr_classes[formula[-1]]
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

            self._index_data_start = index[0]

    def get_data_info(self):
        with open(self.source) as f:
            Data.skip_lines(self.index_data_start, f)
            self._attr_count = len(self._attributes)
            for line in f:
                self._obj_count += 1

    def prepare_line(self, line):
        splitted = list(line.strip())
        result = []
        for val in splitted:
            result.append(str(DataCxt.sym_vals[val]))
        return result

    def write_header(self, target, old_data=None):
        if not self._attributes:
            self._attributes = old_data.attributes

        target.write('B\n')
        if not self.relation_name and old_data:
            self._relation_name = old_data.relation_name
        target.write(self.relation_name + '\n')
        target.write(str(len(self._objects))+'\n')
        target.write(str(len(self._attributes))+'\n')
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
    """Data format for FCALGS"""
    def __init__(self, source,
                 str_attrs=None, str_objects=None,
                 separator=' ', relation_name=''):
        super().__init__(source, str_attrs, str_objects,
                         separator, relation_name)

    def get_data_info(self):
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
        self._attr_count = max_val
        self._obj_count = line_count
        # TODO add support if attributes are passed as parameter
        self._attributes = [(AttrScaleEnum(i, str(i)).update(
                            self.bi_vals['pos'])).update(self.bi_vals['neg'])
                            for i in range(self._attr_count)]

    def prepare_line(self, line):
        splitted = super().prepare_line(line)
        result = ['0'] * (self._attr_count + 1)
        for val in splitted:
            result[int(val)] = str(1)
        return result

    def write_data_scale(self, values, target_file):
        result = []
        for i, attr in enumerate(self._attributes):
            scaled = attr.scale(self._attributes_temp, values)
            if bool(int(scaled)):  # scaled value can be '0'/'1' or True/False
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
