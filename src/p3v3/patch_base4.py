"""Derives src/p3v3/proto_base4.py from src/p3v3/proto_base3.py: the number of value slots per message (SLOTS) becomes a setting, so that the
slot model can be run for the frame with a CRC-24 per message (4 values per message instead of 5; docs/V3_DEV_RESULTS.md, Phase 2).
Designs supported: rec, heur, flags, flagsrec, hyb1, hyb2. DEVELOPMENT DATA ONLY.
Run from Paper3/: python -I src/p3v3/patch_base4.py"""
s = open("src/p3v3/proto_base3.py", encoding="utf-8").read()
NL = chr(10)


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep("from p3.proto_joint import ORDER, build_groups, heur_groups, obj_values, prepare_items  # noqa: E402",
    "from p3.proto_joint import ORDER, obj_values, prepare_items  # noqa: E402" + NL + NL + NL +
    "SLOTS = 5                                           # value slots per message; set from the command line" + NL + NL + NL +
    "def heur_groups(R, hard, present, spare_cap_fn):" + NL +
    '    """Hard objects in one layered group with k <= 2; easy ones in the spare slots of the record group (SLOTS per message)."""' + NL +
    "    hv = [v for o in ORDER if o in present and hard[o] for v in obj_values(o)]" + NL +
    "    if not hv:" + NL +
    "        cR, layered = SLOTS, []" + NL +
    "    else:" + NL +
    "        cw = min(SLOTS - 1, -(-len(hv) // 2))" + NL +
    "        cR, layered = SLOTS - cw, [(hv, cw)]" + NL +
    "    cap = spare_cap_fn(cR)" + NL +
    "    host = []" + NL +
    "    for o in ORDER:" + NL +
    "        if o in present and not hard[o] and len(obj_values(o)) <= cap - len(host):" + NL +
    "            host += obj_values(o)" + NL +
    "    return layered + [(R + host, cR)]")
rep('                    if dn in ("heur", "ex1"):' + NL + '                        g = build_groups("heur" if dn == "heur" else "ex1", it, Q, it["hard"], cache)' + NL,
    '                    if dn == "heur":' + NL +
    '                        Rh = [("R", p) for p in range(len(vals))]' + NL +
    '                        pres = [o for o in ORDER if o != "EC" or it["ew"] is not None]' + NL +
    '                        g = heur_groups(Rh, it["hard"], pres, lambda cR, V=len(vals): -(-V // cR) * cR - V)' + NL)
rep('                    elif dn == "randmix":' + NL + '                        g = build_groups("randmix", it, Q, items[perm[i]]["hard"], cache)' + NL + '                        mode = "coded"' + NL, "")
rep('                        g, mode = [([("R", p) for p in range(len(vals))], 5)], "coded"' + NL + '                    elif dn in ("tight50"',
    '                        g, mode = [([("R", p) for p in range(len(vals))], SLOTS)], "coded"' + NL + '                    elif dn in ("tight50"')
rep("                            cc = cR - (5 - FLAG_CAP)", "                            cc = cR - (SLOTS - FLAG_CAP)")
rep("<= spare_f(5) - len(host)", "<= spare_f(SLOTS) - len(host)")
rep("g[-1][1] - (5 - FLAG_CAP))]", "g[-1][1] - (SLOTS - FLAG_CAP))]")
rep("    global DESIGNS, FLAG_CAP, HEAVY" + NL + "    path, tag, outdir, DESIGNS, FLAG_CAP = args", "    global DESIGNS, FLAG_CAP, HEAVY, SLOTS" + NL + "    path, tag, outdir, DESIGNS, FLAG_CAP, SLOTS = args")
rep("[(p, tag, outdir, DESIGNS, FLAG_CAP) for p in paths]", "[(p, tag, outdir, DESIGNS, FLAG_CAP, SLOTS) for p in paths]")
rep("    global DESIGNS, FLAG_CAP, HEAVY" + NL + "    folder, tag = sys.argv[1], sys.argv[2]", "    global DESIGNS, FLAG_CAP, HEAVY, SLOTS" + NL + "    folder, tag = sys.argv[1], sys.argv[2]")
rep("    limit = int(sys.argv[6]) if len(sys.argv) > 6 else None", "    SLOTS = int(sys.argv[6])" + NL + "    assert all(d in (\"rec\", \"heur\", \"flags\", \"flagsrec\", \"hyb1\", \"hyb2\") for d in DESIGNS)" + NL + "    limit = int(sys.argv[7]) if len(sys.argv) > 7 else None")
rep('flag_cap={FLAG_CAP} seed', 'flag_cap={FLAG_CAP} slots={SLOTS} seed')
rep("<flag capacity> <outname> [sites]", "<flag capacity> <outname> <slots> [limit]")
open("src/p3v3/proto_base4.py", "w", encoding="utf-8").write(s)
print("written")
