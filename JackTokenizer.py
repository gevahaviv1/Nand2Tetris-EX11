"""Tokenizer for the Jack programming language."""

from __future__ import annotations

import re
import typing

from errors import JackSyntaxError


class JackTokenizer:
    """Tokenizes Jack source code for consumption by a compilation engine."""

    _KEYWORDS = {
        "class", "constructor", "function", "method", "field", "static",
        "var", "int", "char", "boolean", "void", "true", "false", "null",
        "this", "let", "do", "if", "else", "while", "return",
    }

    _SYMBOLS = {
        "{", "}", "(", ")", "[", "]", ".", ",", ";",
        "+", "-", "*", "/", "&", "|", "<", ">", "=", "~",
    }

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Read the entire input stream and prepare a token list."""

        source = input_stream.read()
        self._tokens = self._tokenize(source)
        self._current_token: typing.Optional[str] = None

    # ------------------------------------------------------------------
    # Tokenization utilities
    # ------------------------------------------------------------------
    def _tokenize(self, text: str) -> list[str]:
        """Return a list of tokens extracted from ``text``.

        Raises:
            JackSyntaxError: If an illegal character is encountered.
        """

        def remove_comments(source: str) -> str:
            source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
            source = re.sub(r"//.*", "", source)
            return source

        cleaned = remove_comments(text)
        tokens: list[str] = []
        token_re = re.compile(
            r"[{}\[\]()\.,;\+\-\*/&|<>=~]|\d+|[A-Za-z_]\w*|\"[^\"]*\""
        )

        for line_no, line in enumerate(cleaned.splitlines(), start=1):
            pos = 0
            while pos < len(line):
                if line[pos].isspace():
                    pos += 1
                    continue
                match = token_re.match(line, pos)
                if not match:
                    char = line[pos]
                    raise JackSyntaxError(
                        f"Invalid character {char!r} on line {line_no}"
                    )
                tokens.append(match.group(0))
                pos = match.end()

        return tokens


    def has_more_tokens(self) -> bool:
        """Return ``True`` if there are more tokens to consume."""

        return bool(self._tokens)

    def advance(self) -> None:
        """Advance to the next token if available."""

        if self.has_more_tokens():
            self._current_token = self._tokens.pop(0)

    def token_type(self) -> str:
        """Return the Jack classification of the current token."""

        if self._current_token is None:
            raise JackSyntaxError("No current token. Call advance() first.")

        token = self._current_token
        if token in self._KEYWORDS:
            return "KEYWORD"
        if token in self._SYMBOLS:
            return "SYMBOL"
        if token.isdigit():
            return "INT_CONST"
        if token.startswith('"') and token.endswith('"'):
            return "STRING_CONST"
        return "IDENTIFIER"

    def keyword(self) -> str:
        """Return the current token assuming it is a keyword."""
        return self._current_token

    def symbol(self) -> str:
        """Return the current token assuming it is a symbol."""
        return self._current_token

    def identifier(self) -> str:
        """Return the current token assuming it is an identifier."""
        return self._current_token

    def int_val(self) -> int:
        """Return the integer value of the current token."""
        return int(self._current_token)

    def string_val(self) -> str:
        """Return the string value of the current token without quotes."""
        return self._current_token.strip('"')

    def get_next_token(self) -> typing.Optional[str]:
        """Peek at the next token without consuming it."""
        return self._tokens[0] if self._tokens else None

    def get_token_string(self) -> str:
        """Return a string representation of the current token."""

        token_type = self.token_type()
        if token_type == "INT_CONST":
            return str(self.int_val())
        if token_type == "STRING_CONST":
            return self.string_val()
        return self._current_token

