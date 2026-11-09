"""Bit budget of frame version 2 (revision 2, Step 6; docs/FRAME_SPEC_V2.md).

A message is 3 header bytes (not coded) and a 20-byte (160-bit) body:
  CRC-16 over the header and the rest of the body      16 bits   (one check per TRANSMITTED message, data or parity)
  witness descriptor (only if the header flag says a witness group is present)
                                                         8 bits   (k_w: 3 bits; presence mask DO, pHmin, pHmax, T, EC: 5 bits)
  witness symbol                                        ceil(ceil(13 x codes / k_w) / 8) bytes (Reed-Solomon works on bytes)
  record symbol (the rest, a whole number of bytes): segment count 2 + segment header 21 + hosted flag 1 + 24 bits per value
Witness data are 13-bit codes in mask order (DO min, pH min, pH max, T max, conductance rate pair = 2 codes); the slot of a
witness is not carried because no decision rule uses it. A group of k_w witness units is a systematic MDS code over the
same Q messages as the record.
"""
from math import ceil

BODY = 160
CRC = 16
WDESC = 8
SEG_OVERHEAD = 2 + 21 + 1                  # segment count, one segment header, hosted-witness flag
VALUE = 24
CODE = 13
CODES = {"DO": 1, "pH": 2, "T": 1, "EC": 2}


def witness_bits(objs):
    return CODE * sum(CODES[o] for o in objs)


def group_message_bits(objs, k):
    """Bits one message spends on a witness group of the given objects and dimension k (symbol rounded up to bytes)."""
    return WDESC + 8 * ceil(ceil(witness_bits(objs) / k) / 8)


def record_values_per_message(groups, other_bits=0):
    """Values of the record unit that fit in the rest of the body. groups: [(objects, k_w)]; other_bits: further fixed
    bits per message (for example the flags design)."""
    used = CRC + other_bits + sum(group_message_bits(o, k) for o, k in groups)
    return max(0, (BODY - used - SEG_OVERHEAD) // VALUE)


def spare_bits(values_in_last_unit, groups, other_bits=0):
    """Free bits in a record unit that holds `values_in_last_unit` values (room for hosted witnesses)."""
    used = CRC + other_bits + sum(group_message_bits(o, k) for o, k in groups)
    return BODY - used - SEG_OVERHEAD - VALUE * values_in_last_unit


def slot_model_values(c_w):
    """The prototype's model: each layered column costs one 24-bit value slot per message."""
    return 5 - c_w
