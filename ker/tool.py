import argparse
import sys
from .wrapper import load, loads, dump, dumps, json_to_ker, ker_to_json

__name__ = "ker"
__version__ = "1.0.0"
__author__ = "KeiraOMG0"
__goal__ = "Format and convert .ker config files with JSON interop"

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

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Banner if no args
    if not argv:
        print(f"{__name__} {__version__} by {__author__}")
        print(f"Run '{__name__} -h' for help")
        sys.exit(0)

    parser_cli = argparse.ArgumentParser(
        prog=__name__,
        description=f"`.ker` CLI: {__goal__}"
    )
    parser_cli.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser_cli.add_argument("--author", action="store_true", help="show author info")
    parser_cli.add_argument("--info", action="store_true", help="show version, author, and project goal")

    subparsers = parser_cli.add_subparsers(dest="cmd", required=False)

    fmt_p = subparsers.add_parser("fmt", help="format .ker file to canonical .ker")
    fmt_p.add_argument("input", help=".ker file to format (use - for stdin)")
    fmt_p.add_argument("output", nargs="?", default='-', help="output file (default stdout)")

    tojson_p = subparsers.add_parser("to-json", help="convert .ker to JSON")
    tojson_p.add_argument("input", help=".ker file to convert (use - for stdin)")
    tojson_p.add_argument("output", nargs="?", default='-', help="output JSON file (default stdout)")
    tojson_p.add_argument("--indent", "-i", type=int, default=2, help="JSON indent")

    fromjson_p = subparsers.add_parser("from-json", help="convert JSON to .ker")
    fromjson_p.add_argument("input", help="JSON file to convert to .ker (use - for stdin)")
    fromjson_p.add_argument("output", nargs="?", default='-', help="output .ker file (default stdout)")

    args = parser_cli.parse_args(argv)

    # Handle standalone flags first
    if getattr(args, "author", False):
        print(f"{__author__}")
        sys.exit(0)
    if getattr(args, "info", False):
        print(f"{__name__} {__version__}")
        print(f"Author: {__author__}")
        print(f"Goal: {__goal__}")
        sys.exit(0)

    # If a command is provided
    if args.cmd is None:
        parser_cli.print_help()
        sys.exit(1)

    try:
        if args.cmd == 'fmt':
            text = read_file_or_stdin(args.input)
            out = dumps(loads(text))
            write_stdout_or_file(args.output, out)
        elif args.cmd == 'to-json':
            text = read_file_or_stdin(args.input)
            ker_to_json(args.input, args.output, indent=args.indent)
        elif args.cmd == 'from-json':
            if args.input == '-':
                import json
                data = json.loads(sys.stdin.read())
                out = dumps(data)
                write_stdout_or_file(args.output, out)
            else:
                json_to_ker(args.input, args.output)

    except FileNotFoundError:
        print(f"Error: file not found: {getattr(args, 'input', '')}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
