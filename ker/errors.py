class KerError(Exception):
    """Generic top-level error for public API."""
    pass

class LexerError(KerError):
    pass

class ParserError(KerError):
    pass
