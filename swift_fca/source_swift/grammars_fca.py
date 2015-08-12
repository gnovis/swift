from pyparsing import Literal, Combine, Optional, Or, Word, alphas, nums


def boolexpr(VAL=Combine(Optional('-') + Word(nums))):
    VAR = Word(alphas)
    OP = Or(Literal("<") ^ Literal(">") ^
            Literal("<=") ^ Literal(">=") ^
            Literal("=="))
    EXPR = Or(Combine(VAR + OP + VAL, adjacent=False) ^
              Combine(VAL + OP + VAR, adjacent=False) ^
              Combine(VAL + OP + VAR + OP + VAL, adjacent=False))
    return EXPR
