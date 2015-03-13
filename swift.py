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
# print A.name, A.index

pattern = re.compile("(\w+)=(\w+)" +
                     "((?:\((?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+\)i)|" +
                     "(?:\(.*\)r))?")

attrs = pattern.findall("a=b, novy1=puvodni1(10<=x<=100)i, novy2=puvodni2(x<=50)i, novy3=puvodni3(man)r")

for at in attrs:
    print at

m = "(a[ho?j]ky)r"
new = m[1:-2]
print new

