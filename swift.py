#!/bin/python
"""Main file of swift - FCA data converter"""

import re

class Attribute(object):
    def __init__(self, index, name=""):
        self.__name = name
        self.__index = index

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def index(self):
        return self.__index


A = Attribute(0, "vaha")
A.name = "delka"
print A.name, A.index

result = re.findall("(?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+", "A=a[10<=x<=100], B=b[x<=50]")

x = 50
for expr in result:
    print eval(expr)
