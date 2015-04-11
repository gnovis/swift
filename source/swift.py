#!/bin/python3
"""Main file of swift - FCA data converter"""

from convertor_fca import Convertor

# Notes
#
# Testovano:
# csv -> dat
# csv -> cxt
# dat -> csv
# dat -> cxt
# cxt -> dat
# cxt -> csv
# arff -> csv
# arff -> dat
# arff -> cxt
# csv -> arff
# cxt -> arff
# dat -> arff


# Tests

old_str_attrs = 'age,note,sex'

# atributes for scaling
new_str_attrs = "AGE=age[x<50]n, NOTE=note[aaa]s, NUMBER=num, MAN=sex[man]e, WOMAN=sex[woman]e"  # NOQA
new_str_attrs_2 = "SUNNY=outlook[sunny]e, TEMP=temperature[x>80]n, HUM=humidity[70<=x<=80]n"  # NOQA

# obejcts
new_str_objects = "Jan,Petr,Lucie,Jana,Aneta"
new_str_objects_2 = "0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13"

old = dict(source="test.dat")
new = dict(source="dat.arff")

convertor = Convertor(old, new)
convertor.convert()


"""
# Regular expression
pattern = re.compile("(\w+)=(\w+)" +
                     "((?:\((?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+\)i)|" +  # NOQA
                     "(?:\(.*\)r))?")

attrs = pattern.findall("a=b, novy1=puvodni1(10<=x<=100)i, novy2=puvodni2(x<=50)i, novy3=puvodni3(man)r")

"""
