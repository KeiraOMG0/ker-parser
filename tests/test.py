# simple test / example runner for local dev
from ker_parser.main import Parser, to_json, dumps_to_ker

def main():
    with open("examples/example.ker", "r", encoding="utf-8") as f:
        text = f.read()

    root = Parser(text).parse()

    print("JSON output:\n")
    print(to_json(root, indent=2))
    print("\nPretty .ker (round-tripped):\n")
    print(dumps_to_ker(root))

if __name__ == "__main__":
    main()
