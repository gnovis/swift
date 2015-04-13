import os
from source.data_fca import (Data, DataCsv, DataArff, DataDat, DataCxt)


class Convertor:
    """Manage data conversion"""

    """class variables"""
    extensions = {'.csv': DataCsv,
                  '.arff': DataArff,
                  '.dat': DataDat,
                  '.cxt': DataCxt}

    def __init__(self, old, new, print_info=False):

        # suffixes of input files
        old_suff = os.path.splitext(old['source'])[1]
        new_suff = os.path.splitext(new['source'])[1]

        self._old_data = Convertor.extensions[old_suff](**old)
        self._new_data = Convertor.extensions[new_suff](**new)

        # get information from source data
        self._old_data.get_header_info()
        self._old_data.get_data_info()
        if print_info:
            self._old_data.print_info()

        # check if should scale
        self._scaling = False
        if (old_suff == '.csv' or
            old_suff == '.arff') and (new_suff == '.dat' or
                                      new_suff == '.cxt'):
            self._scaling = True
            self._new_data.parse_old_attrs_for_scale(self._old_data.str_attrs,
                                                     self._old_data.separator)
            self._new_data.parse_new_attrs_for_scale()

    def convert(self):
        """Call this method to convert data"""

        target_file = open(self._new_data.source, 'w')
        # write header part
        self._new_data.write_header(target_file, old_data=self._old_data)
        with open(self._old_data.source, 'r') as f:
            # skip header lines
            Data.skip_lines(self._old_data.index_data_start, f)
            for i, line in enumerate(f):
                prepared_line = self._old_data.prepare_line(line)
                if self._scaling:
                    self._new_data.write_data_scale(prepared_line,
                                                    target_file)
                else:
                    self._new_data.write_line(prepared_line,
                                              target_file)
        target_file.close()
