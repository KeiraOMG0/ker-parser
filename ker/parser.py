# ker/parser.py
import re
from .lexer import Lexer, Token
from .errors import ParserError

class Node:
    def __init__(self, value=None, src_pos=None):
        self.value = value
        self.children = None
        self.elements = None
        self.comments_before = []
        self.comment_inline = None
        self.src_pos = src_pos


class Parser:
    def __init__(self, text: str):
        self.lexer = Lexer(text)
        self.current = self.lexer.get_next_token()
        self.pending_comments = []

    def advance(self):
        self.current = self.lexer.get_next_token()

    def parse(self):
        root = Node()
        root.children = {}
        while self.current.type != Token.EOF:
            if self.current.type == Token.COMMENT:
                self.pending_comments.append(self.current.value)
                self.advance()
                continue
            if self.current.type != Token.IDENT:
                raise ParserError(f"Expected identifier at {self.current.line}:{self.current.col}")
            key = self.current.value
            self.advance()
            if self.current.type == Token.LBRACE:
                node = Node(src_pos=(self.current.line, self.current.col))
                node.children = {}
                self.advance()
                self.parse_block(node)
            else:
                if self.current.type != Token.EQUALS:
                    raise ParserError("Expected '='")
                self.advance()
                node = self.parse_value()
            if self.pending_comments:
                node.comments_before = self.pending_comments
                self.pending_comments = []
            root.children[key] = node
        return root

    def parse_block(self, node):
        while True:
            if self.current.type == Token.RBRACE:
                self.advance()
                return
            if self.current.type == Token.COMMENT:
                self.pending_comments.append(self.current.value)
                self.advance()
                continue
            if self.current.type != Token.IDENT:
                raise ParserError("Expected key in block")
            key = self.current.value
            self.advance()
            if self.current.type == Token.LBRACE:
                child = Node(src_pos=(self.current.line, self.current.col))
                child.children = {}
                self.advance()
                self.parse_block(child)
            else:
                if self.current.type != Token.EQUALS:
                    raise ParserError("Expected '='")
                self.advance()
                child = self.parse_value()
            if self.pending_comments:
                child.comments_before = self.pending_comments
                self.pending_comments = []
            node.children[key] = child

    def parse_value(self):
        tok = self.current
        if tok.type == Token.STRING:
            self.advance()
            return Node(tok.value, (tok.line, tok.col))
        if tok.type == Token.NUMBER:
            self.advance()
            v = int(tok.value) if re.fullmatch(r'-?\d+', tok.value) else float(tok.value)
            return Node(v, (tok.line, tok.col))
        if tok.type in (Token.TRUE, Token.FALSE):
            self.advance()
            return Node(tok.value.lower() == "true", (tok.line, tok.col))
        if tok.type == Token.NULL:
            self.advance()
            return Node(None, (tok.line, tok.col))
        if tok.type == Token.LBRACKET:
            self.advance()
            node = Node(src_pos=(tok.line, tok.col))
            node.elements = []
            while self.current.type != Token.RBRACKET:
                node.elements.append(self.parse_value())
                if self.current.type == Token.COMMA:
                    self.advance()
            self.advance()
            return node
        if tok.type == Token.LBRACE:
            self.advance()
            node = Node(src_pos=(tok.line, tok.col))
            node.children = {}
            self.parse_block(node)
            return node
        raise ParserError(f"Unexpected token {tok}")
