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
    def __init__(self, header, line, linei, message):
        super().__init__(header, "Syntax Error in line {}: {}".format(linei+1, line), message)


class SwiftLineException(SwiftException):
    def __init__(self, header, line, linei, message, attr="Unknown", attri=-1):
        if attri == -1:
            attri = "Unknown"
        else:
            attri += 1
        super().__init__(header, "Invalid value in attribute {}: {}, on line {}: {}".format(attri, attr, linei+1, line.strip()), message)


class SwiftAttributeException(SwiftException):
    def __init__(self, message):
        super().__init__("", message, "")
