import adsk.core, adsk.fusion
src = open("C:/Users/jguo121/Documents/F1-60 722/src/f1_60_722.py", encoding="utf-8").read()
exec(compile(src, "f1_60_722.py", "exec"))
def run(c):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    root = des.rootComponent
    sk = root.sketches.add(root.xYConstructionPlane)
    L = sk.sketchCurves.sketchLines
    a, b, t = 135.0, 60.0, 0.15
    pts = [adsk.core.Point3D.create(x*0.1, y*0.1, 0) for x, y in ((-a, -b), (a, -b), (a, b), (-a, b))]
    for i in range(4):
        ln = L.addByTwoPoints(pts[i], pts[(i+1) % 4])
        print("line", round(ln.startSketchPoint.geometry.x*10,2), round(ln.startSketchPoint.geometry.y*10,2), "->", round(ln.endSketchPoint.geometry.x*10,2), round(ln.endSketchPoint.geometry.y*10,2))
    ext = root.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(t*0.1))
    body = ext.add(inp).bodies.item(0)
    print("vol", round(body.volume*1000,1))
    for d in (-100, 0, 100):
        s2 = root.sketches.add(root.xYConstructionPlane)
        s2.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(d*0.1, 0, 0), 0.7)
        inp = ext.createInput(s2.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.participantBodies = [body]
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(t*0.1))
        ext.add(inp)
        print(" cut at", d, "vol", round(body.volume*1000,1))
