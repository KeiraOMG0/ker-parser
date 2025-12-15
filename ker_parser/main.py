# main.py - .ker reference implementation (lexer, parser, JSON <-> .ker)
import re
import json
import sys
import argparse
from typing import Optional

# --- Token and Lexer ---

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
        names = ["IDENT","STRING","NUMBER","TRUE","FALSE","NULL",
                 "EQUALS","LBRACE","RBRACE","LBRACKET","RBRACKET",
                 "COMMA","COLON","COMMENT","EOF"]
        return f"Token({names[self.type]}, {self.value!r}, line={self.line}, col={self.col})"

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        """Advance one character, tracking line/col."""
        if self.current_char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def peek(self):
        if self.pos + 1 < len(self.text):
            return self.text[self.pos+1]
        return None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char in " \t\r":
            self.advance()

    def lex_number(self):
        """Lex JSON-style number (integer, float, exponent)."""
        start_line, start_col = self.line, self.col
        num_str = ''
        if self.current_char == '-':
            num_str += '-'
            self.advance()
            if self.current_char is None or not self.current_char.isdigit():
                raise LexerError(f"Bad number at {self.line}:{self.col}")
        while self.current_char and self.current_char.isdigit():
            num_str += self.current_char
            self.advance()
        if self.current_char == '.':
            num_str += '.'
            self.advance()
            if self.current_char is None or not self.current_char.isdigit():
                raise LexerError(f"Bad number at {self.line}:{self.col}")
            while self.current_char and self.current_char.isdigit():
                num_str += self.current_char
                self.advance()
        if self.current_char and self.current_char in 'eE':
            num_str += self.current_char
            self.advance()
            if self.current_char and self.current_char in '+-':
                num_str += self.current_char
                self.advance()
            if self.current_char is None or not self.current_char.isdigit():
                raise LexerError(f"Bad number at {self.line}:{self.col}")
            while self.current_char and self.current_char.isdigit():
                num_str += self.current_char
                self.advance()
        # Disallow leading zeros like JSON
        if re.match(r'-?0[0-9]', num_str):
            raise LexerError(f"Invalid number format '{num_str}' at {start_line}:{start_col}")
        return Token(Token.NUMBER, num_str, start_line, start_col)

    def lex_ident_or_keyword(self):
        """Lex identifiers and keywords (true/false/null)."""
        start_line, start_col = self.line, self.col
        ident = ''
        while self.current_char and re.match(r'[A-Za-z0-9_]', self.current_char):
            ident += self.current_char
            self.advance()
        if ident in ("true", "True"):
            return Token(Token.TRUE, ident, start_line, start_col)
        if ident in ("false", "False"):
            return Token(Token.FALSE, ident, start_line, start_col)
        if ident in ("null", "None"):
            return Token(Token.NULL, ident, start_line, start_col)
        return Token(Token.IDENT, ident, start_line, start_col)

    def lex_string(self):
        """Lex double-quoted string and decode escapes into actual characters."""
        start_line, start_col = self.line, self.col
        self.advance()  # skip opening quote
        s_chars = []
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char is None:
                    raise LexerError(f"Unterminated escape at {self.line}:{self.col}")
                esc = self.current_char
                if esc == 'n':
                    s_chars.append('\n')
                elif esc == 't':
                    s_chars.append('\t')
                elif esc == 'r':
                    s_chars.append('\r')
                elif esc == '"':
                    s_chars.append('"')
                elif esc == '\\':
                    s_chars.append('\\')
                elif esc == 'u':
                    hex_digits = ''
                    for _ in range(4):
                        self.advance()
                        if self.current_char is None or not re.match(r'[0-9A-Fa-f]', self.current_char):
                            raise LexerError(f"Bad unicode escape at {self.line}:{self.col}")
                        hex_digits += self.current_char
                    try:
                        codepoint = int(hex_digits, 16)
                        s_chars.append(chr(codepoint))
                    except ValueError:
                        raise LexerError(f"Bad unicode escape at {self.line}:{self.col}")
                else:
                    # Unknown escape: keep it literal (backslash + char)
                    s_chars.append('\\' + esc)
                self.advance()
            else:
                s_chars.append(self.current_char)
                self.advance()
        if self.current_char != '"':
            raise LexerError(f"Unterminated string starting at {start_line}:{start_col}")
        self.advance()  # skip closing quote
        return Token(Token.STRING, ''.join(s_chars), start_line, start_col)

    def get_next_token(self):
        """Return next token or EOF."""
        while self.current_char is not None:
            # Skip spaces/tabs/carriage returns
            if self.current_char in ' \t\r':
                self.skip_whitespace()
                continue
            # Skip newlines (advance line count)
            if self.current_char == '\n':
                self.advance()
                continue
            # Comments
            if self.current_char == '#':
                start_line, start_col = self.line, self.col
                self.advance()
                comm = ''
                while self.current_char is not None and self.current_char != '\n':
                    comm += self.current_char
                    self.advance()
                return Token(Token.COMMENT, comm.strip(), start_line, start_col)
            # Identifiers or keywords
            if self.current_char.isalpha() or self.current_char == '_':
                return self.lex_ident_or_keyword()
            # Numbers
            if self.current_char.isdigit() or (self.current_char == '-' and self.peek() and self.peek().isdigit()):
                return self.lex_number()
            # Strings
            if self.current_char == '"':
                return self.lex_string()
            # Punctuation
            if self.current_char == '=':
                tok = Token(Token.EQUALS, '=', self.line, self.col)
                self.advance()
                return tok
            if self.current_char == '{':
                tok = Token(Token.LBRACE, '{', self.line, self.col)
                self.advance()
                return tok
            if self.current_char == '}':
                tok = Token(Token.RBRACE, '}', self.line, self.col)
                self.advance()
                return tok
            if self.current_char == '[':
                tok = Token(Token.LBRACKET, '[', self.line, self.col)
                self.advance()
                return tok
            if self.current_char == ']':
                tok = Token(Token.RBRACKET, ']', self.line, self.col)
                self.advance()
                return tok
            if self.current_char == ',':
                tok = Token(Token.COMMA, ',', self.line, self.col)
                self.advance()
                return tok
            if self.current_char == ':':
                tok = Token(Token.COLON, ':', self.line, self.col)
                self.advance()
                return tok
            # Anything else is an error
            raise LexerError(f"Unexpected character '{self.current_char}' at {self.line}:{self.col}")
        return Token(Token.EOF, None, self.line, self.col)

# --- Parser / AST Node ---

class ParserError(Exception):
    pass

class Node:
    def __init__(self, key: Optional[str]=None, value=None, src_pos: Optional[tuple]=None):
        self.key = key              # e.g. "port"
        self.value = value          # literal value (str, int, bool, None) if leaf
        self.children: Optional[dict] = None        # dict of child Nodes (if object)
        self.elements: Optional[list] = None        # list of child Nodes (if array)
        self.comments_before: list = []   # list of comment strings before this node
        self.comment_inline: Optional[str] = None  # trailing comment string
        self.src_pos = src_pos      # (line,col) of key or value start
    def __repr__(self):
        children_keys = list(self.children.keys()) if self.children else []
        elem_count = len(self.elements) if self.elements else 0
        return (f"Node(key={self.key!r}, value={self.value!r}, "
                f"children={children_keys}, elements_len={elem_count}, "
                f"comments_before={self.comments_before}, comment_inline={self.comment_inline})")

class Parser:
    def __init__(self, text: str):
        # Lex entire input to tokens
        self.lexer = Lexer(text)
        self.tokens = []
        while True:
            tok = self.lexer.get_next_token()
            self.tokens.append(tok)
            if tok.type == Token.EOF:
                break
        self.pos = 0
        self.current = self.tokens[self.pos]
        self.pending_comments = []

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current = self.tokens[self.pos]
        return self.current

    def parse(self):
        """Parse top-level statements into root Node."""
        root = Node(key=None, value=None, src_pos=(1,1))
        root.children = {}
        while self.current.type != Token.EOF:
            # Handle leading comments
            if self.current.type == Token.COMMENT:
                self.pending_comments.append(self.current.value)
                self.advance()
                continue
            if self.current.type in (Token.IDENT, Token.STRING):
                node = self.parse_statement()
                # Attach accumulated comments before this node
                if self.pending_comments:
                    node.comments_before = self.pending_comments
                    self.pending_comments = []
                # Inline comment (same line)
                if self.current.type == Token.COMMENT and self.current.line == node.src_pos[0]:
                    node.comment_inline = self.current.value
                    self.advance()
                # Store in root
                if node.key in root.children:
                    print(f"Warning: duplicate key {node.key} at {node.src_pos}")
                root.children[node.key] = node
                continue
            if self.current.type == Token.COMMA:
                # tolerate stray commas/trailing commas at top-level
                self.advance()
                continue
            raise ParserError(f"Unexpected token {self.current} at top-level")
        return root

    def parse_statement(self):
        """Parse a single assignment or key-block."""
        if self.current.type in (Token.IDENT, Token.STRING):
            key_tok = self.current
            key = key_tok.value
            self.advance()
            # Key-block with colon:  key: { ... }
            if self.current.type == Token.COLON:
                self.advance()
                if self.current.type != Token.LBRACE:
                    raise ParserError(f"Expected '{{' after ':' at {self.current.line}:{self.current.col}")
                node = Node(key=key, src_pos=(key_tok.line, key_tok.col))
                node.children = {}
                self.advance()
                self.parse_block(node)
                return node
            # Assignment with '='
            elif self.current.type == Token.EQUALS:
                self.advance()
                # If next is block literal
                if self.current.type == Token.LBRACE:
                    node = Node(key=key, src_pos=(key_tok.line, key_tok.col))
                    node.children = {}
                    self.advance()
                    self.parse_block(node)
                    return node
                else:
                    # Parse value
                    val_node = self.parse_value()
                    node = Node(key=key, src_pos=(key_tok.line, key_tok.col))
                    # Copy structure if object/array
                    if val_node.children is not None:
                        node.children = val_node.children
                    if val_node.elements is not None:
                        node.elements = val_node.elements
                    node.value = val_node.value
                    return node
            # Implicit block without '=': key { ... }
            elif self.current.type == Token.LBRACE:
                node = Node(key=key, src_pos=(key_tok.line, key_tok.col))
                node.children = {}
                self.advance()
                self.parse_block(node)
                return node
            else:
                raise ParserError(f"Expected '=' or '{{' after key at {self.current.line}:{self.current.col}")
        else:
            raise ParserError(f"Expected key at {self.current.line}:{self.current.col}")

    def parse_block(self, node: Node):
        """Parse contents of a `{ ... }` block, filling node.children."""
        while True:
            if self.current.type == Token.COMMENT:
                self.pending_comments.append(self.current.value)
                self.advance()
                continue
            if self.current.type == Token.RBRACE:
                self.advance()
                break
            if self.current.type == Token.EOF:
                raise ParserError(f"Unclosed block starting at {node.src_pos}")
            if self.current.type in (Token.IDENT, Token.STRING):
                stmt = self.parse_statement()
                if self.pending_comments:
                    stmt.comments_before = self.pending_comments
                    self.pending_comments = []
                if self.current.type == Token.COMMENT and self.current.line == stmt.src_pos[0]:
                    stmt.comment_inline = self.current.value
                    self.advance()
                if stmt.key in node.children:
                    print(f"Warning: duplicate key {stmt.key} in block at {stmt.src_pos}")
                node.children[stmt.key] = stmt
                continue
            if self.current.type == Token.COMMA:
                self.advance()
                continue
            raise ParserError(f"Unexpected token {self.current} in block at {self.current.line}:{self.current.col}")
        return node

    def parse_value(self):
        """Parse a literal value: string, number, bool, null, array, or object."""
        # String
        if self.current.type == Token.STRING:
            tok = self.current
            val = tok.value
            node = Node(value=val, src_pos=(tok.line, tok.col))
            self.advance()
            return node
        # Number
        if self.current.type == Token.NUMBER:
            tok = self.current
            num_str = tok.value
            num_val = int(num_str) if re.match(r'-?\d+$', num_str) else float(num_str)
            node = Node(value=num_val, src_pos=(tok.line, tok.col))
            self.advance()
            return node
        # Boolean
        if self.current.type in (Token.TRUE, Token.FALSE):
            tok = self.current
            bool_val = tok.value.lower() == 'true'
            node = Node(value=bool_val, src_pos=(tok.line, tok.col))
            self.advance()
            return node
        # Null / None
        if self.current.type == Token.NULL:
            node = Node(value=None, src_pos=(self.current.line, self.current.col))
            self.advance()
            return node
        # Array
        if self.current.type == Token.LBRACKET:
            tok = self.current
            node = Node(src_pos=(tok.line, tok.col))
            node.elements = []
            self.advance()
            while True:
                if self.current.type == Token.COMMENT:
                    self.pending_comments.append(self.current.value)
                    self.advance()
                    continue
                if self.current.type == Token.RBRACKET:
                    self.advance()
                    break
                elem_node = self.parse_value()
                if self.pending_comments:
                    elem_node.comments_before = self.pending_comments
                    self.pending_comments = []
                if self.current.type == Token.COMMENT and elem_node.src_pos and self.current.line == elem_node.src_pos[0]:
                    elem_node.comment_inline = self.current.value
                    self.advance()
                node.elements.append(elem_node)
                # allow trailing comma: if COMMA -> consume and continue; if RBRACKET -> loop will break next
                if self.current.type == Token.COMMA:
                    self.advance()
                    continue
                if self.current.type == Token.RBRACKET:
                    continue
                raise ParserError(f"Expected comma or ']' in array at {self.current.line}:{self.current.col}")
            return node
        # Inline object literal after '=' (rare if not using 'key=')
        if self.current.type == Token.LBRACE:
            tok = self.current
            node = Node(src_pos=(tok.line, tok.col))
            node.children = {}
            self.advance()
            self.parse_block(node)
            return node
        raise ParserError(f"Unexpected token {self.current} when expecting value")

# --- JSON Emitter and .ker Pretty-Printer ---

# 1) JSON -> Node AST converter (py value -> Node)
def py_to_node(value, key=None, src_pos=None):
    """Convert a Python value (from json.loads) into a Node AST."""
    node = Node(key=key, value=None, src_pos=src_pos)
    if isinstance(value, dict):
        node.children = {}
        for k, v in value.items():
            child = py_to_node(v, key=k, src_pos=None)
            node.children[k] = child
    elif isinstance(value, list):
        node.elements = []
        for v in value:
            node.elements.append(py_to_node(v, src_pos=None))
    else:
        # literal
        node.value = value
    return node

def node_to_json(node: Node):
    """Convert AST Node to Python data suitable for json.dumps, keeping simple arrays inline."""
    if node.children is not None:
        return {k: node_to_json(v) for k, v in node.children.items()}
    if node.elements is not None:
        # If all elements are literals (no nested objects/arrays), keep inline
        if all(e.value is not None and e.children is None and e.elements is None for e in node.elements):
            return [e.value for e in node.elements]
        else:
            return [node_to_json(e) for e in node.elements]
    return node.value

def to_json(root_node: Node, indent=2):
    """Return valid JSON string for the entire config with simple literal arrays inline."""
    data = {}
    if root_node.children is not None:
        for k, child in root_node.children.items():
            data[k] = node_to_json(child)

    # Dump JSON with indent
    text = json.dumps(data, indent=indent, ensure_ascii=False)

    # Compact arrays of literals into single line
    def compact_array(match):
        return '[' + ', '.join(x.strip() for x in match.group(1).split(',')) + ']'

    # Regex: match arrays that have only numbers/booleans/nulls separated by commas and whitespace
    pattern = r'\[\s*([^\[\]\{\}]+?)\s*\]'
    text = re.sub(pattern, compact_array, text)

    return text


def from_json_string(json_text: str):
    """Parse a JSON string into a root Node (compatible with Parser.parse())."""
    py = json.loads(json_text)
    root = Node(key=None, value=None, src_pos=(1,1))
    root.children = {}
    if not isinstance(py, dict):
        # We expect top-level object; raise for now
        raise ValueError("JSON top-level must be an object for conversion to .ker")
    for k, v in py.items():
        root.children[k] = py_to_node(v, key=k, src_pos=None)
    return root

# 2) Improved .ker pretty-printer (recursive, consistent)
def dumps_to_ker(root_node: Node, indent_str="    "):
    """Return pretty-printed .ker text from AST with example.ker style."""

    def lit_repr(val):
        if isinstance(val, str):
            return json.dumps(val, ensure_ascii=False)
        if isinstance(val, bool):
            return "true" if val else "false"
        if val is None:
            return "null"
        return str(val)

    def identifier_repr(k):
        return k if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', k) else json.dumps(k)

    def node_lines(node: Node, key: Optional[str] = None, level: int = 0):
        ind = indent_str * level
        out = []

        # comments_before
        for c in node.comments_before:
            out.append(ind + "# " + c)

        # Object block
        if node.children is not None:
            if key is None:
                out.append(ind + "{")
            else:
                out.append(ind + f"{identifier_repr(key)} {{")
            for k, child in node.children.items():
                out.extend(node_lines(child, key=k, level=level + 1))
            out.append(ind + "}")
            return out

        # Array
        if node.elements is not None:
            # Determine if array is simple enough to inline
            simple = all(e.value is not None and not e.children and not e.elements for e in node.elements)
            if key is None:
                if simple and len(node.elements) <= 5:
                    line = "[{}]".format(", ".join(lit_repr(e.value) for e in node.elements))
                    out.append(ind + line)
                    return out
                out.append(ind + "[")
            else:
                if simple and len(node.elements) <= 5:
                    line = "{} = [{}]".format(identifier_repr(key), ", ".join(lit_repr(e.value) for e in node.elements))
                    out.append(ind + line)
                    return out
                out.append(ind + f"{identifier_repr(key)} = [")

            for elem in node.elements:
                for c in elem.comments_before:
                    out.append(ind + indent_str + "# " + c)
                if elem.children is not None or elem.elements is not None:
                    out.extend(node_lines(elem, key=None, level=level + 1))
                else:
                    v = lit_repr(elem.value)
                    line = ind + indent_str + v
                    if elem.comment_inline:
                        line += "  # " + elem.comment_inline
                    out.append(line)
            out.append(ind + "]")
            return out

        # Literal
        val_repr = lit_repr(node.value)
        if key is None:
            line = ind + val_repr
        else:
            line = ind + f"{identifier_repr(key)} = {val_repr}"
        if node.comment_inline:
            line += "  # " + node.comment_inline
        out.append(line)
        return out

    lines = []
    if root_node.children:
        for k, child in root_node.children.items():
            lines.extend(node_lines(child, key=k, level=0))
    return "\n".join(lines)


def from_json_file(path: str):
    text = open(path, 'r', encoding='utf-8').read()
    root = from_json_string(text)
    return root

# --- File conversion helpers ---

def read_file_or_stdin(path: str):
    if path == '-':
        return sys.stdin.read()
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_stdout_or_file(path: str, text: str):
    if path == '-':
        sys.stdout.write(text)
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)


def ker_to_json_file(ker_path, json_path, indent=2):
    """Read a .ker file, parse it, and write equivalent JSON to file."""
    with open(ker_path, "r", encoding="utf-8") as f:
        ker_text = f.read()
    parser_obj = Parser(ker_text)
    root_node = parser_obj.parse()
    json_text = to_json(root_node, indent=indent)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_text)
    print(f"Converted '{ker_path}' -> '{json_path}'")


def json_to_ker_file(json_path, ker_path, indent_str="  "):
    """Read a JSON file, convert it to .ker format, and write to file."""
    with open(json_path, "r", encoding="utf-8") as f:
        json_text = f.read()
    root_node = from_json_string(json_text)
    ker_text = dumps_to_ker(root_node, indent_str=indent_str)
    with open(ker_path, "w", encoding="utf-8") as f:
        f.write(ker_text + "\n")
    print(f"Converted '{json_path}' -> '{ker_path}'")


def main():
    parser_cli = argparse.ArgumentParser(prog="ker",
        description="`.ker` CLI (to-json, fmt, from-json)")
    subparsers = parser_cli.add_subparsers(dest="cmd", required=True)

    # .ker formatting
    fmt_p = subparsers.add_parser("fmt", help="format .ker file to canonical .ker")
    fmt_p.add_argument("input", help=".ker file to format (use - for stdin)")
    fmt_p.add_argument("output", nargs="?", default='-', help="output file (default stdout)")

    # .ker -> JSON
    tojson_p = subparsers.add_parser("to-json", help="convert .ker to JSON")
    tojson_p.add_argument("input", help=".ker file to convert (use - for stdin)")
    tojson_p.add_argument("output", nargs="?", default='-', help="output JSON file (default stdout)")
    tojson_p.add_argument("--indent", "-i", type=int, default=2, help="JSON indent")

    # JSON -> .ker
    fromjson_p = subparsers.add_parser("from-json", help="convert JSON to .ker")
    fromjson_p.add_argument("input", help="JSON file to convert to .ker (use - for stdin)")
    fromjson_p.add_argument("output", nargs="?", default='-', help="output .ker file (default stdout)")

    args = parser_cli.parse_args()

    try:
        if args.cmd in ("fmt", "to-json"):
            text = read_file_or_stdin(args.input)
            parser_obj = Parser(text)
            root = parser_obj.parse()

        if args.cmd == "fmt":
            out = dumps_to_ker(root)
            write_stdout_or_file(args.output, out)
        elif args.cmd == "to-json":
            out = to_json(root, indent=args.indent)
            write_stdout_or_file(args.output, out)
        elif args.cmd == "from-json":
            json_text = read_file_or_stdin(args.input)
            root_json = from_json_string(json_text)
            out = dumps_to_ker(root_json)
            write_stdout_or_file(args.output, out)

    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(2)
    except (LexerError, ParserError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# --- Simple built-in tests when run with no args ---

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        # Basic tests if no args
        def test_round_trip():
            sample = '''
                # Test config
                debug = true  # enable debug
                port = 8000
                data {
                    name = "value"
                    list = [1, 2, 3,]
                }
            '''
            p = Parser(sample)
            root = p.parse()
            json_str = to_json(root)
            # convert JSON back into AST
            root2 = from_json_string(json_str)
            # Check some values
            assert root.children['debug'].value == True
            assert root.children['port'].value == 8000
            assert 'data' in root.children
            data = root.children['data']
            assert data.children['name'].value == "value"
            # check from-json produced same data keys
            assert 'debug' in root2.children and 'port' in root2.children and 'data' in root2.children
            print("Round-trip test passed.")
        def test_comments():
            sample = '''
                # top comment
                key = "val"  # inline
            '''
            p = Parser(sample)
            root = p.parse()
            node = root.children['key']
            assert node.comments_before == ['top comment']
            assert node.comment_inline == 'inline'
            print("Comments test passed.")
        def test_unicode_escape():
            sample = r'''
                s = "\u263A"
            '''
            p = Parser(sample)
            root = p.parse()
            assert root.children['s'].value == '\u263A'
            print("Unicode escape test passed.")
        test_round_trip()
        test_comments()
        test_unicode_escape()
