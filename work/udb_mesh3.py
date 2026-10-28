import re, sys
from collections import Counter
txt = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
pts = {}
for m in re.finditer(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*\)\s*\)", txt):
    pts[len(pts)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
zs = Counter(round(v[2], 2) for v in pts.values())
print(sorted(zs.items())[:6], sorted(zs.items())[-6:])
# board top plane: the z with the most points in the y range -60..-5
for target in (1.65, -6.25, -7.3, -7.9):
    sel = [(x, y) for x, y, z in pts.values() if abs(z - target) < 0.02 and -60 < y < -4]
    if sel:
        print(target, len(sel), "x", round(min(s[0] for s in sel),2), round(max(s[0] for s in sel),2), "y", round(min(s[1] for s in sel),2), round(max(s[1] for s in sel),2))
# connector body extents (the 8.94 x 3.21 thing near x=0)
sel = [(x, y, z) for x, y, z in pts.values() if -0.5 < x < 9.5 and -1.2 < y < 3.4]
print("connector x", min(s[0] for s in sel), max(s[0] for s in sel), "z", min(s[2] for s in sel), max(s[2] for s in sel))
