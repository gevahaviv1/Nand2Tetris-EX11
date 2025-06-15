"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

class _Symbol:
    """A single identifier-record inside the symbol table."""

    __slots__ = ("type", "kind", "index")

    def __init__(self, type_: str, kind: str, index: int) -> None:
        self.type: str = type_
        self.kind: str = kind
        self.index: int = index

class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    _CLASS_KINDS = {"STATIC", "FIELD"}
    _SUB_KINDS   = {"ARG", "VAR"}
    _ALL_KINDS   = _CLASS_KINDS | _SUB_KINDS

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        self._class_scope: dict[str, _Symbol] = {}
        self._sub_scope:   dict[str, _Symbol] = {}
        # unified per-kind counters
        self._counters = {kind: 0 for kind in self._ALL_KINDS}

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        self._sub_scope.clear()
        self._counters["ARG"] = 0
        self._counters["VAR"] = 0

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        kind = kind.upper()
        if kind not in self._ALL_KINDS:
            raise ValueError(f"Illegal identifier kind: {kind}")

        index = self._counters[kind]
        self._counters[kind] += 1
        entry = _Symbol(type, kind, index)

        if kind in self._CLASS_KINDS:
            self._class_scope[name] = entry
        else:
            self._sub_scope[name] = entry

    def var_count(self, kind: str) -> int:
        """Returns how many identifiers of ``kind`` have been defined.

        In accordance with the nand2tetris specification, ``STATIC`` and
        ``FIELD`` counters are maintained at the class level, while ``ARG`` and
        ``VAR`` counters are reset for every subroutine.  Therefore this method
        simply exposes the relevant counter value.

        Args:
            kind (str): ``STATIC``, ``FIELD``, ``ARG`` or ``VAR``.
        """
        kind = kind.upper()
        return self._counters.get(kind, 0)

    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        entry = self._lookup(name)
        return entry.kind if entry else None

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        entry = self._lookup(name)
        return entry.type if entry else None

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        entry = self._lookup(name)
        return entry.index if entry else None

    # ---------------------------------------------------------------------- #
    # Debug helpers                                                          #
    # ---------------------------------------------------------------------- #
    def __str__(self) -> str:
        """Nicely formatted snapshot - handy while developing / debugging."""
        lines: list[str] = []
        for scope_name, scope in (("class", self._class_scope),
                                  ("sub",   self._sub_scope)):
            for n, sym in scope.items():
                lines.append(f"{scope_name:5s} | {n:15s} "
                             f"| {sym.type:10s} | {sym.kind:<6s} | {sym.index}")
        return "\n".join(lines) if lines else "(empty)"

    # ---------------------------------------------------------------------- #
    # Internal utilities                                                     #
    # ---------------------------------------------------------------------- #
    def _lookup(self, name: str) -> typing.Optional[_Symbol]:
        """Search *subroutine* scope first, then class scope."""
        return self._sub_scope.get(name) or self._class_scope.get(name)
