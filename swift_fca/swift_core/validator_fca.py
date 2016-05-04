from .constants_fca import RunParams
from .managers_fca import ManagerFca
from .errors_fca import ErrorMessage


class ConvertValidator:
    PARAMS_FILTER = {'.arff.cxt': [[RunParams.SOURCE_ATTRS], []],
                     '.arff.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.arff.data': [[RunParams.CLASSES], []],
                     '.arff.dtl': [[RunParams.SOURCE_ATTRS, RunParams.CLASSES], []],
                     '.csv.arff': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.cxt': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.csv.data': [[RunParams.SOURCE_ATTRS, RunParams.CLASSES], []],
                     '.csv.dtl': [[RunParams.SOURCE_ATTRS, RunParams.CLASSES], []],
                     '.cxt.data': [[RunParams.CLASSES], []],
                     '.cxt.dtl': [[RunParams.CLASSES], []],
                     '.dtl.dtl': [[RunParams.SOURCE_ATTRS, RunParams.CLASSES], []],
                     '.dtl.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.dtl.cxt': [[RunParams.SOURCE_ATTRS], []],
                     '.dtl.data': [[RunParams.CLASSES], []],
                     '.dat.data': [[RunParams.CLASSES], []],
                     '.dat.dtl': [[RunParams.CLASSES], []],
                     '.data.dat': [[RunParams.SOURCE_ATTRS], []],
                     '.data.cxt': [[RunParams.SOURCE_ATTRS], []],
                     '.data.data': [[RunParams.CLASSES], []],
                     '.data.dtl': [[RunParams.SOURCE_ATTRS, RunParams.CLASSES], []]}

    SOURCE_ARGS_DISPLAY = {RunParams.SOURCE: "Source file",
                           RunParams.SOURCE_SEP: "Source separator",
                           RunParams.SOURCE_ATTRS: "Target attributes",
                           RunParams.NFL: "Header Line",
                           RunParams.CLASSES: "Classes"}
    TARGET_ARGS_DISPLAY = {RunParams.TARGET: "Target file",
                           RunParams.TARGET_SEP: "Target separator",
                           RunParams.TARGET_OBJECTS: "Target objects",
                           RunParams.RELATION_NAME: "Relation name"}

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
                self._warnings.append(ErrorMessage.SAME_ST_NAME_ERROR)
                return
            self._source_suff = ManagerFca.get_extension(source, source_params)
            self._target_suff = ManagerFca.get_extension(target, target_params)
            self._validate()
        else:
            self._warnings.append("The source file and the target file are required for a conversion.")

    @property
    def warnings(self):
        return self._warnings.copy()

    def _validate(self):
        key = self._source_suff + self._target_suff
        if key in self.PARAMS_FILTER:
            oblig_source = self.PARAMS_FILTER[key][self.SOURCE_PARAMS]
            oblig_target = self.PARAMS_FILTER[key][self.TARGET_PARAMS]

            def get_error(param):
                return "In a conversion {} to {} the '{}' argument must be set.".format(
                    self._source_suff.upper(), self._target_suff.upper(), param)

            def validate_params(input_params, oblig_params, args_display):
                for p in oblig_params:
                    if p not in input_params:
                        self._warnings.append(get_error(args_display[p]))

            validate_params(self._source_params, oblig_source, self.SOURCE_ARGS_DISPLAY)
            validate_params(self._target_params, oblig_target, self.TARGET_ARGS_DISPLAY)
