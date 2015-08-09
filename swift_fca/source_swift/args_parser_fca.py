from pyparsing import (alphanums, alphas, nums, Combine, Or, Empty,
                       Group, Literal,
                       Optional, delimitedList,
                       Suppress, Word, quotedString, CaselessLiteral)


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

    @staticmethod
    def parse(str_args, parse_func):

        NUMVAL = Word(nums)
        NUMVAR = Word(alphas)
        OP = Or(Literal("<") ^ Literal(">") ^
                Literal("<=") ^ Literal(">=") ^
                Literal("=="))
        NUMEXPR = Or(Combine(NUMVAR + OP + NUMVAL, adjacent=False) ^
                     Combine(NUMVAL + OP + NUMVAR, adjacent=False) ^
                     Combine(NUMVAL + OP + NUMVAR + OP + NUMVAL, adjacent=False))
        SCOMMA = Suppress(',')
        QUOTED_STR = quotedString
        NUM = CaselessLiteral('n') + SCOMMA + NUMEXPR
        DATE = CaselessLiteral('d') + SCOMMA + NUMEXPR + Optional(SCOMMA + QUOTED_STR, default="%Y-%m-%dT%H:%M:%S")
        ENUM = CaselessLiteral('e') + SCOMMA + Word(alphanums)
        STR = CaselessLiteral('s') + SCOMMA + QUOTED_STR
        GEN = Empty()
        PARAMS = Or(STR ^ ENUM ^ DATE ^ NUM ^ GEN)
        OLD = Word(alphanums)
        NEW = Word(alphanums)
        VAR = OLD + Suppress('=') + NEW + Suppress('[') + Group(PARAMS) + Suppress(']')
        parser = delimitedList(VAR)

        GEN.setParseAction(lambda tokens: ['g', {}])
        NUM.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1])])
        DATE.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1],
                                                            date_format=tokens[2])])
        ENUM.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1])])
        STR.setParseAction(lambda tokens: [tokens[0], dict(expr_pattern=tokens[1])])
        QUOTED_STR.setParseAction(lambda tokens: tokens[0][1:-1])
        VAR.setParseAction(parse_func)

        parser.parseString(str_args)
