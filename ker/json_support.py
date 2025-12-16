# ker/json_support.py
import json
import re
from typing import Optional
from .parser import Node

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

def dumps_to_ker(root_node: Node, indent_str: str = "    ") -> str:
    """
    Pretty-print a Node tree to .ker format.

    indent_str: string used for one indentation level (default 4 spaces).
    """
    def node_lines(node: Node, key: Optional[str], level: int):
        ind = indent_str * level
        out = []

        # comments before this node
        for c in getattr(node, "comments_before", []):
            out.append(ind + "# " + c)

        # Object block
        if getattr(node, "children", None) is not None:
            if key is None:
                out.append(ind + "{")
            else:
                out.append(ind + f"{identifier_repr(key)} {{")
            for k, child in node.children.items():
                out.extend(node_lines(child, k, level + 1))
            out.append(ind + "}")
            return out

        # Array
        if getattr(node, "elements", None) is not None:
            simple = all((getattr(e, "value", None) is not None) and not getattr(e, "children", None) and not getattr(e, "elements", None) for e in node.elements)
            if key is None:
                if simple and len(node.elements) <= 5:
                    line = "[{}]".format(", ".join(lit_repr(e.value) for e in node.elements))
                    out.append(ind + line)
                    return out
                out.append(ind + "[")
            else:
                if simple and len(node.elements) <= 5:
                    line = f"{identifier_repr(key)} = [{', '.join(lit_repr(e.value) for e in node.elements)}]"
                    out.append(ind + line)
                    return out
                out.append(ind + f"{identifier_repr(key)} = [")

            for elem in node.elements:
                for c in getattr(elem, "comments_before", []):
                    out.append(ind + indent_str + "# " + c)
                if getattr(elem, "children", None) is not None or getattr(elem, "elements", None) is not None:
                    out.extend(node_lines(elem, key=None, level=level + 1))
                else:
                    v = lit_repr(elem.value)
                    line = ind + indent_str + v
                    if getattr(elem, "comment_inline", None):
                        line += "  # " + elem.comment_inline
                    out.append(line)
            out.append(ind + "]")
            return out

        # Literal
        val_repr = lit_repr(getattr(node, "value", None))
        if key is None:
            line = ind + val_repr
        else:
            line = ind + f"{identifier_repr(key)} = {val_repr}"
        if getattr(node, "comment_inline", None):
            line += "  # " + node.comment_inline
        out.append(line)
        return out

    lines = []
    if getattr(root_node, "children", None):
        for k, child in root_node.children.items():
            lines.extend(node_lines(child, k, 0))
    return "\n".join(lines)


def node_to_json(node: Node):
    """Convert AST Node -> plain Python structures (dict/list/literals)."""
    if getattr(node, "children", None) is not None:
        return {k: node_to_json(v) for k, v in node.children.items()}
    if getattr(node, "elements", None) is not None:
        return [node_to_json(e) for e in node.elements]
    return getattr(node, "value", None)

def py_to_node(val, key=None):
    """Convert plain Python value -> Node tree (for dumping)."""
    # Create a Node instance without assuming constructor signature
    n = Node()  # construct empty, then set attributes
    # set common attrs
    n.key = key
    n.value = None
    n.src_pos = None
    n.comments_before = []
    n.comment_inline = None
    n.children = None
    n.elements = None

    if isinstance(val, dict):
        n.children = {}
        for k, v in val.items():
            child = py_to_node(v, key=k)
            n.children[k] = child
    elif isinstance(val, list):
        n.elements = []
        for v in val:
            n.elements.append(py_to_node(v))
    else:
        n.value = val

    return n
