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
        "<class>",
        "  <keyword> class </keyword>",
        "  <identifier> Main </identifier>",
        "  <symbol> { </symbol>",
        "  <subroutineDec>",
        "    <keyword> function </keyword>",
        "    <keyword> void </keyword>",
        "    <identifier> main </identifier>",
        "    <symbol> ( </symbol>",
        "    <parameterList>",
        "      </parameterList>",
        "    <symbol> ) </symbol>",
        "    <subroutineBody>",
        "      <symbol> { </symbol>",
        "      <statements>",
        "        <returnStatement>",
        "          <keyword> return </keyword>",
        "          <symbol> ; </symbol>",
        "          </returnStatement>",
        "        </statements>",
        "      <symbol> } </symbol>",
        "      </subroutineBody>",
        "    </subroutineDec>",
        "  <symbol> } </symbol>",
        "  </class>",
    ]
    assert result == expected


def test_compile_basic_class_pre_advanced():
    code = "class Main { function void main() { return; } }"
    tokenizer = JackTokenizer(io.StringIO(code))
    tokenizer.advance()
    output = io.StringIO()
    CompilationEngine(tokenizer, output)
    result = output.getvalue().strip().splitlines()
    expected = [
        "<class>",
        "  <keyword> class </keyword>",
        "  <identifier> Main </identifier>",
        "  <symbol> { </symbol>",
        "  <subroutineDec>",
        "    <keyword> function </keyword>",
        "    <keyword> void </keyword>",
        "    <identifier> main </identifier>",
        "    <symbol> ( </symbol>",
        "    <parameterList>",
        "      </parameterList>",
        "    <symbol> ) </symbol>",
        "    <subroutineBody>",
        "      <symbol> { </symbol>",
        "      <statements>",
        "        <returnStatement>",
        "          <keyword> return </keyword>",
        "          <symbol> ; </symbol>",
        "          </returnStatement>",
        "        </statements>",
        "      <symbol> } </symbol>",
        "      </subroutineBody>",
        "    </subroutineDec>",
        "  <symbol> } </symbol>",
        "  </class>",
    ]
    assert result == expected
