#!/bin/python3
"""Main file of swift - FCA data converter"""

import argparse
from source_swift.convertor_fca import Convertor


def run_swift():
    SOURCE_ARGS = {"source": "source",
                   "source_separator": "separator",
                   "source_attributes": "str_attrs",
                   "first_line": "attrs_first_line"}
    TARGET_ARGS = {"target": "source",
                   "target_separator": "separator",
                   "target_attributes": "str_attrs",
                   "target_objects": "str_objects",
                   "relation_name": "relation_name",
                   "classes": "classes"}
    OTHER_ARGS = {"source_info": "print_info"}

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--source", required=True, help="Name of source file.")
    parser.add_argument("-ss", "--source_separator",
                        help="Separator whitch is used in source file. Default is ','.")
    parser.add_argument("-sa", "--source_attributes", help="Source file (old) attributes.")
    parser.add_argument("-si", "--source_info", action='store_true', help="Print information about source file data.")
    parser.add_argument("-fl", "--first_line",
                        action='store_true',
                        help="Read attribute names from first line in source file in csv format.")

    parser.add_argument("-t", "--target", required=True, help="Name of target file.")
    parser.add_argument("-ts", "--target_separator",
                        help="Separator whitch will be used in target file. Default is ','.")
    parser.add_argument("-ta", "--target_attributes", help="Target file (new) attributes.")
    parser.add_argument("-to", "--target_objects", help="Target file (new) objects.")
    parser.add_argument("-rn", "--relation_name", help="New name of relation.")
    parser.add_argument("-cls", "--classes", help="Classes seperated by commas - for C4.5 convert.")

    args = parser.parse_args()

    old_file_args = {}
    new_file_args = {}
    other_args = {}

    for key, val in vars(args).items():
        if val:
            if key in SOURCE_ARGS:
                new_key = SOURCE_ARGS[key]
                old_file_args[new_key] = val
            elif key in TARGET_ARGS:
                new_key = TARGET_ARGS[key]
                new_file_args[new_key] = val
            else:
                new_key = OTHER_ARGS[key]
                other_args[new_key] = val

    convertor = Convertor(old_file_args, new_file_args, **other_args)
    convertor.convert()

# Uncomment following line to run swift application
run_swift()

# TESTING
"""
"""
