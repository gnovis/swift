from pyparsing import (alphanums, Or, Empty, CharsNotIn, ZeroOrMore, nums, LineEnd,
                       Group, removeQuotes, Literal, restOfLine, lineno, ParseException,
                       Optional, delimitedList, printables, OneOrMore, Forward,
                       Suppress, Word, quotedString, CaselessLiteral)

from .attributes_fca import (Attribute, AttrNumeric, AttrDate,
                             AttrEnum, AttrString)
from .date_parser_fca import DateParser
from .grammars_fca import boolexpr, interval
from .errors_fca import HeaderError, FormulaNamesError, FormulaSyntaxError, SequenceSyntaxError, LineError
from .constants_fca import FileType
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
                    'relational': Attribute}

    def __init__(self):
        self._index = 0
        self._attributes = []

    @property
    def attributes(self):
        return self._attributes.copy()


class FormulaParser(Parser):

    NEW_NAME = 0
    OLD_NAME = 1
    ARGS = 2
    TYPE = 0
    NEXT_ARGS = 1

    def _parse_int(self, value):
        try:
            return int(value)
        except ValueError:
            return None

    def _create_attribute(self, tokens):
        old_names = tokens[self.OLD_NAME]
        new_names = tokens[self.NEW_NAME]
        attr_type = tokens[self.ARGS][self.TYPE]
        next_args = tokens[self.ARGS][self.NEXT_ARGS]
        cls = self.ATTR_CLASSES[attr_type]

        if len(old_names) != len(new_names):
            raise FormulaNamesError(old_names, new_names)

        for old, new in zip(old_names, new_names):
            old = str(old)
            new = str(new)
            curr_next_args = next_args.copy()
            curr_next_args['attr_pattern'] = old

            index = self._parse_int(old)

            attribute = cls(index, new, **curr_next_args)
            self._attributes.append(attribute)

    def parse(self, str_args, max_attrs_i):
        def expand_interval(tokens):
            val_from = int(tokens[0])
            val_to = int(tokens[1]) + 1
            result = list(range(val_from, val_to))
            return result

        # Grammar definition
        QUOTED_STR = quotedString.copy()
        NUMEXPR = boolexpr()
        DATEXPR = boolexpr(VAL=quotedString)
        SCOMMA = Suppress(',')
        DATE_FORMAT = Optional(SCOMMA + QUOTED_STR, default=DateParser.ISO_FORMAT)
        NO_SCALE_NUM = CaselessLiteral('n')
        NO_SCALE_DATE = CaselessLiteral('d') + DATE_FORMAT
        NO_SCALE_ENUM = CaselessLiteral('e')
        NO_SCALE_STR = CaselessLiteral('s')
        NUM = CaselessLiteral('n') + SCOMMA + NUMEXPR
        DATE = CaselessLiteral('d') + SCOMMA + DATEXPR + DATE_FORMAT
        ENUM = CaselessLiteral('e') + SCOMMA + Word(alphanums)
        STR = CaselessLiteral('s') + SCOMMA + QUOTED_STR
        GEN = Empty()
        NO_SCALE = NO_SCALE_NUM | NO_SCALE_DATE | NO_SCALE_ENUM | NO_SCALE_STR
        PARAMS = Or(STR ^ ENUM ^ DATE ^ NUM ^ GEN ^ NO_SCALE)

        NAME = Word(printables, excludeChars="[]-,=")
        INTERVAL = interval(max_attrs_i, expand_interval)

        ATTR_SEQUENCE = Group(delimitedList((INTERVAL | NAME)))
        VAR_FIRST_PART = Optional(ATTR_SEQUENCE + Suppress('='), default='') + ATTR_SEQUENCE

        VAR_SECOND_PART = Suppress('[') + Group(PARAMS) + Suppress(']')
        VAR = VAR_FIRST_PART + VAR_SECOND_PART
        parser = delimitedList(VAR)

        # Parse actions for no scale attributes
        no_scale_default_action = lambda tokens: [tokens[0], {}]
        NO_SCALE_NUM.setParseAction(no_scale_default_action)
        NO_SCALE_ENUM.setParseAction(no_scale_default_action)
        NO_SCALE_STR.setParseAction(no_scale_default_action)
        NO_SCALE_DATE.setParseAction(lambda tokens: [tokens[0], dict(date_format=tokens[1])])

        # Parse actions for scale attributes
        scale_default_action = lambda tokens: [tokens[0], dict(expr_pattern=tokens[1])]
        NUM.setParseAction(scale_default_action)
        ENUM.setParseAction(scale_default_action)
        STR.setParseAction(scale_default_action)
        GEN.setParseAction(lambda tokens: [self.GENERAL_TYPE, {}])
        DATE.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1],
                                                            date_format=tokens[2])])
        # Auxiliary parse actions
        QUOTED_STR.setParseAction(removeQuotes)
        VAR_FIRST_PART.setParseAction(lambda tokens: [tokens[1]]*2 if tokens[0] == '' else [tokens[0], tokens[1]])
        VAR.setParseAction(self._create_attribute)

        # Run parser
        try:
            parser.parseString(str_args)
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
