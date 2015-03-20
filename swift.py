#!/bin/python3
"""Main file of swift - FCA data converter"""

import re
import os


class AttrType:
    NUMERIC = 0
    NOMINAL = 1
    STRING = 2
    NOT_SPECIFIED = 3


class Attribute:
    def __init__(self, index, name, attr_type):
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
        self._source = source
        self._str_attrs = str_attrs
        self._str_objects = str_objects
        self._separator = separator
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
            self._attributes = []
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

    def write(self, prepered_line, target):
        """
        Will write data to output in new format
        based on old_values - list of string values
        """
        line = self._separator.join(prepered_line)
        line += '\n'
        target.write(line)

    def write_header(self, relation_name=''):
        pass


class DataArff(Data):
    pass


class DataCsv(Data):
    def write_header(self, target, relation_name=''):
        attrs_name = []
        for attr in self._attributes:
            attrs_name.append(attr.name)
        line = self._separator.join(attrs_name)
        line += '\n'
        target.write(line)


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
            if scaled:
                result.append('X')
            else:
                result.append('.')
        str_result = ''.join(result)
        str_result += "\n"
        target_file.write(str_result)


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
        str_result = self._separator.join(result)
        str_result += "\n"
        target_file.write(str_result)


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
            for i, line in enumerate(f):
                prepared_line = self._old_data.prepare_line(line)
                if self._scaling:
                    self._new_data.write_data_scale(prepared_line,
                                                    target_file)
                else:
                    self._new_data.write(prepared_line,
                                         target_file)
        target_file.close()


# Notes
#
# Třída Convertor bude obsahovat sloty: in_data, out_data a metodu convert,
# ta bude procházet data v in_data a na každý řádek zavolá metodu write
# objektu out_data, tato metoda podle své instance zapíše
# přeformátované/škálované hodnoty do výstupního souboru


# Tests

old_attrs = "a,b,c,d,e"
new_attrs = "A=a[x<=1]n, B=b[x>=2]n, C=c[1<=x<=3]n, D=d[x>2]n, E=e[x>1]n"
convertor = Convertor("test.csv", "new.dat",
                      old_str_attrs=old_attrs,
                      new_str_attrs=new_attrs,
                      new_str_objects='Jan,Petr,Lucie,Jana,Aneta',
                      old_data_sep=';')
convertor.convert()

"""
old_attrs = "age,note,sex"
new_attrs = "AGE=age[x<50]n, NOTE=note[aaa]s, MAN=sex[man]e, WOMAN=sex[woman]e"
convertor = Convertor("old.csv", "new.dat",
                      old_str_attrs=old_attrs,
                      new_str_attrs=new_attrs,
                      new_str_objects='Jan,Petr,Lucie,Jana,Aneta',
                      old_data_sep=';')
convertor.convert()
# c2 = Convertor("new.dat", "new.csv", new_str_attrs="AGE,NOTE,MAN,WOMAN")
# c2.convert()


with open('test.csv') as f:
    for i, line in enumerate(f):
        print(i, ": ", list(map(lambda s: s.strip(), line.split(';'))))
attrs_old = {val: i for i, val in enumerate(['age', 'note', 'sex'])}
values = [50, '00000ah21jky', "woman"]

attr = AttrScaleNumeric(0, 'scale-age', 'age', '(x<70)')
print(attr.scale(attrs_old, values))

attr2 = AttrScaleEnum(2, 'scale-sex', 'sex', 'man')
print(attr2.scale(attrs_old, values))

attr3 = AttrScaleString(1, 'scale-note', 'note', 'ah[123]j')
print(attr3.scale(attrs_old, values))

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
