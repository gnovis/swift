class SwiftException(Exception):
    def __init__(self, header, message, description):
        self._message = message
        self._description = description
        self._header = "Swift Error: {}".format(header)

    @property
    def message(self):
        return self._message

    @property
    def description(self):
        return self._description

    @property
    def header(self):
        return self._header

    def __str__(self):
        return "{}\nMessage: {}\nDescription: {}".format(self.header, self.message, self.description)


class SwiftParseException(SwiftException):
    def __init__(self, header, line, lineno, message):
        super().__init__(header, "Syntax Error in line {}: {}".format(lineno, line), message)
