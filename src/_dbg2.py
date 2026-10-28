src = open("C:/Users/jguo121/Documents/F1-60 722/src/f1_60_722.py", encoding="utf-8").read()
exec(compile(src, "f1_60_722.py", "exec"))
from collections import Counter
def run(c):
    part = Part("T")
    polys = switch_hole_outlines()
    sk = build_sketch(part.root, [map_poly(p, 0.0) for p in polys])
    ar = Counter()
    for i in range(sk.profiles.count):
        p = sk.profiles.item(i)
        bb = p.boundingBox
        ar[round((bb.maxPoint.x - bb.minPoint.x)*10, 2)] += 1
    print("profile widths", ar.most_common(8))
    # small sketch far from origin
    for off in (0, 100, 200, 250, 258):
        sk2 = part.root.sketches.add(part.root.xYConstructionPlane)
        sk2.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(off*0.1, 0.5, 0), 0.7)
        prof = sk2.profiles.item(0)
        bb = prof.boundingBox
        print("circle at", off, "->", round(bb.minPoint.x*10,2), round(bb.maxPoint.x*10,2), round(bb.maxPoint.y*10,2))
