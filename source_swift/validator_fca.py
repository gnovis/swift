import os
from source_swift.constants_fca import (FileType, RunParams)


class ParamValidator:
    suffixes = (FileType.ARFF, FileType.CSV, FileType.CXT, FileType.DAT, FileType.DATA)
    params_filter = {'.arff.cxt': [[], [RunParams.TARGET_ATTRS, RunParams.TARGET_OBJECTS]],
                     '.arff.dat': [[], [RunParams.TARGET_ATTRS]],
                     '.arff.data': [[], [RunParams.CLASSES]],
                     '.csv.arff': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.cxt': [[], [RunParams.TARGET_ATTRS, RunParams.TARGET_OBJECTS]],
                     '.csv.dat': [[], [RunParams.TARGET_ATTRS]],
                     '.csv.data': [[RunParams.SOURCE_ATTRS], [RunParams.CLASSES]],
                     '.cxt.data': [[], [RunParams.CLASSES]],
                     '.dat.arff': [[], [RunParams.TARGET_ATTRS]],
                     '.dat.csv': [[], [RunParams.TARGET_ATTRS]],
                     '.dat.cxt': [[], [RunParams.TARGET_ATTRS, RunParams.TARGET_OBJECTS]],
                     '.dat.data': [[], [RunParams.TARGET_ATTRS, RunParams.CLASSES]],
                     '.data.dat': [[], [RunParams.TARGET_ATTRS]],
                     '.data.cxt': [[], [RunParams.TARGET_ATTRS, RunParams.TARGET_OBJECTS]]}

    SOURCE_PARAMS = 0
    TARGET_PARAMS = 1

    def __init__(self, source, target, source_params, target_params):
        self._errors = []
        self._source_params = source_params
        self._target_params = target_params
        self._source_suff = ''
        self._target_suff = ''
        if source and target:
            self._source_suff = self._get_file_suff(source)
            self._target_suff = self._get_file_suff(target)
            self._validate()
        else:
            self._errors.append("Source and target file path must be always set if want convert.")

    @property
    def errors(self):
        return self._errors.copy()

    def _validate(self):
        if (self._source_suff not in
            self.suffixes) or (self._target_suff not in
                               self.suffixes):
            self._errors.append("Invalid format of source or target file.")

        key = self._source_suff + self._target_suff
        if key in self.params_filter:
            oblig_source = self.params_filter[key][self.SOURCE_PARAMS]
            oblig_target = self.params_filter[key][self.TARGET_PARAMS]

            def get_error(param):
                return ("In conversion " + self._source_suff.upper() + " to " +
                        self._target_suff.upper() + " must be set '" + param + "' parameter.")

            def validate_params(input_params, oblig_params):
                for p in oblig_params:
                    if p not in input_params:
                        self._errors.append(get_error(p))

            validate_params(self._source_params, oblig_source)
            validate_params(self._target_params, oblig_target)

    def _get_file_suff(self, path):
        return os.path.splitext(path)[1]
