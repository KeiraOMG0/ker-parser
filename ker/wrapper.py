from .parser import Parser, Node as ParserNode
from .json_support import node_to_json, py_to_node, dumps_to_ker
from .errors import KerError
from typing import Any
import json
import os


def loads(text: str) -> Any:
    """Parse ker text and return plain Python data (dict/list/literals)."""
    try:
        p = Parser(text)
        root = p.parse()
        return node_to_json(root)
    except Exception as e:
        raise KerError(str(e)) from e


def load(path_or_fp) -> Any:
    if hasattr(path_or_fp, 'read'):
        return loads(path_or_fp.read())
    with open(path_or_fp, 'r', encoding='utf-8') as f:
        return loads(f.read())


def dumps(obj, indent_str="    ") -> str:
    # Build a root Node and serialize using dumps_to_ker
    # new — use real Node so json_support functions see a consistent object
    root = ParserNode()  
    root.key = None
    root.value = None
    root.src_pos = None
    root.comments_before = []
    root.comment_inline = None
    root.children = {}
    root.elements = None

    for k, v in obj.items():
        root.children[k] = py_to_node(v, key=k)

    return dumps_to_ker(root, indent_str=indent_str)


def dump(obj, path_or_fp, indent_str="    "):
    text = dumps(obj, indent_str=indent_str)
    if hasattr(path_or_fp, 'write'):
        path_or_fp.write(text)
    else:
        with open(path_or_fp, 'w', encoding='utf-8') as f:
            f.write(text)


def load_json(path_or_fp):
    if hasattr(path_or_fp, 'read'):
        return json.load(path_or_fp)
    with open(path_or_fp, 'r', encoding='utf-8') as f:
        return json.load(f)


def json_to_ker(json_path, ker_path, indent_str="  "):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    dump(data, ker_path, indent_str=indent_str)


def ker_to_json(ker_path, json_path, indent=2):
    root = Parser(open(ker_path, 'r', encoding='utf-8').read()).parse()
    text = node_to_json(root)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(text, f, indent=indent, ensure_ascii=False)
