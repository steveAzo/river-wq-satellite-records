"""Derives src/p3v3/frame3.py from the frozen src/p3/frame2.py (Phase 2, integrity study). Adds module settings CRCB (message check
bytes: 2 = CRC-16, 3 = CRC-24) and RECCRC (a CRC-32 over the coded record, stored in the last 32 bits of the last record unit, or in an
extra unit when that unit has no room). Run from Paper3/: python -I src/p3v3/patch_frame3.py"""
s = open("src/p3/frame2.py", encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('"""Frame version 2 codec', '"""Integrity-study variant of the frame version 2 codec (derived from src/p3/frame2.py by src/p3v3/patch_frame3.py; DEVELOPMENT ONLY).\nOriginal header: Frame version 2 codec')
rep("from . import frame, rs\nfrom .frame import BitReader, BitWriter, crc16\n",
    "import zlib\n\nfrom p3 import frame, rs\nfrom p3.frame import BitReader, BitWriter, crc16\n\nCRCB = 2          # message check bytes: 2 = CRC-16, 3 = CRC-24\nRECCRC = False    # record-level CRC-32 inside the coded record\n\n\n"
    "def crc24(data, crc=0xB704CE):\n    \"\"\"CRC-24 (poly 0x864CFB, as in OpenPGP).\"\"\"\n    for byte in data:\n        crc ^= byte << 16\n        for _ in range(8):\n            crc = (crc << 1) ^ 0x864CFB if crc & 0x800000 else crc << 1\n            crc &= 0xFFFFFF\n    return crc\n\n\n"
    "def msg_crc(data):\n    return crc16(data) if CRCB == 2 else crc24(data)\n\n\n"
    "def rec_check(units):\n    \"\"\"CRC-32 over the units with the last 4 bytes zeroed.\"\"\"\n    b = b\"\".join(bytes(u) for u in units)\n    return zlib.crc32(b[:-4] + bytes(4))\n")
rep("    used = 16 + (8 + 8 * witness_bytes if witness_bytes else 0)", "    used = 8 * CRCB + (8 + 8 * witness_bytes if witness_bytes else 0)")
# record check in encode_record_units
rep("        units.append(_bits_to_bytes(w.bits, record_bits // 8))\n    return units\n",
    "        used_bits = len(w.bits)\n        units.append(_bits_to_bytes(w.bits, record_bits // 8))\n"
    "    if RECCRC:\n        if used_bits + 32 > record_bits:\n            units.append(_bits_to_bytes([0] * 3, record_bits // 8))      # an empty unit that carries the check\n"
    "        chk = rec_check(units)\n        units[-1] = bytes(units[-1][:-4]) + chk.to_bytes(4, \"big\")\n    return units\n")
rep("        crc = crc16(bytes(head) + bytes(rest))\n        msgs.append(bytes(head) + bytes([crc >> 8, crc & 0xFF]) + bytes(rest))",
    "        crc = msg_crc(bytes(head) + bytes(rest))\n        msgs.append(bytes(head) + crc.to_bytes(CRCB, \"big\") + bytes(rest))")
rep("    assert payload == HEADER_BYTES + BODY_BYTES\n", "    assert payload == HEADER_BYTES + BODY_BYTES\n")
rep("    if len(raw) != HEADER_BYTES + BODY_BYTES:\n        return None\n    head, crc, rest = raw[:3], (raw[3] << 8) | raw[4], raw[5:]\n    if crc16(bytes(head) + bytes(rest)) != crc:",
    "    if len(raw) != HEADER_BYTES + BODY_BYTES:\n        return None\n    head, crc, rest = raw[:3], int.from_bytes(raw[3:3 + CRCB], \"big\"), raw[3 + CRCB:]\n    if msg_crc(bytes(head) + bytes(rest)) != crc:")
rep("            units = rs.decode({i: recs[i] for i in idxs[:K]}, K, max(Qmax, K + 1))\n",
    "            units = rs.decode({i: recs[i] for i in idxs[:K]}, K, max(Qmax, K + 1))\n"
    "            if RECCRC and rec_check(units) != int.from_bytes(bytes(units[-1][-4:]), \"big\"):\n                out.record_rejected = True\n                units = None\n")
rep("            if corroborate and len(recs) > K:" + chr(10) + "                full = rs.encode(units, max(Qmax, K + 1))",
    "            if corroborate and len(recs) > K and units is not None:" + chr(10) + "                full = rs.encode(units, max(Qmax, K + 1))")
open("src/p3v3/frame3.py", "w", encoding="utf-8").write(s)
print("written")
