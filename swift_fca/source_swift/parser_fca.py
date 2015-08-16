from pyparsing import (alphanums, Or, Empty, CharsNotIn, ZeroOrMore,
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
                    ENUM: AttrScaleEnum,
                    'nominal': AttrScaleEnum,
                    's': AttrScaleString,
                    'string': AttrScaleString,
                    'd': AttrScaleDate,
                    'date': AttrScaleDate,
                    GENERAL_TYPE: AttrScale,
                    'relational': AttrScale}

    def __init__(self):
        self.count = 0
        self._attributes = []

    @property
    def attributes(self):
        return self._attributes.copy()


class ArgsParser(Parser):

    NEW_NAME = 0
    OLD_NAME = 1
    ARGS = 2
    TYPE = 0
    NEXT_ARGS = 1

    def create_attribute(self, tokens):
        old_name = tokens[self.OLD_NAME]
        new_name = tokens[self.NEW_NAME]
        attr_type = tokens[self.ARGS][self.TYPE]
        next_args = tokens[self.ARGS][self.NEXT_ARGS]
        next_args['attr_pattern'] = old_name

        cls = self.ATTR_CLASSES[attr_type]
        attribute = cls(self.count, new_name, **next_args)
        self._attributes.append(attribute)
        self.count += 1

    def parse(self, str_args):
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
        NAME = Word(alphanums + '_-')
        VAR_FIRST_PART = Optional(NAME + Suppress('='), default='') + NAME
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
        VAR.setParseAction(self.create_attribute)

        # Run parser
        parser.parseString(str_args)


class ArffParser(Parser):

    def __init__(self):
        super().__init__()
        self._relation_name = ''
        self._data_start = 0

    @property
    def relation_name(self):
        return self._relation_name

    @property
    def data_start(self):
        return self._data_start

    def create_attribute(self, tokens):
        kwargs = tokens.get('next_arg', defaultValue={})
        attr = self.ATTR_CLASSES[tokens.attr_type](self.count, tokens.attr_name, **kwargs)
        if tokens.attr_type == "relational":
            attr.children = tokens.children
        else:
            self.count += 1
        return attr

    def adapt_date_format(self, tokens):
        date_format = tokens.date_format.strip()
        if not date_format:
            date_format = '%Y-%m-%d'
        return {'date_format': date_format}

    def linearize_attrs(self, attrs, parent_name=""):
        for attr in attrs:
            name = attr.name
            if parent_name:
                name = ".".join([parent_name, name])
            attr.name = name
            if attr.has_children():
                self.linearize_attrs(attr.children, name)
            else:
                self._attributes.append(attr)

    def parse(self, header):
        comment = Suppress(Literal("%") + restOfLine)
        quoted = quotedString.copy().setParseAction(removeQuotes)
        string = quoted | Word(printables,  excludeChars='{},%')
        relation = Suppress(CaselessLiteral("@relation")) + Optional(string, default='default_name')('rel_name')
        relation_part = ZeroOrMore(comment) + relation + ZeroOrMore(comment)
        nominal = (Suppress(Literal("{")) +
                   Group(delimitedList(string)) + Suppress(Literal("}"))).setParseAction(lambda t: self.ENUM)
        date = CaselessLiteral("date") + Optional(CharsNotIn("{},\n"))("next_arg").setParseAction(self.adapt_date_format)
        attributes_part = Forward()
        relational = CaselessLiteral("relational") + attributes_part + Suppress(CaselessLiteral("@end")) + string
        attr_type = (CaselessLiteral("numeric") | CaselessLiteral("string") | nominal | date | relational)("attr_type")
        attribute = Suppress(CaselessLiteral("@attribute")) + (string.copy())("attr_name") + attr_type
        attribute_line = comment | attribute
        attributes_part << (Group(OneOrMore(attribute_line)))("children")
        data_part = (CaselessLiteral("@data"))("data_start").setParseAction(lambda s, p, k: (lineno(p, s)))
        arff_header = relation_part + attributes_part + data_part
        attribute.setParseAction(self.create_attribute)
        result = arff_header.parseString(header)

        self._relation_name = result.rel_name
        self.linearize_attrs(result.children)
        self._data_start = result.data_start

    def show_result(self):
        """Method only for testing"""
        print(self.relation_name)
        print(self.data_start)
        for a in self._attributes:
            print(a.name, a.index)
