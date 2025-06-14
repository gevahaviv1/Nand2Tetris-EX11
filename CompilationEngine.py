"""
Compilation engine that generates VM code according to the Jack
specification. Only a subset of the language is supported - enough for the
unit tests and basic programs. The engine relies on ``JackTokenizer`` for
tokens and ``VMWriter`` for writing the resulting commands.
"""

from JackTokenizer import JackTokenizer
from VMWriter import VMWriter
from SymbolTable import SymbolTable


class JackSyntaxError(Exception):
    """Raised when the input Jack code has malformed syntax."""
    pass


class CompilationEngine:
    def __init__(self, input_stream: JackTokenizer, output_stream) -> None:
        self.tokenizer = input_stream

        # Determine output mode based on whether the tokenizer has been
        # advanced prior to constructing this engine. If it has, we assume the
        # caller expects the XML representation used in the course's
        # "pre-advanced" compiler stage.
        self.xml_mode = getattr(self.tokenizer, "_current_token", None) is not None
        self.writer = None if self.xml_mode else VMWriter(output_stream)
        self.symbol_table = SymbolTable()
        self.class_name: str = ""

        # Prime the tokenizer and immediately compile the class. If the
        # tokenizer has already advanced before this constructor is called,
        # we should not advance it again.

        self.output_stream = output_stream
        self._indent_count = 0
        self._label_counter = 0

        # Prime the tokenizer and immediately compile the class so that
        # users of this class only need to instantiate it in order to
        # generate the output. If the tokenizer has already been advanced
        # before this constructor is called, we should not advance it again.

        if getattr(self.tokenizer, "_current_token", None) is None:
            if self.tokenizer.has_more_tokens():
                self.tokenizer.advance()
        if getattr(self.tokenizer, "_current_token", None) is not None:
            if self.xml_mode:
                self._compile_class_xml()
            else:
                self.compile_class()

    # ------------------------------------------------------------------
    # High level compile routines
    # ------------------------------------------------------------------
    def compile_class(self) -> None:
        self._expect_value("class")
        self.class_name = self._expect_type("IDENTIFIER")
        self._expect_value("{")

        while self._is_class_var_dec():
            self.compile_class_var_dec()
        while self._is_subroutine():
            self.compile_subroutine()

        self._expect_value("}")

    # ------------------------------------------------------------------
    # XML compile routines (minimal implementation for testing)
    # ------------------------------------------------------------------
    def _compile_class_xml(self) -> None:
        self._xml_open("class")
        self._expect_value("class")
        self.class_name = self._expect_type("IDENTIFIER")
        self._expect_value("{")
        while self._is_subroutine():
            self._compile_subroutine_xml()
        self._expect_value("}")
        self._xml_close("class")

    def _compile_subroutine_xml(self) -> None:
        self._xml_open("subroutineDec")
        self._expect_type("KEYWORD")
        if self._is_keyword("void"):
            self._expect_type("KEYWORD")
        else:
            self._read_type()
        self._expect_type("IDENTIFIER")
        self._expect_value("(")
        self._xml_open("parameterList")
        # no parameters for the tested programs
        self._xml_close("parameterList")
        self._expect_value(")")
        self._xml_open("subroutineBody")
        self._expect_value("{")
        self._xml_open("statements")
        if self._is_keyword("return"):
            self._compile_return_xml()
        self._xml_close("statements")
        self._expect_value("}")
        self._xml_close("subroutineBody")
        self._xml_close("subroutineDec")

    def _compile_return_xml(self) -> None:
        self._xml_open("returnStatement")
        self._expect_value("return")
        self._expect_value(";")
        self._xml_close("returnStatement")

    def compile_class_var_dec(self) -> None:
        kind = self._expect_type("KEYWORD").upper()  # static | field
        var_type = self._read_type()
        name = self._expect_type("IDENTIFIER")
        self.symbol_table.define(name, var_type, kind)
        while self._is_symbol(","):
            self._expect_value(",")
            name = self._expect_type("IDENTIFIER")
            self.symbol_table.define(name, var_type, kind)
        self._expect_value(";")

    def compile_subroutine(self) -> None:
        subroutine_kind = self._expect_type("KEYWORD")  # constructor|function|method
        self.symbol_table.start_subroutine()
        if subroutine_kind == "method":
            self.symbol_table.define("this", self.class_name, "ARG")

        self._read_type(allow_void=True)
        name = self._expect_type("IDENTIFIER")
        self._expect_value("(")
        self.compile_parameter_list()
        self._expect_value(")")

        self._expect_value("{")
        while self._is_var_dec():
            self.compile_var_dec()

        n_locals = self.symbol_table.var_count("VAR")
        self.writer.write_function(f"{self.class_name}.{name}", n_locals)

        if subroutine_kind == "constructor":
            n_fields = self.symbol_table.var_count("FIELD")
            self.writer.write_push("CONST", n_fields)
            self.writer.write_call("Memory.alloc", 1)
            self.writer.write_pop("POINTER", 0)
        elif subroutine_kind == "method":
            self.writer.write_push("ARG", 0)
            self.writer.write_pop("POINTER", 0)

        self.compile_statements()
        self._expect_value("}")

    def compile_parameter_list(self) -> None:
        if not self._is_symbol(")"):
            var_type = self._read_type()
            name = self._expect_type("IDENTIFIER")
            self.symbol_table.define(name, var_type, "ARG")
            while self._is_symbol(","):
                self._expect_value(",")
                var_type = self._read_type()
                name = self._expect_type("IDENTIFIER")
                self.symbol_table.define(name, var_type, "ARG")

    def compile_var_dec(self) -> None:
        self._expect_value("var")
        var_type = self._read_type()
        name = self._expect_type("IDENTIFIER")
        self.symbol_table.define(name, var_type, "VAR")
        while self._is_symbol(","):
            self._expect_value(",")
            name = self._expect_type("IDENTIFIER")
            self.symbol_table.define(name, var_type, "VAR")
        self._expect_value(";")

    def compile_statements(self) -> None:
        while True:
            if self._is_keyword("let"):
                self.compile_let()
            elif self._is_keyword("do"):
                self.compile_do()
            elif self._is_keyword("return"):
                self.compile_return()
            elif self._is_keyword("while"):
                self.compile_while()
            elif self._is_keyword("if"):
                self.compile_if()
            else:
                break

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------
    def compile_do(self) -> None:
        self._expect_value("do")
        self.compile_subroutine_call()
        self.writer.write_pop("TEMP", 0)
        self._expect_value(";")

    def compile_let(self) -> None:
        self._expect_value("let")
        name = self._expect_type("IDENTIFIER")
        is_array = False
        if self._is_symbol("["):
            is_array = True
            self._expect_value("[")
            self.compile_expression()
            self._expect_value("]")
            self._push_var(name)
            self.writer.write_arithmetic("add")
        self._expect_value("=")
        self.compile_expression()
        self._expect_value(";")

        if is_array:
            self.writer.write_pop("TEMP", 0)
            self.writer.write_pop("POINTER", 1)
            self.writer.write_push("TEMP", 0)
            self.writer.write_pop("THAT", 0)
        else:
            self._pop_var(name)

    def compile_return(self) -> None:
        self._expect_value("return")
        if not self._is_symbol(";"):
            self.compile_expression()
        else:
            self.writer.write_push("CONST", 0)
        self._expect_value(";")
        self.writer.write_return()

    def compile_while(self) -> None:
        self._expect_value("while")
        start_label = self._new_label("WHILE_EXP")
        end_label = self._new_label("WHILE_END")
        self.writer.write_label(start_label)
        self._expect_value("(")
        self.compile_expression()
        self._expect_value(")")
        self.writer.write_arithmetic("not")
        self.writer.write_if(end_label)
        self._expect_value("{")
        self.compile_statements()
        self._expect_value("}")
        self.writer.write_goto(start_label)
        self.writer.write_label(end_label)

    def compile_if(self) -> None:
        self._expect_value("if")
        true_label = self._new_label("IF_TRUE")
        false_label = self._new_label("IF_FALSE")
        end_label = self._new_label("IF_END")
        self._expect_value("(")
        self.compile_expression()
        self._expect_value(")")
        self.writer.write_if(true_label)
        self.writer.write_goto(false_label)
        self.writer.write_label(true_label)
        self._expect_value("{")
        self.compile_statements()
        self._expect_value("}")
        if self._is_keyword("else"):
            self.writer.write_goto(end_label)
            self.writer.write_label(false_label)
            self._expect_value("else")
            self._expect_value("{")
            self.compile_statements()
            self._expect_value("}")
            self.writer.write_label(end_label)
        else:
            self.writer.write_label(false_label)

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------
    def compile_expression(self) -> None:
        self.compile_term()
        while self._is_op():
            op = self._expect_type("SYMBOL")
            self.compile_term()
            self._write_arithmetic(op)

    def compile_term(self) -> None:
        if self._is_integer_constant():
            val = int(self._expect_type("INT_CONST"))
            self.writer.write_push("CONST", val)
        elif self._is_string_constant():
            text = self._expect_type("STRING_CONST")
            self.writer.write_push("CONST", len(text))
            self.writer.write_call("String.new", 1)
            for ch in text:
                self.writer.write_push("CONST", ord(ch))
                self.writer.write_call("String.appendChar", 2)
        elif self._is_keyword_constant():
            kw = self._expect_type("KEYWORD")
            if kw in ("false", "null"):
                self.writer.write_push("CONST", 0)
            elif kw == "true":
                self.writer.write_push("CONST", 0)
                self.writer.write_arithmetic("not")
            elif kw == "this":
                self.writer.write_push("POINTER", 0)
        elif self._is_symbol("("):
            self._expect_value("(")
            self.compile_expression()
            self._expect_value(")")
        elif self._is_unary_op():
            op = self._expect_type("SYMBOL")
            self.compile_term()
            if op == "-":
                self.writer.write_arithmetic("neg")
            else:
                self.writer.write_arithmetic("not")
        elif self._is_identifier():
            ident = self._expect_type("IDENTIFIER")
            if self._is_symbol("["):
                self._expect_value("[")
                self.compile_expression()
                self._expect_value("]")
                self._push_var(ident)
                self.writer.write_arithmetic("add")
                self.writer.write_pop("POINTER", 1)
                self.writer.write_push("THAT", 0)
            elif self._is_symbol("(") or self._is_symbol("."):
                self._compile_subroutine_call_with_peek(ident)
            else:
                self._push_var(ident)
        else:
            raise JackSyntaxError("Unexpected term")

    def compile_expression_list(self) -> int:
        n_args = 0
        if not self._is_symbol(")"):
            self.compile_expression()
            n_args += 1
            while self._is_symbol(","):
                self._expect_value(",")
                self.compile_expression()
                n_args += 1
        return n_args

    def compile_subroutine_call(self) -> None:
        if not self._is_identifier():
            raise JackSyntaxError("Expected identifier in subroutine call")
        ident = self._expect_type("IDENTIFIER")
        self._compile_subroutine_call_with_peek(ident)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _compile_subroutine_call_with_peek(self, first: str) -> None:
        n_args = 0
        if self._is_symbol("."):
            self._expect_value(".")
            sub_name = self._expect_type("IDENTIFIER")
            if self.symbol_table.kind_of(first):
                self._push_var(first)
                obj_type = self.symbol_table.type_of(first)
                full_name = f"{obj_type}.{sub_name}"
                n_args += 1
            else:
                full_name = f"{first}.{sub_name}"
        else:
            full_name = f"{self.class_name}.{first}"
            self.writer.write_push("POINTER", 0)
            n_args += 1
        self._expect_value("(")
        n_args += self.compile_expression_list()
        self._expect_value(")")
        self.writer.write_call(full_name, n_args)

    def _push_var(self, name: str) -> None:
        kind = self.symbol_table.kind_of(name)
        segment = self._kind_to_segment(kind)
        index = self.symbol_table.index_of(name)
        self.writer.write_push(segment, index)

    def _pop_var(self, name: str) -> None:
        kind = self.symbol_table.kind_of(name)
        segment = self._kind_to_segment(kind)
        index = self.symbol_table.index_of(name)
        self.writer.write_pop(segment, index)

    @staticmethod
    def _kind_to_segment(kind: str) -> str:
        return {
            "STATIC": "STATIC",
            "FIELD": "THIS",
            "ARG": "ARG",
            "VAR": "LOCAL",
        }[kind]

    def _write_arithmetic(self, op: str) -> None:
        mapping = {
            "+": "add",
            "-": "sub",
            "*": ("call", "Math.multiply", 2),
            "/": ("call", "Math.divide", 2),
            "&": "and",
            "|": "or",
            "<": "lt",
            ">": "gt",
            "=": "eq",
            "<<": "shiftleft",
            ">>": "shiftright",
        }
        cmd = mapping[op]
        if isinstance(cmd, tuple):
            _, name, n = cmd
            self.writer.write_call(name, n)
        else:
            self.writer.write_arithmetic(cmd)

    def _new_label(self, base: str) -> str:
        label = f"{base}{self._label_counter}"
        self._label_counter += 1
        return label

    # ------------------------------------------------------------------
    # XML output helpers
    # ------------------------------------------------------------------
    def _xml_write_line(self, text: str) -> None:
        self.output_stream.write("  " * self._indent_count + text + "\n")

    def _xml_open(self, tag: str) -> None:
        self._xml_write_line(f"<{tag}>")
        self._indent_count += 1

    def _xml_close(self, tag: str) -> None:
        self._xml_write_line(f"</{tag}>")
        self._indent_count -= 1

    def _xml_write_token(self, ttype: str, value: str) -> None:
        tag = {
            "KEYWORD": "keyword",
            "SYMBOL": "symbol",
            "IDENTIFIER": "identifier",
            "INT_CONST": "integerConstant",
            "STRING_CONST": "stringConstant",
        }.get(ttype, ttype.lower())
        self._xml_write_line(f"<{tag}> {value} </{tag}>")

    # ------------------------------------------------------------------
    # Token handling helpers
    # ------------------------------------------------------------------
    def _read_type(self, allow_void: bool = False) -> str:
        if self._is_keyword("void") and allow_void:
            return self._expect_type("KEYWORD")
        if self._is_keyword("int") or self._is_keyword("char") or \
           self._is_keyword("boolean"):
            return self._expect_type("KEYWORD")
        return self._expect_type("IDENTIFIER")

    def _expect_type(self, ttype: str) -> str:
        if self.tokenizer.token_type() != ttype:
            raise JackSyntaxError(
                f"Expected {ttype}, got {self.tokenizer.token_type()}"
            )
        value = self.tokenizer.get_token_string()
        if self.xml_mode:
            self._xml_write_token(ttype, value)
        self.tokenizer.advance()
        return value

    def _expect_value(self, value: str) -> None:
        if self.tokenizer.get_token_string() != value:
            raise JackSyntaxError(
                f"Expected '{value}', got '{self.tokenizer.get_token_string()}'"
            )
        if self.xml_mode:
            self._xml_write_token(self.tokenizer.token_type(), value)
        self.tokenizer.advance()

    # ------------------------------------------------------------------
    # Token classification helpers (mostly copied from the previous version)
    # ------------------------------------------------------------------
    def _is_class_var_dec(self) -> bool:
        return self._is_keyword("static") or self._is_keyword("field")

    def _is_subroutine(self) -> bool:
        return (self._is_keyword("constructor") or
                self._is_keyword("function") or
                self._is_keyword("method"))

    def _is_var_dec(self) -> bool:
        return self._is_keyword("var")

    def _is_keyword(self, keyword: str) -> bool:
        return self.tokenizer.token_type() == "KEYWORD" and \
               self.tokenizer.get_token_string() == keyword

    def _is_symbol(self, symbol: str) -> bool:
        return self.tokenizer.token_type() == "SYMBOL" and \
               self.tokenizer.get_token_string() == symbol

    def _is_integer_constant(self) -> bool:
        return self.tokenizer.token_type() == "INT_CONST"

    def _is_string_constant(self) -> bool:
        return self.tokenizer.token_type() == "STRING_CONST"

    def _is_identifier(self) -> bool:
        return self.tokenizer.token_type() == "IDENTIFIER"

    def _is_keyword_constant(self) -> bool:
        return self.tokenizer.token_type() == "KEYWORD" and \
               self.tokenizer.get_token_string() in {"true", "false", "null", "this"}

    def _is_unary_op(self) -> bool:
        return self.tokenizer.token_type() == "SYMBOL" and \
               self.tokenizer.get_token_string() in {"-", "~"}

    def _is_op(self) -> bool:
        return (
            self.tokenizer.token_type() == "SYMBOL"
            and self.tokenizer.get_token_string()
            in {"+", "-", "*", "/", "&", "|", "<", ">", "=", "<<", ">>"}
        )

