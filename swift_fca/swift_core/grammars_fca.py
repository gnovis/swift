from pyparsing import Literal, Combine, Optional, Or, Word, alphas, nums, CaselessLiteral, Suppress


def numeric():
    point = Literal('.')
    e = CaselessLiteral('E')
    plusorminus = Literal('+') | Literal('-')
    number = Word(nums)
    integer = Combine(Optional(plusorminus) + number)
    numeric = Combine(integer +
                      Optional(point + Optional(number)) +
                      Optional(e + integer))
    return numeric


def boolexpr(VAL=None):
    if not VAL:
        VAL = numeric()
    VAR = Word(alphas + "_")
    OP = Or(Literal("<") ^ Literal(">") ^
            Literal("<=") ^ Literal(">=") ^
            Literal("==") ^ Literal("!="))
    EXPR = Or(Combine(VAR + OP + VAL, adjacent=False) ^
              Combine(VAL + OP + VAR, adjacent=False) ^
              Combine(VAL + OP + VAR + OP + VAL, adjacent=False))
    return EXPR


def interval(end=0, func=lambda t: t):
    SEPARATOR = Suppress('-') | Suppress('*')
    INTERVAL = Optional(Word(nums), default=0) + SEPARATOR + Optional(Word(nums), default=end)
    INTERVAL.setParseAction(func)
    return INTERVAL
