"""Main file of swift - FCA data converter"""

import argparse
import sys
from .swift_core.managers_fca import Convertor
from .swift_core.constants_fca import RunParams


def run_swift():

    SOURCE_ARGS = {"source": RunParams.SOURCE,
                   "source_format": RunParams.FORMAT,
                   "source_separator": RunParams.SOURCE_SEP,
                   "source_attributes": RunParams.SOURCE_ATTRS,
                   "no_first_line": RunParams.NFL,
                   "none_value": RunParams.NONE_VALUE}
    TARGET_ARGS = {"target": RunParams.TARGET,
                   "target_format": RunParams.FORMAT,
                   "target_separator": RunParams.TARGET_SEP,
                   "target_attributes": RunParams.TARGET_ATTRS,
                   "target_objects": RunParams.TARGET_OBJECTS,
                   "relation_name": RunParams.RELATION_NAME,
                   "classes": RunParams.CLASSES}
    OTHER_ARGS = {"source_info": RunParams.SOURCE_INFO}

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--source", nargs="?", type=argparse.FileType('r'), default=sys.stdin, help="Name of source file.")
    parser.add_argument("-ss", "--source_separator",
                        help="Separator whitch is used in source file. Default is ','.")
    parser.add_argument("-sa", "--source_attributes", help="Source file (old) attributes. Used as additional informations.")
    parser.add_argument("-si", "--source_info", action='store_true', help="Print information about source file data.")
    parser.add_argument("-nv", "--none_value", help="Character which is used in data as value for non-specified attribute.")
    parser.add_argument("-nfl", "--no_first_line",
                        action='store_true',
                        help="Attributes aren't specified on first line in csv data file.")

    parser.add_argument("-t", "--target", nargs="?", type=argparse.FileType('w'), default=sys.stdout, help="Name of target file.")
    parser.add_argument("-ts", "--target_separator",
                        help="Separator whitch will be used in target file. Default is ','.")
    parser.add_argument("-ta", "--target_attributes", help="Target file (new) attributes. Used for scaling.")
    parser.add_argument("-to", "--target_objects", help="Target file (new) objects. Only for CXT format.")
    parser.add_argument("-rn", "--relation_name", help="New name of relation.")
    parser.add_argument("-cls", "--classes", help="Classes seperated by commas - for C4.5 convert.")
    parser.add_argument("-sf", "--source_format", help="Format of source file, must to be specified when source is standart input (stdin)")
    parser.add_argument("-tf", "--target_format", help="Format of target file, must to be specified when target is standart output (stdout)")

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
    convertor.read_info()
    convertor.convert()
