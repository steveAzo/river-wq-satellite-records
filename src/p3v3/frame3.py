"""Integrity-study variant of the frame version 2 codec (derived from src/p3/frame2.py by src/p3v3/patch_frame3.py; DEVELOPMENT ONLY).
Original header: Frame version 2 codec (revision 2, Step 6b). Specification: docs/FRAME_SPEC_V2.md; bit budget: src/p3/capacity.py.

One record day per block. Message = header (3 bytes) + body (20 bytes):
  header: version 2 | block day mod 64 | message index | K | coded | witness-group flag        (24 bits)
  body:   CRC-16 (over header and the rest of the body) | [descriptor | witness symbol] | record symbol
Record data unit: segment count 2 | segment (day offset 6, first position 10, count 3, last 1, bound 1, values of
parameter 2 + slot 9 + code 13) | hosted flag 1 [mask 5, 13-bit codes] | zero padding. A witness group is a systematic
Reed-Solomon code (GF(2^8)) of k_w units over the same messages as the record.
Witness codes are 13-bit quantiser codes in mask order: DOmin, pHmin, pHmax, Tmax, ECa, ECb (ECa and ECb together are the
conductance rate pair, bit 4 of the mask).
"""
from dataclasses import dataclass, field

import zlib

from p3 import frame, rs
from p3.frame import BitReader, BitWriter, crc16

CRCB = 2          # message check bytes: 2 = CRC-16, 3 = CRC-24
RECCRC = False    # record-level CRC-32 inside the coded record


def crc24(data, crc=0xB704CE):
    """CRC-24 (poly 0x864CFB, as in OpenPGP)."""
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc = (crc << 1) ^ 0x864CFB if crc & 0x800000 else crc << 1
            crc &= 0xFFFFFF
    return crc


def msg_crc(data):
    return crc16(data) if CRCB == 2 else crc24(data)


def rec_check(units):
    """CRC-32 over the units with the last 4 bytes zeroed."""
    b = b"".join(bytes(u) for u in units)
    return zlib.crc32(b[:-4] + bytes(4))

VERSION2 = 2
HEADER_BYTES = 3
BODY_BYTES = 20
WITNESS_CODES = ("DOmin", "pHmin", "pHmax", "Tmax", "ECa", "ECb")
MASK_OF = {"DOmin": 0, "pHmin": 1, "pHmax": 2, "Tmax": 3, "ECa": 4, "ECb": 4}
OBJECT_CODES = {"DO": ("DOmin",), "pH": ("pHmin", "pHmax"), "T": ("Tmax",), "EC": ("ECa", "ECb")}


def codes_of_mask(mask):
    """Witness code names present for a 5-bit mask, in mask order."""
    out = []
    for name in WITNESS_CODES:
        if mask >> MASK_OF[name] & 1:
            out.append(name)
    return out


def mask_of(names):
    m = 0
    for n in names:
        m |= 1 << MASK_OF[n]
    return m


def _bits_to_bytes(bits, nbytes):
    w = BitWriter()
    w.bits = list(bits)
    return w.to_bytes(nbytes)


def _witness_bits(names, codes):
    w = BitWriter()
    for n in codes_of_mask(mask_of(names)):
        w.put(int(codes[n]), 13)
    return w.bits


# ------------------------------------------------------------------ record unit
def record_unit_bits(witness_bytes):
    """Bits of the record symbol: body minus CRC, minus descriptor and witness symbol when a layered group exists."""
    used = 8 * CRCB + (8 + 8 * witness_bytes if witness_bytes else 0)
    return 8 * BODY_BYTES - used


def values_per_unit(record_bits):
    return (record_bits - 24) // 24


def encode_record_units(values, bound, record_bits, hosted_codes=None):
    """values: planned [(param, slot, code)]. Returns the list of record data units (bytes). The hosted witness codes
    (dict name -> code) go into the last unit's padding."""
    vpu = values_per_unit(record_bits)
    if vpu < 1:
        raise ValueError("record symbol too small")
    chunks = [values[i:i + vpu] for i in range(0, len(values), vpu)] or [[]]
    units = []
    for u, chunk in enumerate(chunks):
        w = BitWriter()
        w.put(1 if chunk else 0, 2)
        if chunk:
            w.put(0, 6)
            w.put(u * vpu, 10)
            w.put(len(chunk), 3)
            w.put(int(u == len(chunks) - 1), 1)
            w.put(int(bound), 1)
            for p, slot, code in chunk:
                w.put(frame.PARAM_CODE[p], 2)
                w.put(slot, 9)
                w.put(int(code), 13)
        hosted = hosted_codes and u == len(chunks) - 1
        w.put(int(bool(hosted)), 1)
        if hosted:
            names = [n for n in WITNESS_CODES if n in hosted_codes]
            w.put(mask_of(names), 5)
            for n in codes_of_mask(mask_of(names)):
                w.put(int(hosted_codes[n]), 13)
        used_bits = len(w.bits)
        units.append(_bits_to_bytes(w.bits, record_bits // 8))
    if RECCRC:
        if used_bits + 32 > record_bits:
            units.append(_bits_to_bytes([0] * 3, record_bits // 8))      # an empty unit that carries the check
        chk = rec_check(units)
        units[-1] = bytes(units[-1][:-4]) + chk.to_bytes(4, "big")
    return units


def parse_record_unit(unit):
    """-> (segments [(first, last, bound, values)], hosted {name: code}) or None if malformed."""
    r = BitReader(unit)
    try:
        segs = []
        for _ in range(r.get(2)):
            off, first, cnt, last, bound = r.get(6), r.get(10), r.get(3), r.get(1), r.get(1)
            vals = [(frame.PARAM_NAME[r.get(2)], r.get(9), r.get(13)) for _ in range(cnt)]
            segs.append((first, bool(last), bool(bound), vals))
        hosted = {}
        if r.get(1):
            mask = r.get(5)
            for n in codes_of_mask(mask):
                hosted[n] = r.get(13)
        return segs, hosted
    except ValueError:
        return None


# ------------------------------------------------------------------ block
@dataclass
class Block:
    block_day: int
    Q: int
    K: int
    coded: bool
    kw: int
    messages: list = field(default_factory=list)


def build_block(values, bound, block_day, Q, layered=None, kw=1, hosted=None, payload=23):
    """One record day -> Q messages (bytes). layered: {name: code} witness codes in a layered group of kw units;
    hosted: {name: code} witness codes in the padding of the last record unit."""
    assert payload == HEADER_BYTES + BODY_BYTES
    wb = 0
    wunits = []
    if layered:
        names = [n for n in WITNESS_CODES if n in layered]
        bits = _witness_bits(names, layered)
        sym_bits = -(-len(bits) // kw)
        wb = -(-sym_bits // 8)
        padded = bits + [0] * (8 * wb * kw - len(bits))
        wunits = [list(_bits_to_bytes(padded[j * 8 * wb:(j + 1) * 8 * wb], wb)) for j in range(kw)]
        if kw > Q:
            raise ValueError("kw exceeds the quota")
    rbits = record_unit_bits(wb)
    runits = encode_record_units(values, bound, rbits, hosted)
    K = len(runits)
    coded = K <= Q
    rsyms = rs.encode([list(u) for u in runits], Q) if coded and Q > K else [list(u) for u in runits][:Q]
    wsyms = rs.encode(wunits, Q) if layered and Q > kw else wunits
    msgs = []
    for i in range(Q):
        head = bytearray()
        w = BitWriter()
        w.put(VERSION2, 2)
        w.put(block_day % frame.DAY_MOD, 6)
        w.put(i, 7)
        w.put(min(K, 127), 7)
        w.put(int(coded), 1)
        w.put(int(bool(layered)), 1)
        head = w.to_bytes(HEADER_BYTES)
        rest = bytearray()
        if layered:
            rest += bytes([(kw << 5) | mask_of(names)])
            rest += bytes(wsyms[i] if i < len(wsyms) else [0] * wb)
        rest += bytes(rsyms[i]) if i < len(rsyms) else bytes(rbits // 8)
        crc = msg_crc(bytes(head) + bytes(rest))
        msgs.append(bytes(head) + crc.to_bytes(CRCB, "big") + bytes(rest))
    return Block(block_day, Q, K, coded, kw if layered else 0, msgs)


@dataclass
class Decoded:
    values: dict = field(default_factory=dict)      # planned position -> (param, slot, code)
    bound: bool = False
    last_pos: int = None
    witness: dict = field(default_factory=dict)     # name -> code (layered and hosted, after corroboration)
    accepted: int = 0                               # messages that passed the CRC
    crc_failed: int = 0
    record_rejected: bool = False                   # corroboration found an inconsistency
    witness_rejected: bool = False


def _parse_message(raw):
    if len(raw) != HEADER_BYTES + BODY_BYTES:
        return None
    head, crc, rest = raw[:3], int.from_bytes(raw[3:3 + CRCB], "big"), raw[3 + CRCB:]
    if msg_crc(bytes(head) + bytes(rest)) != crc:
        return None
    r = BitReader(head)
    version, day, idx, K, coded, wflag = r.get(2), r.get(6), r.get(7), r.get(7), r.get(1), r.get(1)
    if version != VERSION2:
        return None
    return {"day": day, "i": idx, "K": K, "coded": bool(coded), "wflag": bool(wflag), "rest": bytes(rest)}


def receive(raws, corroborate=True, n_of=None):
    """Messages of one block (any subset, any order, duplicates allowed) -> Decoded. Only CRC-valid messages are used.
    n_of: site profile {param: readings per day}; when given, the sanity rule applies: every decoded value must lie inside
    the profile (slot below the channel's length) and the planned positions must be strictly increasing in (parameter, slot);
    a violation rejects the record. Witness codes that flag a censored reading (0 or 8191) are always rejected."""
    out = Decoded()
    try:
        _receive_body(raws, corroborate, out)
    except (ValueError, IndexError, KeyError, ZeroDivisionError):
        out.values, out.last_pos, out.bound, out.witness = {}, None, False, {}      # a CRC-valid garbage block never crashes
        out.record_rejected = out.witness_rejected = True
    _sanity(out, n_of)
    return out


def _receive_body(raws, corroborate, out):
    msgs = []
    for raw in raws:
        m = _parse_message(raw)
        if m is None:
            out.crc_failed += 1
        else:
            msgs.append(m)
    out.accepted = len(msgs)
    if not msgs:
        return
    # a block is identified by its header fields; keep the most common identity
    ids = {}
    for m in msgs:
        ids.setdefault((m["day"], m["K"], m["coded"], m["wflag"]), []).append(m)
    ident, group = max(ids.items(), key=lambda kv: len(kv[1]))
    if len(ids) > 1 and corroborate:
        out.record_rejected = out.witness_rejected = True      # accepted messages disagree on the block identity
        return
    day, K, coded, wflag = ident
    byidx = {}
    for m in group:
        first_seen = byidx.setdefault(m["i"], m)
        if corroborate and first_seen["rest"] != m["rest"]:
            # two CRC-valid copies of one message disagree: one is corrupt, and which one is unknown (order must not decide)
            out.record_rejected = out.witness_rejected = True
            return
    Q = max(byidx) + 1 if byidx else 0
    wb = 0
    kw = mask = 0
    if wflag:
        first = next(iter(byidx.values()))["rest"]
        kw, mask = first[0] >> 5, first[0] & 31
        if not 1 <= kw <= 6 or mask == 0:
            raise ValueError("invalid witness descriptor")
        nbits = 13 * len(codes_of_mask(mask))
        sym_bits = -(-nbits // kw)
        wb = -(-sym_bits // 8)
        for m in byidx.values():
            if (m["rest"][0] >> 5, m["rest"][0] & 31) != (kw, mask) and corroborate:
                # the descriptor fixes the byte offset of the record symbol, so the whole block is unreliable
                out.record_rejected = out.witness_rejected = True
                return
    # ---- record
    recs = {i: list(m["rest"][(1 + wb) if wflag else 0:]) for i, m in byidx.items()}
    units = None
    if coded:
        if len(recs) >= K:
            Qmax = max(max(recs) + 1, K)
            idxs = sorted(recs)
            units = rs.decode({i: recs[i] for i in idxs[:K]}, K, max(Qmax, K + 1))
            if RECCRC and rec_check(units) != int.from_bytes(bytes(units[-1][-4:]), "big"):
                out.record_rejected = True
                units = None
            if corroborate and len(recs) > K and units is not None:
                full = rs.encode(units, max(Qmax, K + 1))
                if any(full[i] != recs[i] for i in recs):
                    out.record_rejected = True
                    units = None
    unit_by_index = {}
    if units is not None:
        unit_by_index = {j: bytes(u) for j, u in enumerate(units)}
    elif not out.record_rejected:
        unit_by_index = {i: bytes(recs[i]) for i in recs if i < K}
    for j, u in unit_by_index.items():
        p = parse_record_unit(u)
        if p is None:
            continue
        segs, hosted = p
        for first, last, bound, vals in segs:
            out.bound = out.bound or bound
            for t, v in enumerate(vals):
                out.values[first + t] = v
            if last:
                out.last_pos = first + len(vals) - 1
        if hosted and not out.record_rejected:
            out.witness.update(hosted)
    # ---- layered witnesses
    if wflag and not out.witness_rejected:
        wsym = {i: list(m["rest"][1:1 + wb]) for i, m in byidx.items()}
        wunits = None
        if len(wsym) >= kw:
            Qmax = max(max(wsym) + 1, kw)
            idxs = sorted(wsym)
            wunits = rs.decode({i: wsym[i] for i in idxs[:kw]}, kw, max(Qmax, kw + 1)) if Qmax > kw or kw > 0 else None
            if corroborate and len(wsym) > kw and wunits is not None:
                full = rs.encode(wunits, max(Qmax, kw + 1))
                if any(full[i] != wsym[i] for i in wsym):
                    out.witness_rejected = True
                    wunits = None
        if wunits is not None:
            bits = [b for u in wunits for byte in u for b in [(byte >> (7 - t)) & 1 for t in range(8)]]
            r = BitReader(bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits) - len(bits) % 8, 8)))
            for n in codes_of_mask(mask):
                out.witness[n] = r.get(13)


PARAM_ORDER = {"T": 0, "DO": 1, "pH": 2, "EC": 3}


def _sanity(out, n_of):
    if n_of is not None and out.values:
        prev, ok = None, True
        for pos in sorted(out.values):
            p, s, _code = out.values[pos]
            if p not in n_of or s >= n_of[p]:
                ok = False
                break
            key = (PARAM_ORDER[p], s)
            if prev is not None and key <= prev:
                ok = False
                break
            prev = key
        if not ok:
            out.values, out.last_pos, out.bound = {}, None, False
            out.record_rejected = True
    if any(c in (0, 8191) for c in out.witness.values()):
        out.witness = {}
        out.witness_rejected = True
