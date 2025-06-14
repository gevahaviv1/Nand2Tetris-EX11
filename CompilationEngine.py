"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org), as allowed by the Creative Common
Attribution-NonCommercial-ShareAlike 3.0 Unported License.
"""
import typing

class CompilationEngine:

    TOKEN_TYPE_MAP = {
        "KEYWORD":        "keyword",
        "SYMBOL":         "symbol",
        "IDENTIFIER":     "identifier",
        "INT_CONST":      "integerConstant",
        "STRING_CONST":   "stringConstant"
        }

    def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
        self.tokenizer = input_stream
        self.output_stream = output_stream
        self._indent_count = 0

        # Prime the tokenizer and immediately compile the class so that
        # users of this class only need to instantiate it in order to
        # generate the output. If the tokenizer has already been advanced
        # before this constructor is called, we should not advance it again.
        if getattr(self.tokenizer, "_current_token", None) is None:
            if self.tokenizer.has_more_tokens():
                self.tokenizer.advance()
        if getattr(self.tokenizer, "_current_token", None) is not None:
            self.compile_class()

    def compile_class(self) -> None:
        self._write_outer_tag("class")
        self._write_token("KEYWORD")
        self._write_token("IDENTIFIER")
        self._write_token("SYMBOL")

        while self._is_class_var_dec():
            self.compile_class_var_dec()

        while self._is_subroutine():
            self.compile_subroutine()

        self._write_token("SYMBOL")
        self._write_outer_tag("class", end=True)

    def compile_class_var_dec(self) -> None:
        self._write_outer_tag("classVarDec")
        self._write_token("KEYWORD")
        self._write_type()
        self._write_token("IDENTIFIER")

        while self._is_symbol(","):
            self._write_token("SYMBOL")
            self._write_token("IDENTIFIER")

        self._write_token("SYMBOL")
        self._write_outer_tag("classVarDec", end=True)

    def compile_subroutine(self) -> None:
        self._write_outer_tag("subroutineDec")
        self._write_token("KEYWORD")
        self._write_type()
        self._write_token("IDENTIFIER")
        self._write_token("SYMBOL")
        self.compile_parameter_list()
        self._write_token("SYMBOL")
        self._write_outer_tag("subroutineBody")
        self._write_token("SYMBOL")
        
        while self._is_var_dec():
            self.compile_var_dec()

        self.compile_statements()
        self._write_token("SYMBOL")
        self._write_outer_tag("subroutineBody", end=True)
        self._write_outer_tag("subroutineDec", end=True)

    def compile_parameter_list(self) -> None:
        self._write_outer_tag("parameterList")
        if not self._is_symbol(")"):
            self._write_type()
            self._write_token("IDENTIFIER")
            while self._is_symbol(","):
                self._write_token("SYMBOL")
                self._write_type()
                self._write_token("IDENTIFIER")
        self._write_outer_tag("parameterList", end=True)

    def compile_var_dec(self) -> None:
        self._write_outer_tag("varDec")
        self._write_token("KEYWORD")
        self._write_type()
        self._write_token("IDENTIFIER")

        while self._is_symbol(","):
            self._write_token("SYMBOL")
            self._write_token("IDENTIFIER")

        self._write_token("SYMBOL")
        self._write_outer_tag("varDec", end=True)

    def compile_statements(self) -> None:
        self._write_outer_tag("statements")
        while self._is_statement():
            if self._is_keyword("let"):
                self.compile_let()
            elif self._is_keyword("if"):
                self.compile_if()
            elif self._is_keyword("while"):
                self.compile_while()
            elif self._is_keyword("do"):
                self.compile_do()
            elif self._is_keyword("return"):
                self.compile_return()

        self._write_outer_tag("statements", end=True)

    def compile_do(self) -> None:
        self._write_outer_tag("doStatement")
        self._write_token("KEYWORD")
        self.compile_subroutine_call()
        self._write_token("SYMBOL")
        self._write_outer_tag("doStatement", end=True)

    def compile_let(self) -> None:
        self._write_outer_tag("letStatement")
        self._write_token("KEYWORD")
        self._write_token("IDENTIFIER")

        if self._is_symbol("["):
            self._write_token("SYMBOL")
            self.compile_expression()
            self._write_token("SYMBOL")

        self._write_token("SYMBOL")
        self.compile_expression()
        self._write_token("SYMBOL")
        self._write_outer_tag("letStatement", end=True)

    def compile_while(self) -> None:
        self._write_outer_tag("whileStatement")
        self._write_token("KEYWORD")
        self._write_token("SYMBOL")
        self.compile_expression()
        self._write_token("SYMBOL")
        self._write_token("SYMBOL")
        self.compile_statements()
        self._write_token("SYMBOL")
        self._write_outer_tag("whileStatement", end=True)

    def compile_return(self) -> None:
        self._write_outer_tag("returnStatement")
        self._write_token("KEYWORD")

        if not self._is_symbol(";"):
            self.compile_expression()

        self._write_token("SYMBOL")
        self._write_outer_tag("returnStatement", end=True)

    def compile_if(self) -> None:
        self._write_outer_tag("ifStatement")
        self._write_token("KEYWORD")
        self._write_token("SYMBOL")
        self.compile_expression()
        self._write_token("SYMBOL")
        self._write_token("SYMBOL")
        self.compile_statements()
        self._write_token("SYMBOL")

        if self._is_keyword("else"):
            self._write_token("KEYWORD")
            self._write_token("SYMBOL")
            self.compile_statements()
            self._write_token("SYMBOL")

        self._write_outer_tag("ifStatement", end=True)

    def compile_expression(self) -> None:
        self._write_outer_tag("expression")
        self.compile_term()

        while self._is_operator():
            self._write_token("SYMBOL")
            self.compile_term()

        self._write_outer_tag("expression", end=True)

    def compile_term(self) -> None:
        self._write_outer_tag("term")

        if self._is_integer_constant() or self._is_string_constant() or self._is_keyword_constant():
            self._write_token(self.tokenizer.token_type())

        elif self._is_symbol("("):
            self._write_token("SYMBOL")
            self.compile_expression()
            self._write_token("SYMBOL")

        elif self._is_unary_op():
            self._write_token("SYMBOL")
            self.compile_term()

        elif self._is_identifier():
            identifier = self.tokenizer.get_token_string()
            self.tokenizer.advance()

            if self._is_symbol("["):
                self._write_xml_identifier(identifier)
                self._write_token("SYMBOL")
                self.compile_expression()
                self._write_token("SYMBOL")
            elif self._is_symbol("(") or self._is_symbol("."):
                self._compile_subroutine_call_with_peeked_identifier(identifier)
            else:
                self._write_xml_identifier(identifier)

        else:
            raise ValueError("compile_term: Unexpected token in term.")

        self._write_outer_tag("term", end=True)

    def compile_expression_list(self) -> None:
        self._write_outer_tag("expressionList")
        if not self._is_symbol(")"):
            self.compile_expression()
            while self._is_symbol(","):
                self._write_token("SYMBOL")
                self.compile_expression()

        self._write_outer_tag("expressionList", end=True)

    def _compile_subroutine_call_with_peeked_identifier(self, first_identifier: str) -> None:
        self._write_xml_identifier(first_identifier)
        if self._is_symbol("."):
            self._write_token("SYMBOL")
            self._write_token("IDENTIFIER")

        self._write_token("SYMBOL")
        self.compile_expression_list()
        self._write_token("SYMBOL")

    def compile_subroutine_call(self) -> None:
        if self._is_identifier():
            first_id = self.tokenizer.get_token_string()
            self.tokenizer.advance()
            self._compile_subroutine_call_with_peeked_identifier(first_id)
        else:
            raise ValueError("compile_subroutine_call: expected IDENTIFIER for subroutine name/var.")

    def _write_token(self, expected_type: str) -> None:
        token_type = self.tokenizer.token_type()
        if token_type != expected_type:
            raise ValueError(f"Expected token type {expected_type}, got {token_type}")

        token_value = self.tokenizer.get_token_string()
        token_value = self._escape_xml(token_value)

        token_type_lower = self.TOKEN_TYPE_MAP.get(token_type, token_type.lower())

        self.output_stream.write(
            f"{'  ' * self._indent_count}<{token_type_lower}> {token_value} </{token_type_lower}>\n"
        )
        
        self.tokenizer.advance()

    def _escape_xml(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _write_outer_tag(self, tag: str, end: bool = False) -> None:
        if end:
            self.output_stream.write(f"{'  ' * self._indent_count}</{tag}>\n")
            self._indent_count -= 1
        else:
            self.output_stream.write(f"{'  ' * self._indent_count}<{tag}>\n")
            self._indent_count += 1

    def _write_type(self) -> None:
        ttype = self.tokenizer.token_type()
        if ttype not in ("KEYWORD", "IDENTIFIER"):
            raise ValueError(f"Expected type to be KEYWORD or IDENTIFIER, got {ttype}")
        self._write_token(ttype)

    def _write_xml_identifier(self, ident: str) -> None:
        self.output_stream.write(f"{'  ' * self._indent_count}<identifier> {ident} </identifier>\n")

    def _is_class_var_dec(self) -> bool:
        return self._is_keyword("static") or self._is_keyword("field")

    def _is_subroutine(self) -> bool:
        return (self._is_keyword("constructor") or
                self._is_keyword("function") or
                self._is_keyword("method"))

    def _is_var_dec(self) -> bool:
        return self._is_keyword("var")

    def _is_statement(self) -> bool:
        return (self._is_keyword("let") or self._is_keyword("if") or
                self._is_keyword("while") or self._is_keyword("do") or
                self._is_keyword("return"))

    def _is_operator(self) -> bool:
        if self.tokenizer.token_type() != "SYMBOL":
            return False
        return self.tokenizer.get_token_string() in {"+", "-", "*", "/", "&", "|", "<", ">", "=", "^", "#"}

    def _is_unary_op(self) -> bool:
        if self.tokenizer.token_type() != "SYMBOL":
            return False
        return self.tokenizer.get_token_string() in {"-", "~"}

    def _is_keyword_constant(self) -> bool:
        if self.tokenizer.token_type() != "KEYWORD":
            return False
        return self.tokenizer.get_token_string() in {"true", "false", "null", "this"}

    def _is_symbol(self, symbol: str) -> bool:
        if self.tokenizer.token_type() != "SYMBOL":
            return False
        return (self.tokenizer.get_token_string() == symbol)

    def _is_keyword(self, keyword: str) -> bool:
        if self.tokenizer.token_type() != "KEYWORD":
            return False
        return (self.tokenizer.get_token_string() == keyword)

    def _is_integer_constant(self) -> bool:
        return self.tokenizer.token_type() == "INT_CONST"

    def _is_string_constant(self) -> bool:
        return self.tokenizer.token_type() == "STRING_CONST"

    def _is_identifier(self) -> bool:
        return self.tokenizer.token_type() == "IDENTIFIER"

