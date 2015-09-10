"""Main file of swift - FCA data converter"""

import argparse
import sys
import traceback
from .swift_core.managers_fca import Convertor, Browser, Printer
from .swift_core.constants_fca import RunParams, ErrorMessage, FileType
from .swift_core.exceptions_fca import SwiftException
from .swift_core.validator_fca import ConvertValidator

SOURCE = 0
TARGET = 1
OTHERS = 2


def convert(*args):
    validator = ConvertValidator(args[SOURCE][RunParams.SOURCE].name,
                                 args[TARGET][RunParams.SOURCE].name,
                                 args[SOURCE], args[TARGET])
    warnings = validator.warnings
    if len(warnings) > 0:
        raise SwiftException("Arguments",
                             ErrorMessage.MISSING_ARGS_ERROR,
                             "\n".join(warnings))
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

    def display_lines(lines, i):
        index = i
        for line in lines:
            print(line_format.format(str(index), *line))
            index += 1
        return index

    browser = Browser(args[SOURCE], **(args[OTHERS]))
    browser.read_info()
    header = browser.get_header()
    line_format = " ".join(["{:10}"] * (len(header) + 1))
    formated_header = line_format.format("i", *header)

    if browser.source_from_stdin:
        print("Max {} lines displayed. Use {} argument for changing it.\n".format(browser.line_count, RunParams.LINE_COUNT))
        print(formated_header)
        lines = browser.get_display_data(browser.line_count)
        display_lines(lines, 0)
        return

    count = get_line_count(20)
    index = 0
    print(formated_header)
    while True:
        if count is None:
            break
        lines = browser.get_display_data(count)
        if not lines and count != 0:
            print("End of file.")
            break
        index = display_lines(lines, index)
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
                  "line_count": RunParams.LINE_COUNT,
                  "skipped_lines": RunParams.SKIPPED_LINES}

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--source", nargs="?", type=argparse.FileType('r'), default=sys.stdin, help="Name of source file.")
    parser.add_argument("-ss", "--source_separator",
                        help="Separator which is used in source file. Default is ','.")
    parser.add_argument("-sa", "--source_attributes", help="Attributes Formula used for filtering, reordering and converting attributes.")
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
    parser.add_argument("-sf", "--source_format", type=str.lower, choices=list(map(lambda val: val[1:], FileType.ALL)),
                        help="Format of source file, must to be specified when source is standart input (stdin)")
    parser.add_argument("-tf", "--target_format", type=str.lower, choices=list(map(lambda val: val[1:], FileType.ALL)),
                        help="Format of target file, must to be specified when target is standart output (stdout)")
    parser.add_argument("-{}".format(CONVERT[0]), "--{}".format(CONVERT), action='store_true',
                        help="Source file will be converted to target file, this is default option.")
    parser.add_argument("-{}".format(BROWSE[0]), "--{}".format(BROWSE), action='store_true',
                        help="Desired count of lines from source file will be displayed.")
    parser.add_argument("-{}".format(EXPORT[0]), "--{}".format(EXPORT), action='store_true',
                        help="Desired count of lines from source file will be scanned and informations about data will be exported to target file.")
    parser.add_argument("-lc", "--line_count", type=float, help="Count of lines which will be processed in any action.")
    parser.add_argument("-sl", "--skipped_lines", help="Indexes of lines which will be skipped in any operation.")

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

    return action, source_args, target_args, other_args


def main():
    action, source_args, target_args, other_args = get_args()
    try:
        action(source_args, target_args, other_args)
    except SwiftException as e:
        print(e)
    except:
        msg = ErrorMessage.UNKNOWN_ERROR + traceback.format_exc()
        print(msg)