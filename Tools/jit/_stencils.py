"""Core data structures for compiled code templates."""
import dataclasses
import enum
import sys

import _schema


@enum.unique
class HoleValue(enum.Enum):
    """
    Different "base" values that can be patched into holes (usually combined with the
    address of a symbol and/or an addend).
    """

    # The base address of the machine code for the current uop (exposed as _JIT_ENTRY):
    CODE = enum.auto()
    # The base address of the machine code for the next uop (exposed as _JIT_CONTINUE):
    CONTINUE = enum.auto()
    # The base address of the read-only data for this uop:
    DATA = enum.auto()
    # The address of the current executor (exposed as _JIT_EXECUTOR):
    EXECUTOR = enum.auto()
    # The base address of the "global" offset table located in the read-only data.
    # Shouldn't be present in the final stencils, since these are all replaced with
    # equivalent DATA values:
    GOT = enum.auto()
    # The current uop's oparg (exposed as _JIT_OPARG):
    OPARG = enum.auto()
    # The current uop's operand (exposed as _JIT_OPERAND):
    OPERAND = enum.auto()
    # The current uop's target (exposed as _JIT_TARGET):
    TARGET = enum.auto()
    # The base address of the machine code for the first uop (exposed as _JIT_TOP):
    TOP = enum.auto()
    # A hardcoded value of zero (used for symbol lookups):
    ZERO = enum.auto()


@dataclasses.dataclass
class Hole:
    """
    A "hole" in the stencil to be patched with a computed runtime value.

    Analogous to relocation records in an object file.
    """

    offset: int
    kind: _schema.HoleKind
    # Patch with this base value:
    value: HoleValue
    # ...plus the address of this symbol:
    symbol: str | None
    # ...plus this addend:
    addend: int
    # Convenience method:
    replace = dataclasses.replace

    def as_c(self) -> str:
        """Dump this hole as an initialization of a C Hole struct."""
        parts = [
            f"{self.offset:#x}",
            f"HoleKind_{self.kind}",
            f"HoleValue_{self.value.name}",
            f"&{self.symbol}" if self.symbol else "NULL",
            _format_addend(self.addend),
        ]
        return f"{{{', '.join(parts)}}}"


@dataclasses.dataclass
class Stencil:
    """
    A contiguous block of machine code or data to be copied-and-patched.

    Analogous to a section or segment in an object file.
    """

    body: bytearray = dataclasses.field(default_factory=bytearray, init=False)
    holes: list[Hole] = dataclasses.field(default_factory=list, init=False)
    disassembly: list[str] = dataclasses.field(default_factory=list, init=False)

    def pad(self, alignment: int) -> None:
        """Pad the stencil to the given alignment."""
        offset = len(self.body)
        padding = -offset % alignment
        self.disassembly.append(f"{offset:x}: {' '.join(['00'] * padding)}")
        self.body.extend([0] * padding)

    def emit_aarch64_trampoline(self, hole: Hole) -> None:
        """Even with the large code model, AArch64 Linux insists on 28-bit jumps."""
        base = len(self.body)
        where = slice(hole.offset, hole.offset + 4)
        instruction = int.from_bytes(self.body[where], sys.byteorder)
        instruction &= 0xFC000000
        instruction |= ((base - hole.offset) >> 2) & 0x03FFFFFF
        self.body[where] = instruction.to_bytes(4, sys.byteorder)
        self.disassembly += [
            f"{base + 4 * 0: x}: d2800008      mov     x8, #0x0",
            f"{base + 4 * 0:016x}:  R_AARCH64_MOVW_UABS_G0_NC    {hole.symbol}",
            f"{base + 4 * 1:x}: f2a00008      movk    x8, #0x0, lsl #16",
            f"{base + 4 * 1:016x}:  R_AARCH64_MOVW_UABS_G1_NC    {hole.symbol}",
            f"{base + 4 * 2:x}: f2c00008      movk    x8, #0x0, lsl #32",
            f"{base + 4 * 2:016x}:  R_AARCH64_MOVW_UABS_G2_NC    {hole.symbol}",
            f"{base + 4 * 3:x}: f2e00008      movk    x8, #0x0, lsl #48",
            f"{base + 4 * 3:016x}:  R_AARCH64_MOVW_UABS_G3       {hole.symbol}",
            f"{base + 4 * 4:x}: d61f0100      br      x8",
        ]
        for code in [
            0xD2800008.to_bytes(4, sys.byteorder),
            0xF2A00008.to_bytes(4, sys.byteorder),
            0xF2C00008.to_bytes(4, sys.byteorder),
            0xF2E00008.to_bytes(4, sys.byteorder),
            0xD61F0100.to_bytes(4, sys.byteorder),
        ]:
            self.body.extend(code)
        for i, kind in enumerate(
            [
                "R_AARCH64_MOVW_UABS_G0_NC",
                "R_AARCH64_MOVW_UABS_G1_NC",
                "R_AARCH64_MOVW_UABS_G2_NC",
                "R_AARCH64_MOVW_UABS_G3",
            ]
        ):
            self.holes.append(hole.replace(offset=base + 4 * i, kind=kind))


@dataclasses.dataclass
class StencilGroup:
    """
    Code and data corresponding to a given micro-opcode.

    Analogous to an entire object file.
    """

    code: Stencil = dataclasses.field(default_factory=Stencil, init=False)
    data: Stencil = dataclasses.field(default_factory=Stencil, init=False)
    symbols: dict[int | str, tuple[HoleValue, int]] = dataclasses.field(
        default_factory=dict, init=False
    )
    _got: dict[str, int] = dataclasses.field(default_factory=dict, init=False)

    def process_relocations(self, *, alignment: int = 1) -> None:
        """Fix up all GOT and internal relocations for this stencil group."""
        self.code.pad(alignment)
        self.data.pad(8)
        for stencil in [self.code, self.data]:
            holes = []
            for hole in stencil.holes:
                if hole.value is HoleValue.GOT:
                    assert hole.symbol is not None
                    hole.value = HoleValue.DATA
                    hole.addend += self._global_offset_table_lookup(hole.symbol)
                    hole.symbol = None
                elif hole.symbol in self.symbols:
                    hole.value, addend = self.symbols[hole.symbol]
                    hole.addend += addend
                    hole.symbol = None
                elif (
                    hole.kind in {"R_AARCH64_CALL26", "R_AARCH64_JUMP26"}
                    and hole.value is HoleValue.ZERO
                ):
                    self.code.emit_aarch64_trampoline(hole)
                    continue
                holes.append(hole)
            stencil.holes[:] = holes
        self.code.pad(alignment)
        self._emit_global_offset_table()
        self.code.holes.sort(key=lambda hole: hole.offset)
        self.data.holes.sort(key=lambda hole: hole.offset)

    def _global_offset_table_lookup(self, symbol: str) -> int:
        return len(self.data.body) + self._got.setdefault(symbol, 8 * len(self._got))

    def _emit_global_offset_table(self) -> None:
        got = len(self.data.body)
        for s, offset in self._got.items():
            if s in self.symbols:
                value, addend = self.symbols[s]
                symbol = None
            else:
                value, symbol = symbol_to_value(s)
                addend = 0
            self.data.holes.append(
                Hole(got + offset, "R_X86_64_64", value, symbol, addend)
            )
            value_part = value.name if value is not HoleValue.ZERO else ""
            if value_part and not symbol and not addend:
                addend_part = ""
            else:
                addend_part = f"&{symbol}" if symbol else ""
                addend_part += _format_addend(addend, signed=symbol is not None)
                if value_part:
                    value_part += "+"
            self.data.disassembly.append(
                f"{len(self.data.body):x}: {value_part}{addend_part}"
            )
            self.data.body.extend([0] * 8)


def symbol_to_value(symbol: str) -> tuple[HoleValue, str | None]:
    """
    Convert a symbol name to a HoleValue and a symbol name.

    Some symbols (starting with "_JIT_") are special and are converted to their
    own HoleValues.
    """
    if symbol.startswith("_JIT_"):
        try:
            return HoleValue[symbol.removeprefix("_JIT_")], None
        except KeyError:
            pass
    return HoleValue.ZERO, symbol


def _format_addend(addend: int, signed: bool = False) -> str:
    addend %= 1 << 64
    if addend & (1 << 63):
        addend -= 1 << 64
    return f"{addend:{'+#x' if signed else '#x'}}"
