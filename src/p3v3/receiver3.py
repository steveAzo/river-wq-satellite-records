"""Version 3 hardened receiver (finding A5 of docs/REVIEW_FINDINGS_2026-11-09.md). New file; src/p3v3/frame3.py and the frozen
src/p3 code are unchanged.

Two changes against frame3.receive (and frame2.receive):
  1. Every exception raised while decoding a block, of ANY type, including in the sanity rule, rejects the record and the witnesses
     of that block; nothing escapes. frame3.receive catches ValueError, IndexError, KeyError, and ZeroDivisionError only, and runs
     the sanity rule outside its try block.
  2. Each raw message is checked on its own before decoding: an object that is not bytes-like or has the wrong length counts as a
     failed message (crc_failed), like a message that fails its CRC, and does not reject the other messages of the block.
On every list of byte strings (bytes, bytearray) on which frame3.receive returns, receive() returns the same Decoded
(tests/v3/test_receiver3.py checks this). Other objects (for example a list of integers) are failed messages here.
Not changed (reported as a limit, not fixed): a forged record value with a censored code (0 or 8191) passes the sanity rule,
because honest records carry such codes for censored readings; it removes that reading from every decision.
The receiver reads the frame settings (frame3.CRCB, frame3.RECCRC) at call time.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if os.path.join(HERE, "..") not in sys.path:
    sys.path.insert(0, os.path.join(HERE, ".."))
import frame3 as f3  # noqa: E402

Decoded = f3.Decoded
MESSAGE_BYTES = f3.HEADER_BYTES + f3.BODY_BYTES


def _as_message(raw):
    """bytes of one raw message, or None when the object is not a byte string of the message length."""
    try:
        b = bytes(raw) if isinstance(raw, (bytes, bytearray, memoryview)) else None
    except Exception:                       # noqa: BLE001  (a broken buffer object)
        return None
    if b is None or len(b) != MESSAGE_BYTES:
        return None
    return b


def _reject(out):
    out.values, out.last_pos, out.bound, out.witness = {}, None, False, {}
    out.record_rejected = out.witness_rejected = True


def receive(raws, corroborate=True, n_of=None):
    """Messages of one block (any subset, any order, duplicates allowed) -> Decoded. Same rules as frame3.receive; never raises
    for any input that can be iterated (a non-iterable `raws` gives an empty, rejected Decoded)."""
    out = Decoded()
    try:
        msgs, bad = [], 0
        for raw in raws:
            b = _as_message(raw)
            if b is None:
                bad += 1
            else:
                msgs.append(b)
    except Exception:                       # noqa: BLE001  (raws is not iterable, or its iterator fails)
        _reject(out)
        return out
    try:
        f3._receive_body(msgs, corroborate, out)
        f3._sanity(out, n_of)
    except Exception:                       # noqa: BLE001  (a CRC-valid garbage block never crashes, whatever the error type)
        accepted, failed = out.accepted, out.crc_failed
        _reject(out)
        out.accepted, out.crc_failed = accepted, failed
    out.crc_failed += bad
    return out
