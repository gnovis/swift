from pyparsing import (alphanums, alphas, nums, Combine, Or, Empty,
                       Group, Literal,
                       Optional, delimitedList,
                       Suppress, Word, quotedString, CaselessLiteral)

from .attributes_fca import (AttrScale, AttrScaleNumeric,
                             AttrScaleEnum, AttrScaleString, AttrScaleDate)


"""
Grammar for scale arguments

<attr_list> ::= <attribute> | <attribute> <comma> <attr_list>
<attribute> ::= <old_name> "=" <new_name> "[" <args>? "]"
<old_name> ::= \w+
<new_name> ::= \w+
<args> ::= <num_arg> | <enum_arg> | <str_arg> | <date_arg>
<num_arg> ::= "n" <comma> <num_expr>
<enum_arg> ::= "e" <comma> "'" \w+ "'"
<str_arg> ::= "s" <comma> "'" .+ "'"
<date_arg> ::= "d" <comma> <num_expr> (<comma> "'" .+ "'")?
<comma> ::= ","

"""


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

    def parse(self, str_args):

        # Grammar
        NUMVAL = Combine(Optional('-') + Word(nums))
        NUMVAR = Word(alphas)
        OP = Or(Literal("<") ^ Literal(">") ^
                Literal("<=") ^ Literal(">=") ^
                Literal("=="))
        NUMEXPR = Or(Combine(NUMVAR + OP + NUMVAL, adjacent=False) ^
                     Combine(NUMVAL + OP + NUMVAR, adjacent=False) ^
                     Combine(NUMVAL + OP + NUMVAR + OP + NUMVAL, adjacent=False))
        SCOMMA = Suppress(',')
        QUOTED_STR = quotedString
        N, D, E, S = list(map(CaselessLiteral, 'ndes'))
        NUM = N + SCOMMA + NUMEXPR
        DATE = D + SCOMMA + NUMEXPR + Optional(SCOMMA + QUOTED_STR, default="%Y-%m-%dT%H:%M:%S")
        ENUM = E + SCOMMA + Word(alphanums)
        STR = S + SCOMMA + QUOTED_STR
        GEN = Empty()
        NO_SCALE = N | D | E | S
        PARAMS = Or(STR ^ ENUM ^ DATE ^ NUM ^ GEN ^ NO_SCALE)
        NAME = Word(alphanums + '_-')
        VAR_FIRST_PART = NAME + Optional(Suppress('=') + NAME, default='')
        VAR_SECOND_PART = Suppress('[') + Group(PARAMS) + Suppress(']')
        VAR = VAR_FIRST_PART + VAR_SECOND_PART
        parser = delimitedList(VAR)

        # Parse Actions
        NO_SCALE.setParseAction(lambda tokens: [tokens[0], {}])
        GEN.setParseAction(lambda tokens: ['g', {}])
        NUM.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1])])
        DATE.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1],
                                                            date_format=tokens[2])])
        ENUM.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1])])
        STR.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1])])
        QUOTED_STR.setParseAction(lambda tokens: tokens[0][1:-1])
        VAR_FIRST_PART.setParseAction(lambda tokens: [tokens[0]]*2 if tokens[1] == '' else [tokens[0], tokens[1]])
        VAR.setParseAction(self.create_attrs)

        # Run parser
        parser.parseString(str_args)
