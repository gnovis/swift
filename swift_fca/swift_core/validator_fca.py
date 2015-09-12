import os
import sys
from .constants_fca import RunParams
from .errors_fca import ArgError


class ConvertValidator:
    PARAMS_FILTER = {'.arff.cxt': [[RunParams.SOURCE_ATTRS], []],
                     '.arff.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.arff.data': [[], [RunParams.CLASSES]],
                     '.csv.arff': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.cxt': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.data': [[RunParams.SOURCE_ATTRS], [RunParams.CLASSES]],
                     '.cxt.data': [[], [RunParams.CLASSES]],
                     '.dat.data': [[], [RunParams.CLASSES]],
                     '.data.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.data.cxt': [[RunParams.SOURCE_ATTRS], []]}

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
            self._source_suff = self._get_file_suff(source, source_params)
            self._target_suff = self._get_file_suff(target, target_params)
            self._validate()
        else:
            self._warnings.append("Source File and Target File are required for conversion.")

    @property
    def warnings(self):
        return self._warnings.copy()

    def _validate(self):
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

    def _get_file_suff(self, path, params):
        if path == sys.stdin.name or path == sys.stdout.name:
            try:
                return ".{}".format(params[RunParams.FORMAT])
            except KeyError:
                raise ArgError(RunParams.FORMAT)
        return os.path.splitext(path)[1]
