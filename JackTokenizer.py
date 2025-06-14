import re
import typing

class JackTokenizer:

    def __init__(self, input_stream: typing.TextIO) -> None:
        self._lines = input_stream.read().splitlines()
        self._token_buffer = []
        self._current_token = None
        self._current_token_type = None
        self._in_comment = False
        self._prepare_tokensss()

    def _prepare_tokensss(self) -> None:
        def remove_comments(text: str) -> str:
            text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
            text = re.sub(r"//.*", "", text)
            return text

        big_text = "\n".join(self._lines)
        cleaned = remove_comments(big_text)
        lines_no_comments = [line.strip() for line in cleaned.splitlines()]
        cleaned_lines = filter(None, lines_no_comments)

        for line in cleaned_lines:
            tokens = re.findall(r"[{}\[\]()\.,;\+\-\*/&|<>=~]|\w+|\".*?\"", line)
            self._token_buffer.extend(tokens)


    def has_more_tokens(self) -> bool:
        return len(self._token_buffer) > 0

    def advance(self) -> None:
        if self.has_more_tokens():
            self._current_token = self._token_buffer.pop(0)
            self._current_token_type = self.token_type()

    def token_type(self) -> str:
        keywords = {"class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean", "void", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"}
        symbols = {"{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"}

        if self._current_token in keywords:
            return "KEYWORD"
        elif self._current_token in symbols:
            return "SYMBOL"
        elif self._current_token.isdigit():
            return "INT_CONST"
        elif self._current_token.startswith('"') and self._current_token.endswith('"'):
            return "STRING_CONST"
        else:
            return "IDENTIFIER"

    def keyword(self) -> str:
        return self._current_token

    def symbol(self) -> str:
        return self._current_token

    def identifier(self) -> str:
        return self._current_token

    def int_val(self) -> int:
        return int(self._current_token)

    def string_val(self) -> str:
        return self._current_token.strip('"')

    def get_next_token(self) -> typing.Optional[str]:
        return self._token_buffer[0] if self._token_buffer else None

    def get_token_string(self) -> str:
        token_type = self.token_type()
        if token_type == "KEYWORD":
            return self.keyword()
        elif token_type == "SYMBOL":
            return self.symbol()
        elif token_type == "IDENTIFIER":
            return self.identifier()
        elif token_type == "INT_CONST":
            return str(self.int_val())
        elif token_type == "STRING_CONST":
            return self.string_val()
        return ""

