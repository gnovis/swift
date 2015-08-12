from pyparsing import (alphanums, alphas, nums, Combine, Or, Empty,
                       Group, Literal,
                       Optional, delimitedList,
                       Suppress, Word, quotedString, CaselessLiteral)

from .attributes_fca import (AttrScale, AttrScaleNumeric, AttrScaleDate,
                             AttrScaleEnum, AttrScaleString)
from .date_parser_fca import DateParser
from .grammars_fca import boolexpr


class ArgsParser():

    NEW_NAME = 0
    OLD_NAME = 1
    ARGS = 2
    TYPE = 0
    NEXT_ARGS = 1

    ATTR_CLASSES = {'n': AttrScaleNumeric,
                    'e': AttrScaleEnum,
                    's': AttrScaleString,
                    'd': AttrScaleDate,
                    'g': AttrScale}

    def __init__(self):
        self.count = 0
        self._attributes = []

    def create_attrs(self, tokens):
        old_name = tokens[self.OLD_NAME]
        new_name = tokens[self.NEW_NAME]
        attr_type = tokens[self.ARGS][self.TYPE]
        next_args = tokens[self.ARGS][self.NEXT_ARGS]
        next_args['attr_pattern'] = old_name

        cls = self.ATTR_CLASSES[attr_type]
        attribute = cls(self.count, new_name, **next_args)
        self._attributes.append(attribute)
        self.count += 1

    @property
    def attributes(self):
        return self._attributes.copy()

    @staticmethod
    def boolexpr(VAL=Combine(Optional('-') + Word(nums))):
        VAR = Word(alphas)
        OP = Or(Literal("<") ^ Literal(">") ^
                Literal("<=") ^ Literal(">=") ^
                Literal("=="))
        EXPR = Or(Combine(VAR + OP + VAL, adjacent=False) ^
                  Combine(VAL + OP + VAR, adjacent=False) ^
                  Combine(VAL + OP + VAR + OP + VAL, adjacent=False))
        return EXPR

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
        GEN.setParseAction(lambda tokens: ['g', {}])
        DATE.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1],
                                                            date_format=tokens[2])])
        # Auxiliary parse actions
        QUOTED_STR.setParseAction(lambda tokens: tokens[0][1:-1])
        VAR_FIRST_PART.setParseAction(lambda tokens: [tokens[1]]*2 if tokens[0] == '' else [tokens[0], tokens[1]])
        VAR.setParseAction(self.create_attrs)

        # Run parser
        parser.parseString(str_args)
