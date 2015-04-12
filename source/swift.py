#!/bin/python3
"""Main file of swift - FCA data converter"""

import argparse
# from convertor_fca import Convertor

SOURCE_ARGS = {"source": "source",
               "source_separator": "separator",
               "source_attributes": "str_attrs"}
TARGET_ARGS = {"target": "source",
               "target_separator": "separator",
               "target_attributes": "str_attrs",
               "target_objects": "str_objects",
               "relation_name": "relation_name"}

parser = argparse.ArgumentParser()

parser.add_argument("-s", "--source", help="Name of source file")
parser.add_argument("-ss", "--source_separator",
                    help="Separator whitch is used in source file. Default is ','")
parser.add_argument("-sa", "--source_attributes", help="Source file (old) attributes")
parser.add_argument("-t", "--target", help="Name of target file")
parser.add_argument("-ts", "--target_separator",
                    help="Separator whitch will be used in target file. Default is ','")
parser.add_argument("-ta", "--target_attributes", help="Target file (new) attributes")
parser.add_argument("-to", "--target_objects", help="Target file (new) objects")
parser.add_argument("-rn", "--relation_name", help="New name of relation")

args = parser.parse_args()

old_file_args = {}
new_file_args = {}

for key, val in vars(args).items():
    if key in SOURCE_ARGS:
        new_key = SOURCE_ARGS[key]
        old_file_args[new_key] = val
    elif key in TARGET_ARGS:
        new_key = TARGET_ARGS[key]
        new_file_args[new_key] = val

print(old_file_args)
print(new_file_args)

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

# convertor = Convertor(old, new)
# convertor.convert()


"""
# Regular expression
pattern = re.compile("(\w+)=(\w+)" +
                     "((?:\((?:[0-9]+(?:>=|<=|>|<))?x(?:>=|<=|>|<)[0-9]+\)i)|" +  # NOQA
                     "(?:\(.*\)r))?")

attrs = pattern.findall("a=b, novy1=puvodni1(10<=x<=100)i, novy2=puvodni2(x<=50)i, novy3=puvodni3(man)r")

"""
