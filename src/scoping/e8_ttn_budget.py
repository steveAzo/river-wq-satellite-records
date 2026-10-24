"""E8: daily uplink byte budget under the TTN fair-use policy (30 s airtime/device/day), per spreading factor.

LoRa time on air (Semtech AN1200.13 / SX1276 datasheet): BW 125 kHz, CR 4/5, explicit header, CRC on,
8-symbol preamble, low-data-rate optimisation for SF11-12. LoRaWAN overhead 13 B (MHDR 1, FHDR 7, FPort 1,
MIC 4). EU868 maximum application payload per data rate (RP002-1.0.3): SF7-9 222 B (SF9: 115 B; using
the conservative RP002 values below), SF10 51 B, SF11 51 B, SF12 51 B.
Compared with a 4-parameter node sampling every 10 min (144 cycles/day, 2 B per value + 1 B slot index
per cycle = 9 B/cycle, 1,296 B/day). Run from Paper3/: python -I src/scoping/e8_ttn_budget.py
"""
import math

MAXPL = {7: 222, 8: 222, 9: 115, 10: 51, 11: 51, 12: 51}


def toa(pl_app, sf, bw=125e3, cr=1, preamble=8):
    pl = pl_app + 13
    de = 1 if sf >= 11 else 0
    ts = (2 ** sf) / bw
    n = 8 + max(math.ceil((8 * pl - 4 * sf + 28 + 16) / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return (preamble + 4.25) * ts + n * ts


need = 144 * 9
print(f"Node need: {need} B/day (4 params, 10 min). TTN fair use: 30 s airtime/day.")
print("SF | max payload B | airtime per full frame s | frames/day | bytes/day | share of need")
for sf in range(7, 13):
    t = toa(MAXPL[sf], sf)
    frames = math.floor(30 / t)
    print(f"{sf:2d} | {MAXPL[sf]:3d} | {t:6.3f} | {frames:4d} | {frames*MAXPL[sf]:6d} | {frames*MAXPL[sf]/need:5.2f}")
