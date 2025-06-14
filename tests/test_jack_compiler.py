import sys, os, io
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine


def test_tokenizer_basic():
    code = "class Main { function void main() { return; } }"
    tokenizer = JackTokenizer(io.StringIO(code))
    tokens = []
    while tokenizer.has_more_tokens():
        tokenizer.advance()
        tokens.append(tokenizer.get_token_string())
    assert tokens == [
        "class", "Main", "{", "function", "void", "main", "(", ")",
        "{", "return", ";", "}", "}"
    ]


def test_compile_basic_class():
    code = "class Main { function void main() { return; } }"
    tokenizer = JackTokenizer(io.StringIO(code))
    output = io.StringIO()
    CompilationEngine(tokenizer, output)
    result = output.getvalue().strip().splitlines()
    expected = [
        "function Main.main 0",
        "push constant 0",
        "return",
    ]
    assert result == expected
