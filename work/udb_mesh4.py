import re, sys
from collections import Counter, defaultdict
txt = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
pts = {}
for m in re.finditer(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*\)\s*\)", txt):
    pts[len(pts)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
# For every x column, list y range for the top PCB surface (largest z with many pts)
rows = defaultdict(list)
for x, y, z in pts.values():
    if -60 < y < -4:
        rows[round(x, 2)].append((y, z))
for x in sorted(rows)[:20] + sorted(rows)[-10:]:
    ys = sorted(rows[x])
    print(x, "ymin", round(ys[0][0],2), "ymax", round(ys[-1][0],2), "zmin", round(min(z for y, z in ys),2), "zmax", round(max(z for y, z in ys),2), len(ys))
