src = open("C:/Users/jguo121/Documents/F1-60 722/src/f1_60_722.py", encoding="utf-8").read()
exec(compile(src, "f1_60_722.py", "exec"))
def run(c):
    part = Part("T")
    polys = [poly_rrect(PLATE_X0, PLATE_Y0, PLATE_X1, PLATE_Y1, 10.0)]
    lp = map_poly(polys, 0.0)
    print("npts", len(lp[0]), lp[0][:3], "origin", local_origin(polys))
    sk, sks = build_sketch(part.root, [lp], split=True)
    print("sketches", len(sks), "main profiles", sk.profiles.count, "main lines", sk.sketchCurves.sketchLines.count, "splines", sk.sketchCurves.sketchFittedSplines.count)
    p = sk.profiles.item(0)
    bb = p.boundingBox
    print("prof bb", round((bb.maxPoint.x-bb.minPoint.x)*10,2), round((bb.maxPoint.y-bb.minPoint.y)*10,2), "area", round(p.areaProperties().area*100,1))
