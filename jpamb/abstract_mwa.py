# Abstract domains for machine word analysis
# Based on interval analysis and bitfield domains from the course material

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Set, Literal
import math

# constants for three-valued logic
THREE_VALUED_0 = "0"
THREE_VALUED_1 = "1" 
THREE_VALUED_BOT = "⊥"  # unknown bit value

@dataclass(frozen=True)
class Interval:
    """Basic interval domain [low, high]"""
    low: float = -math.inf
    high: float = math.inf

    @staticmethod
    def of(*values: int):
        # create interval from concrete values
        if not values:
            return Interval()
        return Interval(min(values), max(values))

    def is_bottom(self) -> bool:
        # bottom means impossible/empty (low > high)
        return self.low > self.high
    
    def is_top(self) -> bool:
        return self.low == -math.inf and self.high == math.inf

    def __repr__(self) -> str:
        if self.is_bottom():
            return "⊥"
        if self.is_top():
            return "(-∞, +∞)"
        return f"[{int(self.low) if self.low != -math.inf else '-∞'}, {int(self.high) if self.high != math.inf else '+∞'}]"

    def join(self, other: "Interval") -> "Interval":
        # least upper bound - take widest range
        if self.is_bottom(): 
            return other
        if other.is_bottom(): 
            return self
        return Interval(min(self.low, other.low), max(self.high, other.high))

    def meet(self, other: "Interval") -> "Interval":
        # intersection of intervals
        low = max(self.low, other.low)
        high = min(self.high, other.high)
        return Interval(low, high)

    def widen(self, other: "Interval") -> "Interval":
        # widening operator for loop termination
        low = self.low if self.low <= other.low else -math.inf
        high = self.high if self.high >= other.high else math.inf
        return Interval(low, high)

    def __add__(self, other: "Interval") -> "Interval":
        if self.is_bottom() or other.is_bottom():
            return Interval(1, 0)  # bottom
        return Interval(self.low + other.low, self.high + other.high)

    def __sub__(self, other: "Interval") -> "Interval":
        if self.is_bottom() or other.is_bottom():
            return Interval(1, 0)
        return Interval(self.low - other.high, self.high - other.low)

    def __mul__(self, other: "Interval") -> "Interval":
        if self.is_bottom() or other.is_bottom():
            return Interval(1, 0)
        a, b, c, d = self.low, self.high, other.low, other.high
        # need to check all combinations
        return Interval(min(a*c, a*d, b*c, b*d), max(a*c, a*d, b*c, b*d))

    def __neg__(self) -> "Interval":
        if self.is_bottom():
            return Interval(1, 0)
        return Interval(-self.high, -self.low)
    
    def __and__(self, other: "Interval") -> "Interval":
        # bitwise AND - conservative approximation
        if self.is_bottom() or other.is_bottom():
            return Interval(1, 0)
        
        if self.low < 0 or other.low < 0:
            # negative numbers make this tricky
            return Interval(-max(abs(self.high), abs(other.high)), 
                          max(self.high, other.high))
        
        return Interval(0, min(self.high, other.high))
    
    def __or__(self, other: "Interval") -> "Interval":
        if self.is_bottom() or other.is_bottom():
            return Interval(1, 0)
        
        if self.low < 0 or other.low < 0:
            return Interval(-max(abs(self.high), abs(other.high)), 
                          max(self.high, other.high))
        
        return Interval(0, max(self.high, other.high))
    
    def __xor__(self, other: "Interval") -> "Interval":
        if self.is_bottom() or other.is_bottom():
            return Interval(1, 0)
        
        if self.low < 0 or other.low < 0:
            return Interval(-max(abs(self.high), abs(other.high)), 
                          max(self.high, other.high))
        
        return Interval(0, max(self.high, other.high))
    
    def lshift(self, bits: int) -> "Interval":
        if self.is_bottom():
            return Interval(1, 0)
        return Interval(self.low * (2 ** bits), self.high * (2 ** bits))
    
    def rshift(self, bits: int) -> "Interval":
        if self.is_bottom():
            return Interval(1, 0)
        return Interval(self.low // (2 ** bits), self.high // (2 ** bits))


@dataclass(frozen=True, order=True)
class SignedInterval(Interval):
    """Signed interval with bit width (default 32-bit)"""
    bit_width: int = 32
    
    def __post_init__(self):
        min_val = -(2 ** (self.bit_width - 1))
        max_val = 2 ** (self.bit_width - 1) - 1
        
        # clamp to valid range
        if not (self.low == -math.inf or self.low == math.inf):
            object.__setattr__(self, 'low', max(self.low, min_val))
        if not (self.high == -math.inf or self.high == math.inf):
            object.__setattr__(self, 'high', min(self.high, max_val))


@dataclass(frozen=True, order=True)
class UnsignedInterval(Interval):
    """Unsigned interval [0, 2^n - 1]"""
    bit_width: int = 32
    
    def __post_init__(self):
        min_val = 0
        max_val = 2 ** self.bit_width - 1
        
        if not (self.low == -math.inf or self.low == math.inf):
            object.__setattr__(self, 'low', max(self.low, min_val))
        if not (self.high == -math.inf or self.high == math.inf):
            object.__setattr__(self, 'high', min(self.high, max_val))


@dataclass(frozen=True)
class Bitfield:
    """Bitfield with 3-valued logic: 0, 1, or ⊥ (unknown)"""
    bits: tuple = ()
    bit_width: int = 32
    
    def __init__(self, bits: tuple | str = "⊥", bit_width: int = 32):
        if isinstance(bits, str):
            object.__setattr__(self, 'bits', tuple([bits] * bit_width))
        else:
            object.__setattr__(self, 'bits', bits)
        object.__setattr__(self, 'bit_width', bit_width)
    
    @staticmethod
    def of(value: int, bit_width: int = 32) -> "Bitfield":
        # convert concrete value to bitfield
        bits_list = []
        for i in range(bit_width):
            bit_val = (value >> i) & 1
            bits_list.append("1" if bit_val else "0")
        return Bitfield(tuple(reversed(bits_list)), bit_width)
    
    def _bit_op_3valued(self, op: str, other: "Bitfield") -> "Bitfield":
        # 3-valued logic operations
        result = []
        for a, b in zip(self.bits, other.bits):
            if op == "AND":
                table = {
                    ("0", "0"): "0", ("0", "1"): "0", ("0", "⊥"): "0",
                    ("1", "0"): "0", ("1", "1"): "1", ("1", "⊥"): "⊥",
                    ("⊥", "0"): "0", ("⊥", "1"): "⊥", ("⊥", "⊥"): "⊥",
                }
            elif op == "OR":
                table = {
                    ("0", "0"): "0", ("0", "1"): "1", ("0", "⊥"): "⊥",
                    ("1", "0"): "1", ("1", "1"): "1", ("1", "⊥"): "1",
                    ("⊥", "0"): "⊥", ("⊥", "1"): "1", ("⊥", "⊥"): "⊥",
                }
            elif op == "XOR":
                table = {
                    ("0", "0"): "0", ("0", "1"): "1", ("0", "⊥"): "⊥",
                    ("1", "0"): "1", ("1", "1"): "0", ("1", "⊥"): "⊥",
                    ("⊥", "0"): "⊥", ("⊥", "1"): "⊥", ("⊥", "⊥"): "⊥",
                }
            result.append(table.get((a, b), "⊥"))
        return Bitfield(tuple(result), self.bit_width)
    
    def __and__(self, other: "Bitfield") -> "Bitfield":
        return self._bit_op_3valued("AND", other)
    
    def __or__(self, other: "Bitfield") -> "Bitfield":
        return self._bit_op_3valued("OR", other)
    
    def __xor__(self, other: "Bitfield") -> "Bitfield":
        return self._bit_op_3valued("XOR", other)
    
    def __invert__(self) -> "Bitfield":
        # flip bits (0->1, 1->0, ⊥ stays ⊥)
        result = tuple("1" if b == "0" else "0" if b == "1" else "⊥" for b in self.bits)
        return Bitfield(result, self.bit_width)
    
    def join(self, other: "Bitfield") -> "Bitfield":
        # merge bitfields - different bits become unknown
        result = []
        for a, b in zip(self.bits, other.bits):
            if a == b:
                result.append(a)
            else:
                result.append("⊥")
        return Bitfield(tuple(result), self.bit_width)
    
    def is_bottom(self) -> bool:
        return False
    
    def __repr__(self) -> str:
        return "".join(self.bits)