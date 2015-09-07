"""Main file of swift - FCA data converter"""

import argparse
import sys
from .swift_core.managers_fca import Convertor, Browser, Printer
from .swift_core.constants_fca import RunParams
from .swift_core.exceptions_fca import SwiftException


SOURCE = 0
TARGET = 1
OTHERS = 2


def convert(*args):
    convertor = Convertor(args[SOURCE], args[TARGET], **(args[OTHERS]))
    convertor.read_info()
    convertor.convert()


def browse(*args):
    def get_line_count(count):
        try:
            command = input('Enter the nubmer of rows (defualt=20) or (q/quit) for exit: ')
            if command == 'q' or command == 'quit':
                return None
            count = int(command)
        except ValueError:
            pass
        return count

    browser = Browser(**args[SOURCE])
    browser.read_info()
    header = browser.get_header()
    line_format = " ".join(["{:10}"] * (len(header) + 1))

    count = get_line_count(20)
    print(line_format.format("", *header))
    print()

    index = 0
    while True:
        if count is None:
            break
        lines = browser.get_display_data(count)
        if not lines and count != 0:
            print("End of file.")
            break
        for line in lines:
            print(line_format.format(str(index), *line))
            index += 1
        count = get_line_count(count)
    browser.close_file()


def export(*args):
    printer = Printer(args[SOURCE], **(args[OTHERS]))
    printer.read_info()
    printer.print_info(args[TARGET][RunParams.TARGET])


def get_args():
    CONVERT = 'convert'
    BROWSE = 'browse'
    EXPORT = 'export'

    ACTIONS = {CONVERT: convert, BROWSE: browse, EXPORT: export}

    SOURCE_ARGS = {"source": RunParams.SOURCE,
                   "source_format": RunParams.FORMAT,
                   "source_separator": RunParams.SOURCE_SEP,
                   "source_attributes": RunParams.SOURCE_ATTRS,
                   "no_first_line": RunParams.NFL,
                   "none_value": RunParams.NONE_VALUE}
    TARGET_ARGS = {"target": RunParams.TARGET,
                   "target_format": RunParams.FORMAT,
                   "target_separator": RunParams.TARGET_SEP,
                   "target_objects": RunParams.TARGET_OBJECTS,
                   "relation_name": RunParams.RELATION_NAME,
                   "classes": RunParams.CLASSES}
    OTHER_ARGS = {"source_info": RunParams.SOURCE_INFO,
                  "line_count": RunParams.LINE_COUNT}

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--source", nargs="?", type=argparse.FileType('r'), default=sys.stdin, help="Name of source file.")
    parser.add_argument("-ss", "--source_separator",
                        help="Separator which is used in source file. Default is ','.")
    parser.add_argument("-sa", "--source_attributes", help="Source file (old) attributes. Used as additional informations.")
    parser.add_argument("-si", "--source_info", action='store_true', help="Print information about source file data.")
    parser.add_argument("-nv", "--none_value", help="Character which is used in data as value for non-specified attribute.")
    parser.add_argument("-nfl", "--no_first_line",
                        action='store_true',
                        help="Attributes aren't specified on first line in csv data file.")

    parser.add_argument("-t", "--target", nargs="?", type=argparse.FileType('w'), default=sys.stdout, help="Name of target file.")
    parser.add_argument("-ts", "--target_separator",
                        help="Separator which will be used in target file. Default is ','.")
    parser.add_argument("-to", "--target_objects", help="Target file (new) objects. Only for CXT format.")
    parser.add_argument("-rn", "--relation_name", help="New name of relation.")
    parser.add_argument("-cls", "--classes", help="Classes seperated by commas - for C4.5 convert.")
    parser.add_argument("-sf", "--source_format", help="Format of source file, must to be specified when source is standart input (stdin)")
    parser.add_argument("-tf", "--target_format", help="Format of target file, must to be specified when target is standart output (stdout)")
    parser.add_argument("-{}".format(CONVERT[0]), "--{}".format(CONVERT), action='store_true')
    parser.add_argument("-{}".format(BROWSE[0]), "--{}".format(BROWSE), action='store_true')
    parser.add_argument("-{}".format(EXPORT[0]), "--{}".format(EXPORT), action='store_true')
    parser.add_argument("-lc", "--line_count", type=float)

    args = parser.parse_args()

    source_args = {}
    target_args = {}
    other_args = {}
    action = ACTIONS[CONVERT]

    for key, val in vars(args).items():
        if val:
            if key in SOURCE_ARGS:
                new_key = SOURCE_ARGS[key]
                source_args[new_key] = val
            elif key in TARGET_ARGS:
                new_key = TARGET_ARGS[key]
                target_args[new_key] = val
            elif key in OTHER_ARGS:
                new_key = OTHER_ARGS[key]
                other_args[new_key] = val
            else:
                action = ACTIONS[key]

    action(source_args, target_args, other_args)


def main():
    try:
        get_args()
    except SwiftException as e:
        print(e)
