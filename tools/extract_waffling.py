# -*- coding: utf-8 -*-
"""Waffling60-DB switch layout extraction.

Reads the drill file of the solder waffling60-DB PCB and prints the key
positions in 19.05 mm units (origin = the PCB's bottom-left corner).
Used to verify the case/plate layout matches the PCB the user owns.
Run:  python tools/extract_waffling.py <RoundHoles.TXT>
"""
import json
import os
import sys

UNIT = 19.05


def parse_drill(path, xoff=0.0, yoff=0.0):
    tools = {}
    cur = None
    x = y = 0.0
    out = []
    for line in open(path):
        s = line.strip()
        if s.startswith("T") and "C" in s and s[1].split("F")[0].isdigit():
            head, dia = s.split("C")
            tools[int(head[1:].split("F")[0])] = float(dia)
            continue
        if s.startswith("T") and s[1:].isdigit():
            cur = int(s[1:])
            continue
        if s[:1] in ("X", "Y") and cur is not None:
            for part in s.replace("X", " X").replace("Y", " Y").split():
                v = int(part[1:]) / 10000.0
                if part[0] == "X":
                    x = v
                else:
                    y = v
            out.append((x - xoff, y - yoff, tools.get(cur)))
    return out


def main():
    p = sys.argv[1]
    holes = parse_drill(p)
    sw = [h for h in holes if abs(h[2] - 1.5) < 0.01]
    x0 = min(h[0] for h in sw)
    y0 = min(h[1] for h in sw)
    # Waffling60: the grid origin sits 0.375 above the min row and 0.97 right of min x
    ox, oy = 0.97, 0.375
    rows = {}
    for x, y, d in holes:
        if abs(d - 1.5) > 0.01:
            continue
        iu = round((x - x0 - ox) / UNIT, 3)
        ju = round((y - y0 - oy) / UNIT, 3)
        rows.setdefault(ju, []).append(iu)
    out = {"keys": [], "stabs": []}
    for j in sorted(rows):
        xs = sorted(rows[j])
        out["keys"].append({"row_units": j, "switch_x_units": xs})
    for x, y, d in holes:
        if abs(d - 1.7) < 0.01:
            out["stabs"].append([round((x - x0 - ox) / UNIT, 3), round((y - y0 - oy) / UNIT, 3)])
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
