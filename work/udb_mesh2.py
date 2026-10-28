import re, sys
from collections import Counter, defaultdict
txt = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
pts = {}
for m in re.finditer(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*\)\s*\)", txt):
    pts[len(pts)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
z0 = [(x, y) for x, y, z in pts.values() if abs(z) < 0.01]
print("z=0 pts", len(z0))
xs = sorted(set(round(x, 2) for x, y in z0)); ys = sorted(set(round(y, 2) for x, y in z0))
print("x", xs[:12], "...", xs[-12:]); print("y", ys[:12], "...", ys[-12:])
# USB-C connector-ish: the connector centered on X, at min y
for x in xs:
    col = [y for xx, y in z0 if abs(xx - x) < 0.01]
    print(round(x,2), round(min(col),2), round(max(col),2), len(col))
