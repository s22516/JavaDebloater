#Test for Machine Word Abstract Domains

import sys
import os
import importlib.util
import math
from jpamb.abstract_mwa import Bitfield, SignedInterval, UnsignedInterval

def test_bitfield_operations():
    """Test the Bitfield domain with 3-valued logic"""
    print("\n=== Testing Bitfield Domain ===\n")
    
    # Basic bitfield creation
    b1 = Bitfield.of(5, 8)
    b2 = Bitfield.of(3, 8)
    print(f"b1 = {b1} (5 in binary)")
    print(f"b2 = {b2} (3 in binary)")
    
    # Bitwise operations
    print(f"\nAND: {b1} & {b2} = {b1 & b2}")
    print(f"OR:  {b1} | {b2} = {b1 | b2}")
    print(f"XOR: {b1} ^ {b2} = {b1 ^ b2}")
    print(f"NOT: ~{b1} = {~b1}")
    
    # Unknown bits
    b_unknown = Bitfield("⊥", 8)
    print(f"\nUnknown bitfield: {b_unknown}")
    
    # Join operation
    b0 = Bitfield.of(0, 8)
    b5 = Bitfield.of(5, 8)
    print(f"Join {b0} and {b5} = {b0.join(b5)}")


def test_signed_intervals():
    """Test signed interval domain"""
    print("\n=== Testing Signed Intervals ===\n")
    
    s1 = SignedInterval(-100, 100)
    s2 = SignedInterval(50, 150)
    zero = SignedInterval(0, 0)
    
    print(f"s1 = {s1}")
    print(f"s2 = {s2}")
    
    # Arithmetic operations
    print(f"\nArithmetic:")
    print(f"s1 + zero = {s1 + zero}")
    print(f"s2 - zero = {s2 - zero}")
    print(f"s1 * zero = {s1 * zero}")
    print(f"-s1 = {-s1}")
    
    # Bitwise operations
    a = SignedInterval(12, 12)
    b = SignedInterval(10, 10)
    print(f"\nBitwise:")
    print(f"[12,12] & [10,10] = {a & b}")
    print(f"[12,12] | [10,10] = {a | b}")
    print(f"[12,12] ^ [10,10] = {a ^ b}")
    
    # Shifts
    s = SignedInterval(8, 8)
    print(f"\nShifts:")
    print(f"[8,8] << 2 = {s.lshift(2)}")
    print(f"[8,8] >> 1 = {s.rshift(1)}")
    
    # Lattice operations
    print(f"\nLattice operations:")
    print(f"s1 join s2 = {s1.join(s2)}")
    print(f"s1 meet s2 = {s1.meet(s2)}")
    print(f"s1 widen s2 = {s1.widen(s2)}")


def test_unsigned_intervals():
    """Test unsigned interval domain"""
    print("\n=== Testing Unsigned Intervals ===\n")
    
    u1 = UnsignedInterval(0, 100)
    u2 = UnsignedInterval(50, 200)
    
    print(f"u1 = {u1}")
    print(f"u2 = {u2}")
    print(f"u1 + u2 = {u1 + u2}")
    print(f"u2 - u1 = {u2 - u1}")
    print(f"u1 * u2 = {u1 * u2}")
    
    # Underflow test
    u_small = UnsignedInterval(0, 10)
    u_large = UnsignedInterval(20, 30)
    print(f"\nUnderflow test: {u_small} - {u_large} = {u_small - u_large}")


def test_loop_widening():
    """Demonstrate widening for loop analysis"""
    print("\n=== Loop Analysis with Widening ===\n")
    print("Analyzing: i = 0; while(i < 1000000) i++;")
    
    i = SignedInterval(0, 0)
    print(f"\nInitial: i = {i}")
    
    for iteration in range(1, 8):
        i_next = i + SignedInterval(1, 1)
        print(f"Iteration {iteration}: {i} + [1,1] = {i_next}")
        if iteration == 3:
            print("  -> Applying widening")
            i = i.widen(i_next)
        else:
            i = i_next
        print(f"  Result: {i}")
    
    print(f"\nFinal: i ∈ {i}")


def test_division_by_zero():
    """Test detecting potential division by zero"""
    print("\n=== Division by Zero Detection ===\n")
    
    safe = SignedInterval(1, 10)
    print(f"Denominator: {safe}")
    print(f"Can be zero? {0 >= safe.low and 0 <= safe.high}")
    print("Status: SAFE\n")
    
    risky = SignedInterval(-5, 5)
    print(f"Denominator: {risky}")
    print(f"Can be zero? {0 >= risky.low and 0 <= risky.high}")
    print("Status: UNSAFE")
    
    # Refine with meet
    refined = risky.meet(SignedInterval(1, math.inf))
    print(f"\nAfter meet with [1,∞]: {refined}")
    print(f"Can be zero? {0 >= refined.low and 0 <= refined.high}")


def test_soundness():
    """Test soundness properties"""
    print("\n=== Soundness Tests ===\n")
    
    # Test abstraction
    concrete = [10, 15, 12]
    abstract = SignedInterval.of(*concrete)
    print(f"Concrete values: {concrete}")
    print(f"Abstract: {abstract}")
    print(f"All values covered? {all(abstract.low <= v <= abstract.high for v in concrete)}")
    
    # Test operation soundness
    a, b = 7, 3
    abs_a = SignedInterval(7, 7)
    abs_b = SignedInterval(3, 3)
    concrete_sum = a + b
    abstract_sum = abs_a + abs_b
    print(f"\nConcrete: {a} + {b} = {concrete_sum}")
    print(f"Abstract: {abs_a} + {abs_b} = {abstract_sum}")
    print(f"Sound? {abstract_sum.low <= concrete_sum <= abstract_sum.high}")


def test_three_valued_logic():
    """Test 3-valued logic truth tables"""
    print("\n=== 3-Valued Logic Truth Tables ===\n")
    
    print("AND Truth Table:")
    print("  A │ B │ A∧B")
    print("────┼───┼────")
    vals = [("0", "0"), ("0", "1"), ("0", "⊥"), 
            ("1", "0"), ("1", "1"), ("1", "⊥"),
            ("⊥", "0"), ("⊥", "1"), ("⊥", "⊥")]
    
    for a, b in vals:
        bf_a = Bitfield(tuple([a]), 1)
        bf_b = Bitfield(tuple([b]), 1)
        result = (bf_a & bf_b).bits[0]
        print(f"  {a} │ {b} │ {result}")
    
    print("\nOR Truth Table:")
    print("  A │ B │ A∨B")
    print("────┼───┼────")
    for a, b in vals:
        bf_a = Bitfield(tuple([a]), 1)
        bf_b = Bitfield(tuple([b]), 1)
        result = (bf_a | bf_b).bits[0]
        print(f"  {a} │ {b} │ {result}")


if __name__ == "__main__":
    print("=" * 70)
    print("  Machine Word Abstract Domains - Test Suite")
    print("=" * 70)
    
    test_bitfield_operations()
    test_signed_intervals()
    test_unsigned_intervals()
    test_loop_widening()
    test_division_by_zero()
    test_soundness()
    test_three_valued_logic()
    
    print("\n" + "=" * 70)
    print("  All tests completed")
    print("=" * 70 + "\n")
