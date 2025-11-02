import json
from parser import Parser

def main():
    with open("sample_parser_in.txt", "r") as f:
        tokens = json.load(f)

    parser = Parser(tokens)
    ast = parser.parse_program()

    with open("parser_output.txt", "w") as f:
        json.dump(ast, f, indent=4)

    with open("sample_parser_out.txt", "r") as f:
        expected = json.load(f)

    if ast == expected:
        print("Parser output matches expected sample_out.txt")
    else:
        print("Parser output differs from expected sample_out.txt")
        print("Generated output saved to parser_output.txt")

if __name__ == "__main__":
    main()
