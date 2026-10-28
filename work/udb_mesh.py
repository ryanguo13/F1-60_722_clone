import re, sys
from collections import Counter
txt = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
pts = {}
for m in re.finditer(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*\)\s*\)", txt):
    pts[len(pts)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
print("points", len(pts))
xs = [v[0] for v in pts.values()]; ys = [v[1] for v in pts.values()]; zs = [v[2] for v in pts.values()]
print("x", round(min(xs),2), round(max(xs),2), "y", round(min(ys),2), round(max(ys),2), "z", round(min(zs),2), round(max(zs),2))
cz = Counter(round(v,2) for v in zs)
print("z levels", cz.most_common(10))
