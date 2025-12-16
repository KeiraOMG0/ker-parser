# ker/lexer.py
import re
from .errors import LexerError

class Token:
    IDENT, STRING, NUMBER, TRUE, FALSE, NULL, \
    EQUALS, LBRACE, RBRACE, LBRACKET, RBRACKET, \
    COMMA, COLON, COMMENT, EOF = range(15)

    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value}, {self.line}:{self.col})"


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = text[0] if text else None

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        nxt = self.pos + 1
        return self.text[nxt] if nxt < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char in ' \t\r':
            self.advance()

    def lex_string(self):
        start_line, start_col = self.line, self.col
        self.advance()  # skip opening "
        s = []
        while self.current_char and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if not self.current_char:
                    break
            s.append(self.current_char)
            self.advance()
        if self.current_char != '"':
            raise LexerError(f"Unterminated string at {start_line}:{start_col}")
        self.advance()
        return Token(Token.STRING, ''.join(s), start_line, start_col)

    def lex_number(self):
        start_line, start_col = self.line, self.col
        num = ''
        if self.current_char == '-':
            num += '-'
            self.advance()
        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            num += self.current_char
            self.advance()
        return Token(Token.NUMBER, num, start_line, start_col)

    def lex_ident_or_keyword(self):
        start_line, start_col = self.line, self.col
        s = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            s += self.current_char
            self.advance()
        kw = s.lower()
        if kw == "true":
            return Token(Token.TRUE, s, start_line, start_col)
        if kw == "false":
            return Token(Token.FALSE, s, start_line, start_col)
        if kw == "null":
            return Token(Token.NULL, s, start_line, start_col)
        return Token(Token.IDENT, s, start_line, start_col)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char in ' \t\r':
                self.skip_whitespace()
                continue
            if self.current_char == '\n':
                self.advance()
                continue
            if self.current_char == '#':
                start_line, start_col = self.line, self.col
                self.advance()
                c = ''
                while self.current_char and self.current_char != '\n':
                    c += self.current_char
                    self.advance()
                return Token(Token.COMMENT, c.strip(), start_line, start_col)
            if self.current_char.isalpha() or self.current_char == '_':
                return self.lex_ident_or_keyword()
            if self.current_char.isdigit() or (self.current_char == '-' and self.peek() and self.peek().isdigit()):
                return self.lex_number()
            if self.current_char == '"':
                return self.lex_string()
            mapping = {
                '=': Token.EQUALS,
                '{': Token.LBRACE,
                '}': Token.RBRACE,
                '[': Token.LBRACKET,
                ']': Token.RBRACKET,
                ',': Token.COMMA,
                ':': Token.COLON,
            }
            if self.current_char in mapping:
                tok = Token(mapping[self.current_char], self.current_char, self.line, self.col)
                self.advance()
                return tok
            raise LexerError(f"Unexpected char '{self.current_char}' at {self.line}:{self.col}")
        return Token(Token.EOF, None, self.line, self.col)
