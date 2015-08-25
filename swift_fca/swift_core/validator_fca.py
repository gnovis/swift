import os
from .constants_fca import (FileType, RunParams)


class ParamValidator:
    SUFFIXES = (FileType.ARFF, FileType.CSV, FileType.CXT, FileType.DAT, FileType.DATA)
    PARAMS_FILTER = {'.arff.cxt': [[RunParams.SOURCE_ATTRS], [RunParams.TARGET_OBJECTS]],
                     '.arff.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.arff.data': [[], [RunParams.CLASSES]],
                     '.csv.arff': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.cxt': [[RunParams.SOURCE_ATTRS], [RunParams.TARGET_OBJECTS]],
                     '.csv.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.data': [[RunParams.SOURCE_ATTRS], [RunParams.CLASSES]],
                     '.cxt.data': [[], [RunParams.CLASSES]],
                     '.dat.arff': [[RunParams.SOURCE_ATTRS], []],
                     '.dat.csv': [[RunParams.SOURCE_ATTRS], []],
                     '.dat.cxt': [[RunParams.SOURCE_ATTRS], [RunParams.TARGET_OBJECTS]],
                     '.dat.data': [[RunParams.SOURCE_ATTRS], [RunParams.CLASSES]],
                     '.data.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.data.cxt': [[RunParams.SOURCE_ATTRS], [RunParams.TARGET_OBJECTS]]}

    SOURCE_ARGS_DISPLAY = {RunParams.SOURCE: "Source file",
                           RunParams.SOURCE_SEP: "Source separator",
                           RunParams.SOURCE_ATTRS: "Source attributes",
                           RunParams.NFL: "Attributes on first line"}
    TARGET_ARGS_DISPLAY = {RunParams.TARGET: "Target file",
                           RunParams.TARGET_SEP: "Target separator",
                           RunParams.TARGET_OBJECTS: "Target objects",
                           RunParams.RELATION_NAME: "Relation name",
                           RunParams.CLASSES: "Classes"}

    SOURCE_PARAMS = 0
    TARGET_PARAMS = 1

    def __init__(self, source, target, source_params, target_params):
        self._warnings = []
        self._source_params = source_params
        self._target_params = target_params
        self._source_suff = ''
        self._target_suff = ''

        if source and target:
            if source == target:
                self._warnings.append("Isn't possible to read and write to the same file, target and source can't be same.")
                return
            self._source_suff = self._get_file_suff(source)
            self._target_suff = self._get_file_suff(target)
            self._validate()
        else:
            self._warnings.append("Source File and Target File are required for conversion.")

    @property
    def warnings(self):
        return self._warnings.copy()

    def _validate(self):
        if (self._source_suff not in
            self.SUFFIXES) or (self._target_suff not in
                               self.SUFFIXES):
            self._warnings.append("Invalid format of source or target file.")

        key = self._source_suff + self._target_suff
        if key in self.PARAMS_FILTER:
            oblig_source = self.PARAMS_FILTER[key][self.SOURCE_PARAMS]
            oblig_target = self.PARAMS_FILTER[key][self.TARGET_PARAMS]

            def get_error(param):
                return ("In conversion " + self._source_suff.upper() + " to " +
                        self._target_suff.upper() + " must be set '" + param + "' argument.")

            def validate_params(input_params, oblig_params, args_display):
                for p in oblig_params:
                    if p not in input_params:
                        self._warnings.append(get_error(args_display[p]))

            validate_params(self._source_params, oblig_source, self.SOURCE_ARGS_DISPLAY)
            validate_params(self._target_params, oblig_target, self.TARGET_ARGS_DISPLAY)

    def _get_file_suff(self, path):
        return os.path.splitext(path)[1]
