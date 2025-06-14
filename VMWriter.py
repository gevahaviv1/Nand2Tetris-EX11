"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from typing import TextIO, Iterable


class VMWriter:
    """
    Writes VM commands into a file. Encapsulates the VM command syntax.
    """

    _SEGMENT_MAP = {
        "CONST": "constant",
        "ARG": "argument",
        "LOCAL": "local",
        "STATIC": "static",
        "THIS": "this",
        "THAT": "that",
        "POINTER": "pointer",
        "TEMP": "temp",

        "constant": "constant",
        "argument": "argument",
        "local": "local",
        "static": "static",
        "this": "this",
        "that": "that",
        "pointer": "pointer",
        "temp": "temp",
    }

    _ARITHMETIC_ALLOWED = {
        "add", "sub", "neg",
        "eq", "gt", "lt",
        "and", "or", "not",
        "shiftleft", "shiftright",
    }

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Creates a new file and prepares it for writing VM commands."""
        self._out: TextIO = output_stream

    def write_push(self, segment: str, index: int) -> None:
        """Writes a VM push command.

        Args:
            segment (str): the segment to push to, can be "CONST", "ARG", 
            "LOCAL", "STATIC", "THIS", "THAT", "POINTER", "TEMP"
            index (int): the index to push to.
        """
        self._write("push", self._translate_segment(segment), index)

    def write_pop(self, segment: str, index: int) -> None:
        """Writes a VM pop command.

        Args:
            segment (str): the segment to pop from, can be "CONST", "ARG", 
            "LOCAL", "STATIC", "THIS", "THAT", "POINTER", "TEMP".
            index (int): the index to pop from.
        """
        self._write("pop", self._translate_segment(segment), index)

    def write_arithmetic(self, command: str) -> None:
        """Writes a VM arithmetic command.

        Args:
            command (str): the command to write, can be "ADD", "SUB", "NEG", 
            "EQ", "GT", "LT", "AND", "OR", "NOT", "SHIFTLEFT", "SHIFTRIGHT".
        """
        cmd = command.lower()
        if cmd not in self._ARITHMETIC_ALLOWED:
            raise ValueError(f"Illegal arithmetic command: {command}")
        self._write(cmd)

    def write_label(self, label: str) -> None:
        """Writes a VM label command.

        Args:
            label (str): the label to write.
        """
        self._write("label", label)

    def write_goto(self, label: str) -> None:
        """Writes a VM goto command.

        Args:
            label (str): the label to go to.
        """
        self._write("goto", label)

    def write_if(self, label: str) -> None:
        """Writes a VM if-goto command.

        Args:
            label (str): the label to go to.
        """
        self._write("if-goto", label)

    def write_call(self, name: str, n_args: int) -> None:
        """Writes a VM call command.

        Args:
            name (str): the name of the function to call.
            n_args (int): the number of arguments the function receives.
        """
        self._write("call", name, n_args)

    def write_function(self, name: str, n_locals: int) -> None:
        """Writes a VM function command.

        Args:
            name (str): the name of the function.
            n_locals (int): the number of local variables the function uses.
        """
        self._out.write("\n")
        self._write("function", name, n_locals)

    def write_return(self) -> None:
        """Writes a VM return command."""
        self._write("return")

    def _translate_segment(self, seg: str) -> str:
        try:
            return self._SEGMENT_MAP[seg]  # fast-path
        except KeyError:
            raise ValueError(f"Illegal memory segment: {seg}") from None

    def _write(self, *parts: Iterable[typing.Any]) -> None:
        line = " ".join(str(p) for p in parts if p not in ("", None))
        self._out.write(f"{line}\n")
