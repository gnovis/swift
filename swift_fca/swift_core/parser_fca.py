from pyparsing import (Or, Empty, CharsNotIn, ZeroOrMore, nums, LineEnd,
                       Group, removeQuotes, Literal, restOfLine, lineno, ParseException,
                       Optional, delimitedList, printables, OneOrMore, Forward,
                       Suppress, Word, quotedString, CaselessLiteral)

from .attributes_fca import (Attribute, AttrNumeric, AttrDate,
                             AttrEnum, AttrString)
from .date_parser_fca import DateParser
from .grammars_fca import interval, numeric, boolexpr
from .errors_fca import HeaderError, FormulaNamesError, FormulaSyntaxError, SequenceSyntaxError, LineError
from .constants_fca import FileType, Bival
from .interval_fca import Interval, Intervals


class Parser():

    GENERAL_TYPE = 'g'
    ENUM = 'e'
    ATTR_CLASSES = {'n': AttrNumeric,
                    'numeric': AttrNumeric,
                    'continuous': AttrNumeric,
                    ENUM: AttrEnum,
                    'nominal': AttrEnum,
                    'discrete': AttrEnum,
                    's': AttrString,
                    'string': AttrString,
                    'd': AttrDate,
                    'date': AttrDate,
                    GENERAL_TYPE: Attribute,
                    '': Attribute,
                    'relational': Attribute}

    def __init__(self):
        self._index = 0
        self._attributes = []

    @property
    def attributes(self):
        return self._attributes.copy()

    @staticmethod
    def expand_sequence_grammar(max_attrs_i):

        def expand_interval(tokens):
            val_from = int(tokens[0])
            val_to = int(tokens[1]) + 1
            result = list(map(str, range(val_from, val_to)))
            return result

        name = interval(max_attrs_i, expand_interval) | Word(printables, excludeChars="[]-,=:;")
        names = delimitedList(name)
        return names


class FormulaParser(Parser):

    def clone_names(self, tokens):
        if tokens[0] == "":
            return [tokens[1]] * 2
        else:
            return [tokens[0], tokens[1]]

    def _parse_int(self, value):
        try:
            return int(value)
        except ValueError:
            return None

    def _create_attribute(self, tokens):

        def process_attr_type(tokens):
            attr_type = tokens.attr_type
            cls = AttrDate
            next_args = {}
            if type(attr_type) is str:  # attr_type is only identifier of class
                cls = self.ATTR_CLASSES[attr_type]
            else:  # attr_type is list with attributes, currently only a date has attribute format
                next_args = dict(date_format=attr_type[1])
                if tokens.date_format_new:
                    next_args['date_format'] = tokens.date_format_new[0]
            return [cls, next_args]

        NEW_NAMES = 0
        OLD_NAMES = 1
        CLASS = 0
        NEXT = 1

        old_names = tokens[OLD_NAMES]
        new_names = tokens[NEW_NAMES]
        attribute_type = process_attr_type(tokens)
        cls = attribute_type[CLASS]
        next_args = attribute_type[NEXT]

        true = Bival.true()
        false = Bival.false()
        bin_vals = tokens.get('new_bins')
        if bin_vals:
            if bin_vals.new_true:
                true = bin_vals.new_true
            if bin_vals.new_false:
                false = bin_vals.new_false

        scale = tokens.scale
        unpack = tokens.get('unpack', defaultValue=False)
        if unpack:
            cls = AttrEnum

        if len(old_names) != len(new_names):
            raise FormulaNamesError(old_names, new_names)

        for old, new in zip(old_names, new_names):
            old = str(old)
            new = str(new)
            curr_next_args = next_args.copy()
            curr_next_args['attr_pattern'] = old
            curr_next_args['expr_pattern'] = scale
            index = self._parse_int(old)
            attribute = cls(index, new, **curr_next_args)
            attribute.true = true
            attribute.false = false
            attribute.unpack = unpack
            self._attributes.append(attribute)

    def parse(self, str_args, max_attrs_i):

        date_val = quotedString
        quoted_str = quotedString.copy()
        quoted_str.setParseAction(removeQuotes)
        comma = Suppress(",")
        bin_vals = Group(Optional((Suppress("0=") + quoted_str("new_false") + comma)) + Optional(Suppress("1=")) + quoted_str("new_true"))
        date_format = Optional(Suppress(CaselessLiteral("F="))) + quoted_str
        date_scale = boolexpr(date_val) + Optional(Suppress("/") + date_format)("date_format_new")
        str_scale = quoted_str
        enum_scale = quoted_str
        num_scale = boolexpr(numeric())
        # name = interval(max_attrs_i, expand_interval) | Word(printables, excludeChars="[]-,=:;")
        scale = num_scale | enum_scale | str_scale | date_scale
        typ = Or(CaselessLiteral("n") ^ CaselessLiteral("e") ^
                 CaselessLiteral("s") ^ Group(Literal("d") + Optional(Suppress("/") + date_format("date_format"), default="%Y-%m-%dT%H:%M:%S")))
        # names = Group(delimitedList(name))
        names = Group(self.expand_sequence_grammar(max_attrs_i))
        new_old_names = (Optional(names + Suppress("="), default='') + names).setParseAction(self.clone_names)
        formula = (new_old_names +
                   Optional(Or(Literal("[]")("unpack").setParseAction(lambda t: True) ^
                               (Suppress("[") + bin_vals("new_bins") + Suppress("]")) ^
                               (Suppress(":") + typ("attr_type") +
                                Optional(Suppress("[") + Optional(scale("scale")) + Suppress("]"))))))
        formulas = delimitedList(formula, delim=";") + Optional(Suppress(";"))

        formula.setParseAction(self._create_attribute)

        # Run parser
        try:
            formulas.parseString(str_args, parseAll=True)
        except ParseException as e:
            raise FormulaSyntaxError(e.lineno, e.col, e.line, e)


class ArffParser(Parser):

    """
    Arff Grammar
    ============

    <header> ::= <relation_part> <attributes_part> <data_part>
    <relation_part> ::= <comment_line>* <relation> "\n" <comment_line>*
    <attributes_part> ::= <attribute_line> | ("\n" <attribute_line>)*
    <data_part> ::= "@data" "\n" (<data_line> | ("\n" <data_line>)*)
    <data_line> ::= <comment> | <instance> | <blank>
    <instance> ::= <string> | ("," <string>)*
    <attribute_line> ::= <comment> | <attribute> | <blank>
    <attribute> ::= "@attribute" <string> <type>
    <type> ::= "numeric" | "string" | <nominal> | <date> | <relational>
    <nominal> ::= "{" <string> | ("," <string>)* "}"
    <date> ::= 'date' <string>?
    <relational> ::= "relational" "\n" <attribute_part> "@end" <string>
    <relation> ::= "@relation" <string>?
    <string> ::= [^%,{}]+ | "'" .+ "'"
    <blank> ::= ^$
    <comment> ::= "%".*
    <comment_line> ::= <comment> "\n"
    """

    def __init__(self, separator):
        super().__init__()
        self._relation_name = ''
        self._data_start = 0
        self._separator = separator
        # first level relational attribute occurrences
        self._rel_occur = []
        self._delim_list_parser = self._delim_list(separator)
        self._rel_delim_list_parser = self._relational_delim_list(separator)

    @property
    def relation_name(self):
        return self._relation_name

    @property
    def data_start(self):
        return self._data_start

    def get_values(self, t):
        return {'values': t[0].asList()}

    def parse(self, header):
        comment = self._comment()
        quoted = quotedString.copy().setParseAction(removeQuotes)
        string = quoted | Word(printables,  excludeChars='{},%')
        relation = (Suppress(CaselessLiteral("@relation")) +
                    Optional(restOfLine, default='default_name')('rel_name').setParseAction(lambda t: t.rel_name.strip()))
        relation_part = ZeroOrMore(comment) + relation + ZeroOrMore(comment)
        nominal = (Empty().copy().setParseAction(lambda t: self.ENUM) +
                   Suppress(Literal("{")) +
                   Group(delimitedList(string, delim=self._separator))("next_arg").setParseAction(self.get_values) +
                   Suppress(Literal("}")))

        date = CaselessLiteral("date") + Optional(CharsNotIn("{},\n"))("next_arg").setParseAction(self._adapt_date_format)
        attributes_part = Forward()
        relational = CaselessLiteral("relational") + attributes_part + Suppress(CaselessLiteral("@end")) + string
        attr_type = (CaselessLiteral("numeric") | CaselessLiteral("string") | nominal | date | relational)("attr_type")
        attribute = Suppress(CaselessLiteral("@attribute")) + (string.copy())("attr_name") + attr_type
        attribute_line = comment | attribute
        attributes_part << (Group(OneOrMore(attribute_line)))("children")
        data_part = (CaselessLiteral("@data"))("data_start").setParseAction(lambda s, p, k: (lineno(p, s)))
        arff_header = relation_part + attributes_part + data_part
        attribute.setParseAction(self._create_attribute)

        try:
            result = arff_header.parseString(header, parseAll=True)
        except ParseException as e:
            raise HeaderError(FileType.ARFF, e.lineno, e.col, e.line, e)

        self._relation_name = result.rel_name
        self._find_relational(result.children)
        self._linearize_attrs(result.children)
        self._data_start = result.data_start
        self._index = 0

    def parse_line(self, line):
        self._index = 0
        try:
            result = self._rel_delim_list_parser.parseString(line, parseAll=True).asList()
        except ParseException as e:
            raise LineError(FileType.ARFF, e.lineno, e.col, line, e)
        return result

    def show_result(self):
        """Method only for testing"""
        print(self.relation_name)
        print(self.data_start)
        for a in self._attributes:
            print(a.name, a.index)

    """ Auxiliary methods for parse"""

    def _create_attribute(self, tokens):
        kwargs = tokens.get('next_arg', defaultValue={})
        attr = self.ATTR_CLASSES[tokens.attr_type](self._index, tokens.attr_name, **kwargs)
        if tokens.attr_type == "relational":
            attr.children = tokens.children
        else:
            self._index += 1
        return attr

    def _adapt_date_format(self, tokens):
        date_format = tokens.next_arg.strip()
        if not date_format:
            date_format = DateParser.ISO_FORMAT
        return {'date_format': date_format}

    def _linearize_attrs(self, attrs, parent_name=""):
        for attr in attrs:
            name = attr.name
            if parent_name:
                name = ".".join([parent_name, name])
            attr.name = name
            if attr.has_children():
                self._linearize_attrs(attr.children, name)
            else:
                self._attributes.append(attr)

    """Auxiliary methods for parse_line"""

    def _find_relational(self, attrs):
        for i, attr in enumerate(attrs):
            if attr.has_children():
                self._rel_occur.append(i)

    def _parse_rel(self, value, sep):
        if self._index in self._rel_occur:
            rel = self._delim_list_parser.parseString(str(value))
            return rel

    def _inc_index(self):
        self._index += 1

    def _delim_list(self, sep):
        quoted = quotedString.copy()
        value = quoted | Word(printables,  excludeChars=('%' + sep))
        parser = delimitedList(value, delim=sep)
        return parser

    def _relational_delim_list(self, sep):
        quoted = quotedString.copy()
        quoted.setParseAction(lambda s, p, t: self._parse_rel(removeQuotes(s, p, t), sep))
        value = quoted | Word(printables,  excludeChars=('%' + sep))
        value.setParseAction(self._inc_index)
        comment = self._comment()
        parser = comment | delimitedList(value, delim=sep)
        return parser

    def _comment(self):
        return Suppress(Literal("%") + restOfLine)


class DataParser(Parser):

    """
    Grammar for .names file
    =======================

    <names> ::= <entry> | (<delimiter> <entry>)*
    <entry> ::= <classes> | <attribute> | <blank>
    <classes> ::= <string> | <string> "," <classes> | <comment>
    <attribute> ::= <string> ":" <type> <comment>? | <comment>
    <blank> ::= \s*
    <delimiter> ::= "." | "\n"
    <string> ::= [^|?,.\s]+
    <type> ::= "continuous" | "ignore"| <discrete> | <enum>
    <discrete> ::= "discrete" \d+
    <enum> ::= <string> | ("," <string>)*
    <comment> ::= "|".*
    """

    def __init__(self):
        super().__init__()
        self._classes = []

    @property
    def attributes(self):
        self._attributes.append(AttrEnum(self._index, "class"))
        return self._attributes.copy()

    @property
    def classes(self):
        return self._classes.copy()

    def _create_attribute(self, tokens):
        if tokens.type == "ignore":
            return
        kwargs = tokens.get('next_arg', defaultValue={})
        attr = self.ATTR_CLASSES[tokens.type](self._index, tokens.name, **kwargs)
        self._attributes.append(attr)
        self._index += 1

    def _get_class(self, tokens):
        self._classes.append(tokens.cls)

    def _remove_dots(self, t):
        value = t[0]
        if value.endswith("."):
            return value[:-1]
        return value

    def parse(self, file_path):
        string = Word(printables, excludeChars="|?,:").setParseAction(self._remove_dots)
        comment = "|" + restOfLine
        delimiter = Suppress(".") | LineEnd()
        enum = (Empty().copy().setParseAction(lambda t: self.ENUM) +
                Group(delimitedList(string))("next_arg").setParseAction(lambda t: {'values': t.next_arg.asList()}))
        discrete = Literal("discrete") + Suppress(Word(nums))
        attr_type = (Literal("continuous") | Literal("ignore") | discrete | enum)("type")
        attribute = string("name") + Suppress(":") + attr_type
        cls = string("cls")
        cls.addParseAction(self._get_class)
        classes = delimitedList(cls)
        entry = attribute | classes
        attribute.setParseAction(self._create_attribute)
        parser = OneOrMore(entry + Optional(delimiter))
        parser.ignore(comment)
        try:
            parser.parseFile(file_path, parseAll=True)
        except ParseException as e:
            raise HeaderError(FileType.DATA, e.lineno, e.col, e.line, e)


def parse_intervals(string):
    if not string:
        return Intervals([])
    seq = delimitedList(interval(end=float('inf'), func=lambda t: Interval(t[0], t[1])) |
                        Word(nums)("num").setParseAction(lambda t: Interval(t.num, t.num)))
    try:
        return Intervals(seq.parseString(string, parseAll=True).asList())
    except ParseException as e:
        raise SequenceSyntaxError(e.lineno, e.col, e.line, e)


def parse_sequence(str_to_parse, max_attrs_i):
    if not str_to_parse:
        return []
    seq = Parser.expand_sequence_grammar(max_attrs_i)

    try:
        return seq.parseString(str_to_parse, parseAll=True).asList()
    except ParseException as e:
        raise SequenceSyntaxError(e.lineno, e.col, e.line, e)
