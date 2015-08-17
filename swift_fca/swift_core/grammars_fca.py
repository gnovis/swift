from pyparsing import Literal, Combine, Optional, Or, Word, alphas, nums, CaselessLiteral


def numeric():
    point = Literal('.')
    e = CaselessLiteral('E')
    plusorminus = Literal('+') | Literal('-')
    number = Word(nums)
    integer = Combine(Optional(plusorminus) + number)
    floatnumber = Combine(integer +
                          Optional(point + Optional(number)) +
                          Optional(e + integer))
    numeric = number | floatnumber
    return numeric


def boolexpr(VAL=numeric()):
    VAR = Word(alphas)
    OP = Or(Literal("<") ^ Literal(">") ^
            Literal("<=") ^ Literal(">=") ^
            Literal("=="))
    EXPR = Or(Combine(VAR + OP + VAL, adjacent=False) ^
              Combine(VAL + OP + VAR, adjacent=False) ^
              Combine(VAL + OP + VAR + OP + VAL, adjacent=False))
    return EXPR
