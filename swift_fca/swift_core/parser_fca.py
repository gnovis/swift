from pyparsing import (alphanums, Or, Empty, CharsNotIn, ZeroOrMore, nums, LineEnd,
                       Group, removeQuotes, Literal, restOfLine, lineno,
                       Optional, delimitedList, printables, OneOrMore, Forward,
                       Suppress, Word, quotedString, CaselessLiteral)

from .attributes_fca import (AttrScale, AttrScaleNumeric, AttrScaleDate,
                             AttrScaleEnum, AttrScaleString)
from .date_parser_fca import DateParser
from .grammars_fca import boolexpr


class Parser():

    GENERAL_TYPE = 'g'
    ENUM = 'e'
    ATTR_CLASSES = {'n': AttrScaleNumeric,
                    'numeric': AttrScaleNumeric,
                    'continuous': AttrScaleNumeric,
                    ENUM: AttrScaleEnum,
                    'nominal': AttrScaleEnum,
                    'discrete': AttrScaleEnum,
                    's': AttrScaleString,
                    'string': AttrScaleString,
                    'd': AttrScaleDate,
                    'date': AttrScaleDate,
                    GENERAL_TYPE: AttrScale,
                    'relational': AttrScale}

    def __init__(self):
        self._index = 0
        self._attributes = []

    @property
    def attributes(self):
        return self._attributes.copy()


class ArgsParser(Parser):

    """
    Swift Arguments Grammar
    =======================

    <formula_list> ::= <formula> | <formula> <comma> <formula_list>
    <formula> ::= <formula_first_part> <formula_second_part>
    <formula_first_part> ::= (<name> "=")? <name>
    <formula_second_part> ::= "[" <args>? "]"
    <name> ::= \w+
    <args> ::= <num_arg> | <enum_arg> | <str_arg> | <date_arg> | <no_scale_arg>
    <num_arg> ::= "n" <comma> <num_expr>
    <enum_arg> ::= "e" <comma> "'" \w+ "'"
    <str_arg> ::= "s" <comma> "'" .+ "'"
    <date_arg> ::= "d" <comma> <date_expr> (<comma> "'" .+ "'")?
    <expr_var> ::= [a-zA-Z_]
    <num_val> ::= "-"? \d
    <num_expr> ::= <expr_var> <op> <num_val> |
                   <num_val> <op> <expr_var> |
                   <num_val> <op> <expr_var> <op> <num_val>
    <date_val> ::= "'" .+ "'"
    <date_expr> ::= <expr_var> <op> <date_val> |
                    <date_val> <op> <expr_var> |
                    <date_val> <op> <expr_var> <op> <date_val>
    <op> ::= "<" | ">" | "<=" | ">=" | "=="
    <no_scale_arg> ::= <no_scale_num> | <no_scale_enum> | <no_scale_str> | <no_scale_date>
    <no_scale_num> ::= "n"
    <no_scale_enum> ::= "e"
    <no_scale_str> ::= "s"
    <no_scale_date> ::= "d" <comma> (<comma> "'" .+ "'")?
    <comma> ::= ","
    """

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

        for old, new in zip(old_names, new_names):
            curr_next_args = next_args.copy()
            curr_next_args['attr_pattern'] = old

            index = self._parse_int(old)

            attribute = cls(index, new, **curr_next_args)
            self._attributes.append(attribute)

    def parse(self, str_args):

        def expand_interval(tokens):
            val_from = int(tokens[0])
            val_to = int(tokens[1]) + 1
            result = list(map(str, range(val_from, val_to)))
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
        INTERVAL = Word(nums) + Suppress("-") + Word(nums)
        INTERVAL.setParseAction(expand_interval)
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
        parser.parseString(str_args)


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

    def parse(self, header):
        comment = self._comment()
        quoted = quotedString.copy().setParseAction(removeQuotes)
        string = quoted | Word(printables,  excludeChars='{},%')
        relation = (Suppress(CaselessLiteral("@relation")) +
                    Optional(restOfLine, default='default_name')('rel_name').setParseAction(lambda t: t.rel_name.strip()))
        relation_part = ZeroOrMore(comment) + relation + ZeroOrMore(comment)
        nominal = (Suppress(Literal("{")) +
                   Group(delimitedList(string, delim=self._separator)) + Suppress(Literal("}"))).setParseAction(lambda t: self.ENUM)
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
        result = arff_header.parseString(header)

        self._relation_name = result.rel_name
        self._find_relational(result.children)
        self._linearize_attrs(result.children)
        self._data_start = result.data_start
        self._index = 0

    def parse_line(self, line):
        self._index = 0
        return self._rel_delim_list_parser.parseString(line).asList()

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
        date_format = tokens.date_format.strip()
        if not date_format:
            date_format = '%Y-%m-%d'
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
        self._attributes.append(AttrScaleEnum(self._index, "class"))
        return self._attributes.copy()

    @property
    def classes(self):
        return self._classes.copy()

    def _create_attribute(self, tokens):
        if tokens.type == "ignore":
            return
        attr = self.ATTR_CLASSES[tokens.type](self._index, tokens.name)
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
        enum = Group(delimitedList(string)).setParseAction(lambda t: self.ENUM)
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
        parser.parseFile(file_path, parseAll=True)
