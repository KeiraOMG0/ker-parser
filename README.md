### `README.md` (starter)


# ker-parser

A small Python parser and CLI for `.ker` configuration files. Supports comments, blocks, arrays, JSON ↔ .ker conversion, and a `ker` command-line tool.

## Install locally (editable)
From the project root:

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# or: source venv/bin/activate  # macOS / Linux

pip install -e .
```

That installs a `ker` command (editable install — changes are immediate).

## CLI examples

Format a .ker file:

```bash
ker fmt examples/example.ker pretty.ker
```

Convert .ker → JSON:

```bash
ker to-json examples/example.ker examples/example.json
```

Convert JSON → .ker:

```bash
ker from-json examples/example.json out.ker
```

Or print to stdout:

```bash
ker to-json examples/example.ker -
```

## Using as a library

```python
from ker_parser.main import Parser, to_json, dumps_to_ker

with open("examples/example.ker", "r", encoding="utf-8") as f:
    root = Parser(f.read()).parse()

print(to_json(root))
```

## Contributing

Open issues or PRs, run tests in `tests/test.py`, etc.

## License

MIT

