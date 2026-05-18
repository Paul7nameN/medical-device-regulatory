class ParseError(Exception):
    pass


class InvalidTimestampError(ParseError):
    pass


class UnknownLogTypeError(ParseError):
    pass
