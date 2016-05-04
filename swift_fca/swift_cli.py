from __future__ import print_function
import argparse
import sys
import traceback
import os
from .swift_core.managers_fca import Convertor, Browser, Printer, ManagerFca
from .swift_core.constants_fca import RunParams, FileType, App
from .swift_core.errors_fca import SwiftError, ErrorMessage, ErrorCode, ArgError
from .swift_core.validator_fca import ConvertValidator

SOURCE = 0
TARGET = 1
OTHERS = 2
ADDITIONAL_ACTION_ARG = 3


class SwiftFileType(argparse.FileType):
    F_NAME = 0
    EXT = 1

    # carefull, this is static variable
    FILE_NAME = None

    def __call__(self, string):
        if SwiftFileType.FILE_NAME == string:
            e = ArgError(message=ErrorMessage.SAME_ST_NAME_ERROR)
            print(e, file=sys.stderr)
            sys.exit(e.ident)
        if SwiftFileType.FILE_NAME is None:
            SwiftFileType.FILE_NAME = string
        # if an input file name has .names extension,
        # then extension is renamed to .data
        parts = os.path.splitext(string)
        ext = parts[self.EXT]
        fname = parts[self.F_NAME]
        if ext == FileType.NAMES_EXT:
            string = "{}{}".format(fname, FileType.DATA_EXT)

        return super().__call__(string)


def convert(*args):
    validator = ConvertValidator(args[SOURCE][RunParams.SOURCE].name,
                                 args[TARGET][RunParams.SOURCE].name,
                                 args[SOURCE], args[TARGET])
    warnings = validator.warnings
    if len(warnings) > 0:
        raise ArgError(message=ErrorMessage.MISSING_ARGS_ERROR + "\n" + "\n".join(warnings))
    convertor = Convertor(args[SOURCE], args[TARGET], **(args[OTHERS]))
    convertor.read_info()
    convertor.convert()


def preview(*args):
    def get_line_format(line):
        max_len = len(max(line, key=len))
        return " ".join(["{:" + str(max_len) + "}"] * (len(header)))

    def disp_line(line, index):
        print(get_line_format(line).format(*line))

    line_count = 20
    if type(args[ADDITIONAL_ACTION_ARG]) is str:
        try:
            parsed_num = int(args[ADDITIONAL_ACTION_ARG])
            line_count = parsed_num
        except ValueError:
            pass

    browser = Browser(args[SOURCE], **(args[OTHERS]))
    browser.read_info()
    header = browser.get_header()
    formated_header = get_line_format(header).format(*header)

    print(formated_header)
    browser.get_display_data(line_count, print_func=disp_line)


def export(*args):
    printer = Printer(args[SOURCE], **(args[OTHERS]))
    printer.read_info()
    printer.print_info(args[TARGET][RunParams.TARGET])


def get_args():
    CONVERT = 'convert'
    PREVIEW = 'preview'
    EXPORT = 'export'

    ACTIONS = {CONVERT: convert, PREVIEW: preview, EXPORT: export}

    SOURCE_ARGS = {"source": RunParams.SOURCE,
                   "source_format": RunParams.FORMAT,
                   "source_separator": RunParams.SOURCE_SEP,
                   "target_attributes": RunParams.SOURCE_ATTRS,
                   "source_no_header": RunParams.NFL,
                   "classes": RunParams.CLASSES,
                   "missing_value": RunParams.NONE_VALUE,
                   "source_cls_separator": RunParams.CLS_SEPARATOR}
    TARGET_ARGS = {"target": RunParams.TARGET,
                   "target_format": RunParams.FORMAT,
                   "target_separator": RunParams.TARGET_SEP,
                   "objects": RunParams.TARGET_OBJECTS,
                   "name": RunParams.RELATION_NAME,
                   "target_no_header": RunParams.NFL,
                   "target_cls_separator": RunParams.CLS_SEPARATOR}
    OTHER_ARGS = {"info": RunParams.SOURCE_INFO,
                  "skipped_lines": RunParams.SKIPPED_LINES,
                  "skip_errors": RunParams.SKIP_ERRORS}

    USAGE = """swift-cli.py [source]
                    [-h] [-ss source_separator] [-ta target_attributesbutes] [-i]
                    [-mv missing_value] [-snh] [-tnh] [-t [target]]
                    [-ts target_attributeset_separator] [-to target_objects] [-n name]
                    [-cls classes] [-sf {csv,arff,dat,data,cxt,dtl}]
                    [-tf {csv,arff,dat,data,cxt,dtl}] [-c [rows_count]] [-p [rows_count]]
                    [-sl skipped_lines] [-se] [-scs source_cls_separatorarator]
                    [-tcs target_cls_separator]"""

    parser = argparse.ArgumentParser(prog=App.NAME, description=App.DESCRIPTION, usage=USAGE)

    parser.add_argument("source", nargs="?", type=SwiftFileType('r'), default=sys.stdin,
                        help="Name of the source file. If the source is omitted or if it equals to '-', the program reads the input from the stdin.")
    parser.add_argument("-ss", "--source_separator",
                        help="Separator which is used in source file. Default is ','.")
    parser.add_argument("-ta", "--target_attributes", help="Attributes Formula used for filtering, reordering and converting attributes.")
    parser.add_argument("-i", "--info", action='store_true', help="Print information about source file data.")
    parser.add_argument("-mv", "--missing_value", help="Character which is used in data as value for non-specified attribute.")
    parser.add_argument("-snh", "--source_no_header",
                        action='store_false',
                        help="Attributes aren't specified on first line in csv data file.")

    parser.add_argument("-tnh", "--target_no_header",
                        action='store_false',
                        help="Attributes wont't be specified on first line in csv data file.")

    parser.add_argument("-t", "--target", nargs="?", type=SwiftFileType('w'), default=sys.stdout,
                        help="Name of the target file. If the --target is omitted or if it equals to '-', the program writes the output to the stdout.")

    parser.add_argument("-ts", "--target_separator",
                        help="Separator which will be used in target file. Default is ','.")
    parser.add_argument("-o", "--objects", help="Target file (new) objects. Only for CXT format.")
    parser.add_argument("-n", "--name", help="New name of relation.")
    parser.add_argument("-cls", "--classes", help="""Intervals (e.g 5-8) or keys, seperated by commas.
                        For determine, which attribute will be used as class. Compulsory for coversion: -> C4.5 and -> DTL.""")
    parser.add_argument("-sf", "--source_format", type=str.lower, choices=FileType.ALL_REPR_NO_NAMES,
                        help="Format of source file, must to be specified when source is standart input (stdin)")
    parser.add_argument("-tf", "--target_format", type=str.lower, choices=FileType.ALL_REPR_NO_NAMES,
                        help="Format of target file, must to be specified when target is standart output (stdout)")
    parser.add_argument("-{}".format(CONVERT[0]), "--{}".format(CONVERT), nargs='?', default=False, const=True,
                        help="Source file will be converted to target file, this is default option.")
    parser.add_argument("-{}".format(PREVIEW[0]), "--{}".format(PREVIEW), nargs='?', default=False, const=True,
                        help="Desired count of lines from source file will be displayed.")
    parser.add_argument("-sl", "--skipped_lines", help="Intervals of source line indices, which will be skipped in any operation.")
    parser.add_argument("-se", "--skip_errors", action="store_true", help="Skip broken lines, which cause an errors.")
    parser.add_argument("-scs", "--source_cls_separator", help="Separator which separates attributes and classes in source (will be read) C4.5 file format.")
    parser.add_argument("-tcs", "--target_cls_separator", help="Separator which separates attributes and classes in target (will be written) C4.5 file format.")

    args = parser.parse_args()

    source_args = {}
    target_args = {}
    other_args = {}
    action = ACTIONS[CONVERT]
    action_arg = None

    for key, val in vars(args).items():
        if val is not None:
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
                if val:
                    action = ACTIONS[key]
                    action_arg = val

    # this piece of code is for universal using -i --info
    file_extension = None
    try:
        file_extension = ManagerFca.get_extension(target_args[RunParams.SOURCE].name, target_args)
    except ArgError:
        pass  # target file is stdout
    if not file_extension and (RunParams.SOURCE_INFO in other_args):
        if other_args[RunParams.SOURCE_INFO]:
            action = ACTIONS[EXPORT]

    return action, source_args, target_args, other_args, action_arg


def main():
    action, source_args, target_args, other_args, action_arg = get_args()
    try:
        action(source_args, target_args, other_args, action_arg)
    except SwiftError as e:
        print(e, file=sys.stderr)
        sys.exit(e.ident)
    except KeyboardInterrupt:
        sys.exit(ErrorCode.keyboard_interrupt)
    except BrokenPipeError:  # NOQA
        sys.exit(ErrorCode.broken_pipe)
    except:
        msg = ErrorMessage.UNKNOWN_ERROR + traceback.format_exc()
        print(msg, file=sys.stderr)
        sys.exit(ErrorCode.unknown)
