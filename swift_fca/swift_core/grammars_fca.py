from pyparsing import Literal, Combine, Optional, Or, Word, alphas, nums, CaselessLiteral, Suppress


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
            Literal("==") ^ Literal("!="))
    EXPR = Or(Combine(VAR + OP + VAL, adjacent=False) ^
              Combine(VAL + OP + VAR, adjacent=False) ^
              Combine(VAL + OP + VAR + OP + VAL, adjacent=False))
    return EXPR


def interval(end=0, func=lambda t: t):
    INTERVAL = Optional(Word(nums), default=0) + Suppress("-") + Optional(Word(nums), default=end)
    INTERVAL.setParseAction(func)
    return INTERVAL
