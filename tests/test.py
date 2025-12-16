import os
import ker

def main():
    # path relative to this file
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    example_path = os.path.join(root_dir, "examples", "example.ker")

    with open(example_path, "r", encoding="utf-8") as f:
        text = f.read()

    data = ker.loads(text)
    print("JSON output:\n", data)
    print("\nRound-tripped .ker:\n", ker.dumps(data))

if __name__ == "__main__":
    main()
