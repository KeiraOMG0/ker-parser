# ker-parser

> ⚠️ **Major rewrite notice (v1.0.0)**
> This release is a **large internal rewrite** that split the project into clear modules (lexer, parser, AST, JSON helpers, CLI).
> If you find bugs, edge cases, or have ideas for improvement, **issues and pull requests are highly appreciated** for this release.

A small Python parser and CLI for `.ker` configuration files. Supports comments, blocks, arrays, JSON ↔ `.ker` conversion, and a `ker` command-line tool.

`ker` is intentionally lightweight and readable, aiming to be easier to hand-edit than JSON while remaining structured and predictable.

---

## Features (Updated)

* `.ker` → Python dict loading
* Python dict / JSON → `.ker` dumping
* Comments (full-line and inline)
* Nested blocks and arrays
* Canonical formatter (`ker fmt`)
* Simple CLI similar to `json.tool`
* **Enhanced CLI flags**:

  * `ker` → prints banner with name + version + hint
  * `ker --version` → prints version
  * `ker --author` → prints author
  * `ker --info` → prints version, author, and project goal
  * `ker -h` / `ker --help` → help with commands and options

---

## Install

### For users

```bash
pip install git+https://github.com/KeiraOMG0/ker-parser.git
```

### For developers (editable)

```bash
git clone https://github.com/KeiraOMG0/ker-parser.git
cd ker-parser
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # macOS / Linux
pip install -e .
```

This installs a `ker` command (editable install — changes take effect immediately).

---

## CLI usage

### Banner & Help

Run `ker` with no arguments:

```bash
ker
# Outputs: ker 1.0.0 by KeiraOMG0
# Hint: Run 'ker -h' for help
```

General help:

```bash
ker -h
```

Show version only:

```bash
ker --version
```

Show author only:

```bash
ker --author
```

Show project info (version, author, goal):

```bash
ker --info
```

### Commands

Format a `.ker` file:

```bash
ker fmt examples/example.ker pretty.ker
```

Convert `.ker` → JSON:

```bash
ker to-json examples/example.ker examples/example.json
```

Convert JSON → `.ker`:

```bash
ker from-json examples/example.json out.ker
```

Print to stdout:

```bash
ker to-json examples/example.ker -
```

---

## Using as a library (unchanged)

### Load a `.ker` config

```python
import ker

config = ker.load("config.ker")
print(config["server"]["port"])
```

```ker
server {
    host = "localhost"
    port = 8080
}
```

### Load from string

```python
import ker

config = ker.loads("""
server {
    host = "127.0.0.1"
    port = 8080
}
""")
```

### Dump to `.ker`

```python
import ker

ker_text = ker.dumps({"debug": True, "port": 8000})
print(ker_text)
```

---

## Project layout

```text
ker/
├── lexer.py         # character scanning / tokens
├── parser.py        # grammar → AST
├── json_support.py  # JSON ↔ AST helpers
├── wrapper.py       # public load/dump API
├── tool.py          # CLI implementation
├── errors.py        # shared exceptions
└── __init__.py      # public exports
```

Only the functions exposed in `ker.__init__` are considered public API.

---

## Target audience (unchanged)

* Python developers who want a **human-friendly config format**
* Small to medium projects (bots, tools, services)
* Not intended as a strict standard or replacement for JSON/YAML

---

## Comparison (unchanged)

| Format | Pros                                  | Cons                          |
| ------ | ------------------------------------- | ----------------------------- |
| JSON   | Standard, ubiquitous                  | Verbose, no comments          |
| YAML   | Flexible, readable                    | Complex, ambiguous edge cases |
| `.ker` | Simple grammar, comments, predictable | New, non-standard             |

`.ker` intentionally stays small and opinionated.

---

## Contributing

Issues and pull requests are welcome.

Guidelines:

* Keep the grammar simple
* Avoid feature creep
* Prefer clarity over cleverness


---

## License (unchanged)

MIT
