import dataclasses

from formatting import Formatter
import lexer as lx
import parsing
from typing import AbstractSet


@dataclasses.dataclass
class InstructionFlags:
    """Construct and manipulate instruction flags"""

    HAS_ARG_FLAG: bool = False
    HAS_CONST_FLAG: bool = False
    HAS_NAME_FLAG: bool = False
    HAS_JUMP_FLAG: bool = False
    HAS_FREE_FLAG: bool = False
    HAS_LOCAL_FLAG: bool = False
    HAS_EVAL_BREAK_FLAG: bool = False
    HAS_DEOPT_FLAG: bool = False
    HAS_ERROR_FLAG: bool = False

    def __post_init__(self) -> None:
        self.bitmask = {name: (1 << i) for i, name in enumerate(self.names())}

    @staticmethod
    def fromInstruction(instr: parsing.Node) -> "InstructionFlags":
        has_free = (
            variable_used(instr, "PyCell_New")
            or variable_used(instr, "PyCell_GET")
            or variable_used(instr, "PyCell_SET")
        )

        return InstructionFlags(
            HAS_ARG_FLAG=variable_used(instr, "oparg"),
            HAS_CONST_FLAG=variable_used(instr, "FRAME_CO_CONSTS"),
            HAS_NAME_FLAG=variable_used(instr, "FRAME_CO_NAMES"),
            HAS_JUMP_FLAG=variable_used(instr, "JUMPBY"),
            HAS_FREE_FLAG=has_free,
            HAS_LOCAL_FLAG=(
                variable_used(instr, "GETLOCAL") or variable_used(instr, "SETLOCAL")
            )
            and not has_free,
            HAS_EVAL_BREAK_FLAG=variable_used(instr, "CHECK_EVAL_BREAKER"),
            HAS_DEOPT_FLAG=variable_used(instr, "DEOPT_IF"),
            HAS_ERROR_FLAG=(
                variable_used(instr, "ERROR_IF")
                or variable_used(instr, "error")
                or variable_used(instr, "pop_1_error")
                or variable_used(instr, "exception_unwind")
                or variable_used(instr, "resume_with_error")
            ),
        )

    @staticmethod
    def newEmpty() -> "InstructionFlags":
        return InstructionFlags()

    def add(self, other: "InstructionFlags") -> None:
        for name, value in dataclasses.asdict(other).items():
            if value:
                setattr(self, name, value)

    def names(self, value: bool | None = None) -> list[str]:
        if value is None:
            return list(dataclasses.asdict(self).keys())
        return [n for n, v in dataclasses.asdict(self).items() if v == value]

    def bitmap(self, ignore: AbstractSet[str] = frozenset()) -> int:
        flags = 0
        assert all(hasattr(self, name) for name in ignore)
        for name in self.names():
            if getattr(self, name) and name not in ignore:
                flags |= self.bitmask[name]
        return flags

    @classmethod
    def emit_macros(cls, out: Formatter) -> None:
        flags = cls.newEmpty()
        for name, value in flags.bitmask.items():
            out.emit(f"#define {name} ({value})")

        for name, value in flags.bitmask.items():
            out.emit(
                f"#define OPCODE_{name[:-len('_FLAG')]}(OP) "
                f"(_PyOpcode_opcode_metadata[OP].flags & ({name}))"
            )


def variable_used(node: parsing.Node, name: str) -> bool:
    """Determine whether a variable with a given name is used in a node."""
    return any(
        token.kind == "IDENTIFIER" and token.text == name for token in node.tokens
    )


def variable_used_unspecialized(node: parsing.Node, name: str) -> bool:
    """Like variable_used(), but skips #if ENABLE_SPECIALIZATION blocks."""
    tokens: list[lx.Token] = []
    skipping = False
    for i, token in enumerate(node.tokens):
        if token.kind == "MACRO":
            text = "".join(token.text.split())
            # TODO: Handle nested #if
            if text == "#if":
                if i + 1 < len(node.tokens) and node.tokens[i + 1].text in (
                    "ENABLE_SPECIALIZATION",
                    "TIER_ONE",
                ):
                    skipping = True
            elif text in ("#else", "#endif"):
                skipping = False
        if not skipping:
            tokens.append(token)
    return any(token.kind == "IDENTIFIER" and token.text == name for token in tokens)
