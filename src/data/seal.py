"""Seal (or verify) a data folder with MD5 checksums; contents are hashed, never parsed.

Seal:   python -I src/data/seal.py seal   <folder> <checksum file>
Verify: python -I src/data/seal.py verify <checksum file>
"""
import glob
import hashlib
import os
import sys


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def seal(folder, out):
    files = sorted(glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True))
    with open(out, "w") as f:
        for p in files:
            f.write(f"{md5(p)} *{p.replace(os.sep, '/')}\n")
    print(f"sealed {len(files)} files in {out}")


def verify(checks):
    bad = 0
    lines = [x for x in open(checks).read().splitlines() if x.strip()]
    for line in lines:
        digest, path = line.split(" *", 1)
        if not os.path.exists(path) or md5(path) != digest:
            print("MISMATCH", path)
            bad += 1
    print(f"{len(lines) - bad}/{len(lines)} checksums OK")
    return bad == 0


if __name__ == "__main__":
    if sys.argv[1] == "seal":
        seal(sys.argv[2], sys.argv[3])
    else:
        sys.exit(0 if verify(sys.argv[2]) else 1)
