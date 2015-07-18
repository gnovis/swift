import os
from source_swift.constants_fca import (FileType, RunParams)


class ParamValidator:
    suffixes = (FileType.ARFF, FileType.CSV, FileType.CXT, FileType.DAT, FileType.DATA)

    def __init__(self, source_params, target_params):
        self._errors = []
        self._source_params = source_params
        self._target_params = target_params
        self._source_suff = ''
        self._target_suff = ''
        if (RunParams.SOURCE in source_params) and (RunParams.TARGET in target_params):
            self._source_suff = self.get_file_suff(source_params[RunParams.SOURCE])
            self._target_suff = self.get_file_suff(source_params[RunParams.SOURCE])
        else:
            self._errors.append("Source and target file path must be always set.")

    @property
    def errors(self):
        return self._errors.copy()

    def validate(self):
        def validate_formats():
            if (self._source_suff not in
                self.suffixes) or (self._target_source not in
                                   self.suffixes):
                self._errors.append("Invalid format of source or target file.")

    def get_file_suff(self, path):
        return os.path.splitext(path)[1]
