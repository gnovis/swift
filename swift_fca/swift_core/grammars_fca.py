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
            Literal("=="))
    EXPR = Or(Combine(VAR + OP + VAL, adjacent=False) ^
              Combine(VAL + OP + VAR, adjacent=False) ^
              Combine(VAL + OP + VAR + OP + VAL, adjacent=False))
    return EXPR


def interval(end=0):
    def expand_interval(tokens):
        val_from = int(tokens[0])
        val_to = int(tokens[1]) + 1
        result = list(range(val_from, val_to))
        return result
    INTERVAL = Optional(Word(nums), default=0) + Suppress("-") + Optional(Word(nums), default=end)
    INTERVAL.setParseAction(expand_interval)
    return INTERVAL
