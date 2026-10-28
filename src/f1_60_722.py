# -*- coding: utf-8 -*-
"""F1-60 722 clone -- parametric Fusion 360 build script (WKL, 3D-print ready).

Parts (one document each, exported into `out/`):

  BOTTOM   bottom case, 7.22 deg typing angle, stainless-weight well (left
           hollow for later), uDB window in the rear wall, inner floor and
           eight bosses for 嘉立创-embedded M3 heat-set inserts
  TOP      top case: bezel, WKL blockers/slots, switch-pocket recess, flat
           strap over the rear carrying the two uDB M2 taps, eight M3
           clearance holes, outer walls that wrap over the seam
  PLATE    1.5 mm ANSI/WKL plate: paddle hooks on the two inner edges, uDB M2
           holes, PCB switch/led reliefs, Cherry stab slots

See docs/DESIGN.md for the derivation of every number.

Coordinates
-----------
"Layout space" (mm, Z up):
  x: 0..284.5   left -> right of the finished keyboard
  y: 0..94.5    front lip -> back edge
  z: plate top = 0; PCB top -5, PCB bottom -6.6, case floor -10.5
The keyboard's back row faces the case's printed BACK edge, i.e. the model's
+Y is the PCB's -y. A layout point maps to the BOTTOM part as

  model = (W - x, -z + (H - y) * tan(angle), (H - y) * cos(angle))

The front lip is flat on the print bed; the case only leans through its
profiles (walls stay printable). The same map is used for every part.
"""
import adsk.core
import adsk.fusion
import math
import os
import traceback

MM = 0.1
OUT = "C:/Users/jguo121/Documents/F1-60 722/out/"
REF = "C:/Users/jguo121/Documents/F1-60 722/ref/"

P = dict(
    W=284.5, H=94.5,
    angle=7.22,
    r_side=6.0, r_back=8.0,
    plate_t=1.5, plate_z0=-1.5,
    pcb_top=-5.0, pcb_bot=-6.6,
    floor_z=-10.5,
    deck_z=-16.0,
    top_bottom=-1.5,
    top_bottom_rear=-20.0,
    top_bottom_rear_r=4.0,
    rear_recess=6.0,
    lip_z=-5.0,
    top_lip_z=-9.0,
    side_wall=3.0, front_wall=3.0, rear_wall=3.0,
    pocket_x0=36.0, pocket_x1=246.375, pocket_y0=29.0, pocket_y1=86.0,
    pocket_z=-16.0, pocket_r=2.0,
    rear_recess_x0=36.0, rear_recess_x1=246.375,
    weight_x0=11.5, weight_x1=273.0, weight_y0=11.5, weight_y1=76.5, weight_r=3.0,
    db_w=18.0, db_h=16.5,
    db_y0=84.6, db_y1=89.5,
    db_dx=7.0, db_dy0=11.3, db_dy1=17.0,
    pad_x0=133.0, pad_x1=159.0, pad_y0=84.6, pad_y1=89.5,
    screw_inset=6.0, screw_y_bottom=6.0, screw_y_top=14.25,
    boss=8.0, insert_d=3.6, insert_len=6.0, screw_d=3.4, head_d=6.2, head_dz=1.8,
    pocket_tol=0.5,
    hook_gap=3.0, hook_top_leg=2.2, hook_bot_leg=3.2, hook_w=2.4, hook_web=2.0,
)

U = 19.05
KX0 = (P['W'] - 15 * U) / 2.0
KEY_Y = [13.8455, 32.8955, 51.9455, 71.0055, 85.2155]
PLATE_X0, PLATE_X1 = 5.825, 278.675
PLATE_Y0, PLATE_Y1 = 2.82, 91.68
EL = math.radians(P['angle'])
TAN = math.tan(EL)
COS = math.cos(EL)


# =====================================================================
# LAYOUT
# =====================================================================
def build_keys():
    rows = [
        [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1),
         (10, 1), (11, 1), (12, 2)],
        [(0, 1.5)] + [(1.5, 1)] * 10 + [(11.5, 1), (12.5, 1), (13.5, 1.5), (15.0, 1.5), (16.5, 1.5)],
        [(0, 1.75)] + [(1.75, 1)] * 9 + [(10.75, 1), (11.75, 1), (12.75, 2.25), (15.0, 1.5), (16.5, 1.5)],
        [(0, 2.25)] + [(2.25, 1)] * 7 + [(9.25, 1), (10.25, 1), (11.25, 1), (12.25, 1.75), (14.0, 2.75), (16.75, 1.25)],
        [(0, 1.25), (1.25, 1.25), (2.5, 1.25), (3.75, 6.25), (10.0, 1.25), (11.25, 1.25), (12.5, 1.25), (13.75, 1.25)],
    ]
    keys = []
    for r, row in enumerate(rows):
        x_left = KX0 - 0.125 * U + (1.25 * U if r in (1, 2, 3) else 0.0)
        for off, w in row:
            x0 = x_left + off * U
            yc = KEY_Y[r]
            keys.append(dict(x0=x0, x1=x0 + w * U, y0=yc - U / 2, y1=yc + U / 2, w=w, row=r))
    return keys


KEYS = build_keys()
STABS = [
    (1, 0.0, 2.25, 2.0),
    (2, 10.75, 2.25, 2.0),
    (3, 12.25, 2.75, 2.0),
    (4, 3.75, 6.25, 6.25),
]


def stab_holes_for(k):
    out = []
    for (row, off, kw, wire) in STABS:
        if row != k['row'] or abs(k['w'] - kw) > 1e-6:
            continue
        half = (wire - 1) * U / 2.0
        kc = (k['x0'] + k['x1']) / 2.0 + (0.2 if row == 3 else 0.0)
        out += [(kc - half, KEY_Y[row]), (kc + half, KEY_Y[row])]
    return out


def stab_holes():
    out = []
    for k in KEYS:
        out += stab_holes_for(k)
    return out


SPACE = [k for k in KEYS if k['row'] == 4 and abs(k['w'] - 6.25) < 1e-6][0]
DB_CX = (SPACE['x0'] + SPACE['x1']) / 2.0


def top_edge(x):
    """Layout y of the case's outer edge at layout x (rounded back corners)."""
    r = P['r_back']
    if x < r:
        return P['H'] - r + math.sqrt(max(0.0, r * r - (r - x) ** 2))
    if x > P['W'] - r:
        return P['H'] - r + math.sqrt(max(0.0, r * r - (x - (P['W'] - r)) ** 2))
    return P['H']


def bottom_edge(x):
    r = P['r_side']
    if x < r:
        return r - math.sqrt(max(0.0, r * r - (r - x) ** 2))
    if x > P['W'] - r:
        return r - math.sqrt(max(0.0, r * r - (x - (P['W'] - r)) ** 2))
    return 0.0


def screw_positions():
    """(x, y) layout positions of the eight M3 screws."""
    out = []
    for x in (P['screw_inset'], P['W'] - P['screw_inset']):
        out.append((x, bottom_edge(x) + P['screw_y_bottom']))
        out.append((x, top_edge(x) - P['screw_y_top']))
    return out


def db_centre_y():
    return (P['db_y0'] + P['db_y1']) / 2.0 + 0.25


# =====================================================================
# SHAPES (pure python, layout XY)
# =====================================================================
def poly_ul(x0, x1, y0, y1, r, side, n=6):
    """Rectangle with the two corners toward `side` rounded by a polygonal arc
    of radius r. The arc leaves the straight edge perpendicular (a handful of
    segments keeps Fusion's sketch solver happy at print scale)."""
    def arc(cx, cy, a0):
        pts = []
        for i in range(n + 1):
            a = a0 + (math.pi / 2) * i / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts
    if side == 'front':
        return ([(x0, y1), (x0, y0 + r)] + arc(x0 + r, y0 + r, math.pi) +
                arc(x1 - r, y0 + r, 1.5 * math.pi) + [(x1, y1)])
    return ([(x0, y0), (x0, y1 - r)] + arc(x0 + r, y1 - r, math.pi) +
            arc(x1 - r, y1 - r, 1.5 * math.pi) + [(x1, y0)])


def poly_rrect(x0, y0, x1, y1, r):
    r = max(0.0, min(r, (x1 - x0) / 2.0 - 0.001, (y1 - y0) / 2.0 - 0.001))
    k = 0.55 * r
    if r <= 0.01:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [
        (x0 + r, y0), (x1 - r, y0), (x1 - r + k, y0), (x1, y0 + r - k), (x1, y0 + r),
        (x1, y1 - r), (x1, y1 - r + k), (x1 - r + k, y1), (x1 - r, y1),
        (x0 + r, y1), (x0 + r - k, y1), (x0, y1 - r + k), (x0, y1 - r),
        (x0, y0 + r), (x0, y0 + r - k), (x0 + r - k, y0), (x0 + r, y0)]


def poly_circle(cx, cy, dia, n=None):
    r = dia / 2.0
    n = n or (48 if r > 2.0 else 24)
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def outline_polys(r_side, r_back):
    yr = P['H'] - P['rear_wall']
    return [poly_ul(0, P['W'], yr, P['H'], r_back, 'back'),
            poly_ul(0, P['W'], 0, yr, r_side, 'front')]


def map_pt(x, y, z):
    L = P['H'] - y
    return P['W'] - x, -z + L * TAN, L * COS


def merge_loops(polys, eps=1e-4):
    out = []
    for p in polys:
        loop = []
        for pt in p:
            if loop and abs(loop[-1][0] - pt[0]) < eps and abs(loop[-1][1] - pt[1]) < eps:
                continue
            loop.append(pt)
        while len(loop) > 2 and abs(loop[0][0] - loop[-1][0]) < eps and abs(loop[0][1] - loop[-1][1]) < eps:
            loop.pop()
        out += loop
    while len(out) > 2 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def local_origin(poly_xy, z):
    """Origin a sketch can be built around so Fusion's sketch geometry stays
    small (it rounds coordinates > 109 mm to a coarse grid). The mapped
    outline is a thin, long strip; centre it on its bounding-box centre in x
    and on its 3D centroid in y."""
    pts = merge_loops(poly_xy) if isinstance(poly_xy[0][0], (list, tuple)) else list(poly_xy)
    m = [map_pt(a, b, z) for (a, b) in pts]
    ox = (min(p[0] for p in m) + max(p[0] for p in m)) / 2.0
    oy = sum(p[1] for p in m) / len(m)
    return ox, oy


def map_poly(poly_xy, z, origin=None):
    if isinstance(poly_xy[0][0], (list, tuple)):
        poly_xy = merge_loops(poly_xy)
    pts = [map_pt(a, b, z) for (a, b) in poly_xy]
    if origin is None:
        ox, oy = local_origin(poly_xy, z)
    else:
        ox, oy = origin
    return [(p[0] - ox, p[1] - oy) for p in pts]


# =====================================================================
# FUSION HELPERS
# =====================================================================
def px(x, y, z=0.0):
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def vreal(v):
    return adsk.core.ValueInput.createByReal(v)


def new_doc(name):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        doc.name = name
    except Exception:
        pass
    des = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    return doc, des, des.rootComponent


def build_sketch(root, polys, at=(0.0, 0.0)):
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    for pts in polys:
        sp = []
        for p in pts:
            pt = sk.sketchPoints.add(px(p[0], p[1]))
            if sp and abs((sp[-1].geometry.x - pt.geometry.x) * 10) < 1e-4 and                     abs((sp[-1].geometry.y - pt.geometry.y) * 10) < 1e-4:
                continue
            sp.append(pt)
        if len(sp) > 2 and abs((sp[0].geometry.x - sp[-1].geometry.x) * 10) < 1e-4 and                 abs((sp[0].geometry.y - sp[-1].geometry.y) * 10) < 1e-4:
            sp.pop()
        for i in range(len(sp)):
            lines.addByTwoPoints(sp[i], sp[(i + 1) % len(sp)])
    sk.isComputeDeferred = False
    return sk


def move_bodies(root, bodies, dx=0.0, dy=0.0, dz=0.0):
    bodies = [b for b in bodies if b.isValid]
    if not bodies or (abs(dx) + abs(dy) + abs(dz) < 1e-9):
        return
    coll = adsk.core.ObjectCollection.create()
    for b in bodies:
        coll.add(b)
    mf = root.features.moveFeatures
    inp = mf.createInput2(coll)
    inp.defineAsTranslateXYZ(vreal(dx * MM), vreal(dy * MM), vreal(dz * MM), True)
    mf.add(inp)


def cut_z(root, polys, targets, z0, z1):
    """Cut `polys` between layout z0..z1: extrude a tool solid from z0 straight
    to z1 in ONE sketch region (union of all loops at the sketch level, so the
    boolean is a single tool), then boolean-cut it out."""
    z0, z1 = min(z0, z1), max(z0, z1)
    org = local_origin(polys, z0)
    polys = [map_poly(merge_loops(polys), z0, org)]
    sk = build_sketch(root, polys)
    profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
    profs = [p for p in profs if p.areaProperties().area * 100 > 1e-6]
    if not profs:
        return
    ext = root.features.extrudeFeatures
    inp = ext.createInput(profs[0], adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    h = abs(z1 - z0)
    inp.setDistanceExtent(False, vreal(h * MM))
    f = ext.add(inp)
    tool = f.bodies.item(0)
    move_bodies(root, [tool], org[0], org[1], z0)
    tg = [t for t in targets if t.isValid]
    coll = adsk.core.ObjectCollection.create()
    for t in tg:
        coll.add(t)
    cib = root.features.combineFeatures
    ci = cib.createInput(tool, coll)
    ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    ci.isKeepToolBodies = False
    cib.add(ci)
    try:
        if tool.isValid:
            tool.deleteMe()
    except Exception:
        pass


def _multi_input(ext, profs):
    inp = ext.createInput(profs[0], adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    return inp


def make_tool(root, polys, height):
    ext = root.features.extrudeFeatures
    tools = []
    for poly in polys:
        sk = build_sketch(root, [poly])
        if sk.profiles.count != 1:
            raise RuntimeError("tool loop gave %d profiles: %s" % (sk.profiles.count, poly[:3]))
        inp = ext.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, vreal(height * MM))
        f = ext.add(inp)
        for i in range(f.bodies.count):
            tools.append(f.bodies.item(i))
    return tools


def add_bodies(root, polys, z0, z1, name=None):
    org = local_origin(polys, z0)
    polys = [map_poly(merge_loops(polys), z0, org)]
    bs = make_tool(root, polys, abs(z1 - z0))
    move_bodies(root, bs, org[0], org[1], min(z0, z1))
    if name:
        for i, b in enumerate(bs):
            b.name = name if len(bs) == 1 else "%s_%02d" % (name, i + 1)
    return bs


def join(root, target, tools):
    tools = [t for t in tools if t.isValid and t != target]
    if not tools:
        return target
    try:
        coll = adsk.core.ObjectCollection.create()
        for t in tools:
            coll.add(t)
        cib = root.features.combineFeatures
        ci = cib.createInput(target, coll)
        ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        ci.isKeepToolBodies = False
        cib.add(ci)
    except Exception as ex:
        print("join failed (%s), falling back to separate bodies" % ex)
    return target


def slice_body(root, body, x):
    pl = adsk.core.Plane.create(px(x, 0, 0), adsk.core.Vector3D.create(1, 0, 0))
    try:
        s = adsk.fusion.TemporaryBRepManager.get().planeIntersection(body, pl)
    except Exception:
        return []
    pts = set()
    if s is not None:
        for i in range(s.edges.count):
            e = s.edges.item(i)
            for v in (e.startVertex, e.endVertex):
                if v:
                    p = v.geometry
                    pts.add((round(p.y * 10, 2), round(p.z * 10, 2)))
    return sorted(pts)


def bbox_mm(b):
    bb = b.boundingBox
    return [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                       bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]


def export_step(root, path):
    app = adsk.core.Application.get()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sty = app.exportManager.createSTEPExportOptions(path, root)
    app.exportManager.execute(sty)
    return path


def fillet_edges(root, body, picker, radius):
    edges = adsk.core.ObjectCollection.create()
    for i in range(body.edges.count):
        e = body.edges.item(i)
        if picker(e):
            edges.add(e)
    if edges.count == 0:
        return None
    fi = root.features.filletFeatures.createInput()
    fi.addConstantRadiusEdgeSet(edges, vreal(radius * MM), True)
    return root.features.filletFeatures.add(fi)


# =====================================================================
# PARTS
# =====================================================================
W, H = P['W'], P['H']
R_OUT = 3.0          # plan-view inner radius of walls
R_OUT_MAX = 8.0      # matches the back corner radius
R_DB = 0.8


def bottom_outline():
    return outline_polys(P['r_side'], P['r_back'])


def inner_outline(layer):
    """Inner face of the case walls at a height layer; `layer` in ('body','lip')."""
    if layer == 'lip':
        o = 0.15                      # the top's lip sits 0.15 outside the bottom's wall
        f, s, r = P['front_wall'] - o, P['side_wall'] - o, P['rear_wall'] - o
    else:
        f, s, r = P['front_wall'], P['side_wall'], P['rear_wall']
    rs = max(0.5, P['r_side'] - s) if layer == 'body' else max(0.5, P['r_side'] - s - 0.15)
    rb = max(0.5, P['r_back'] - r) if layer == 'body' else max(0.5, P['r_back'] - r - 0.15)
    yr = H - r
    xs0, xs1 = s, W - s
    return [poly_ul(xs0, xs1, yr, H - r, rb, 'back'), poly_ul(xs0, xs1, f, yr, rs, 'front')]


def y_floor_back(x_of_wall):
    """Where a wall's inner face is at layout x (rounded back corner aware)."""
    return top_edge(x_of_wall) - P['rear_wall']


def cut_circles(polys_xy, z, dia):
    pass


def build_bottom():
    doc, des, root = new_doc("BOTTOM")
    # 1. outer prism
    base = add_bodies(root, [map_poly(bottom_outline(), P['top_bottom'])], P['top_bottom'], P['floor_z'], "BOTTOM")
    body = base[0]
    if len(base) > 1:
        body = join(root, base[0], base[1:])
    body.name = "BOTTOM"
    # 2. cavity above the floor
    cav = inner_outline('body')
    cut_z(root, [map_poly(cav, P['floor_z'])], [body], P['top_bottom'] + 1.0, P['floor_z'])
    # 3. the bottom's rib (what the top rests on): front band and rear deck,
    #    everything not under the top's walls, from the deck level up to the seam plane
    rib = inner_outline('body')
    band = [poly_ul(rib[1][0][0], rib[1][-2][0], 0.0, H - P['rear_wall'], 0.0, 'front')]
    print("bottom", bbox_mm(body), round(body.volume * 1000, 1))
    return doc, des, root, body


def run(c=None):
    try:
        doc, des, root, body = build_bottom()
        print("slice x=40", slice_body(root, body, 40))
        print("slice x=142", slice_body(root, body, 142.25))
    except Exception:
        print(traceback.format_exc())


# =====================================================================
# PART BUILDERS
# =====================================================================
PLATE_SLOT_W = 7.2          # stab cut-out length along x (cherry: 7.0 + pocket room)
PLATE_SLOT_H = 2.8          # stab cut-out height around the centre line
HOOK_OVER = 22.0            # hook lip overhang past the switch cut-out edge


def keys_zone():
    """Corridor around the switch cut-outs (x/plate y extents)."""
    xs = [k['x0'] for k in KEYS] + [k['x1'] for k in KEYS]
    ys = [k['y0'] for k in KEYS] + [k['y1'] for k in KEYS]
    return min(xs) + HOOK_OVER, max(xs) - HOOK_OVER, min(ys) + 0.25, max(ys) - 0.25


def hook_profiles(kind):
    """Layout-XY outlines (closed) of the plate hooks on side `kind`.
    'left': x = keys_zone()[0] is the inner limit of the switch cut-outs."""
    x0, x1, y0, y1 = keys_zone()
    w = P['hook_w']
    t_top = P['hook_top_leg']
    t_bot = P['hook_bot_leg']
    if kind == 'left':
        a = PLATE_X0
        top = [(a, y0), (x0 - P['hook_gap'], y0), (x0 - P['hook_gap'], y0 + w), (a, y0 + w)]
        bot = [(a, y1 - w), (x0 - P['hook_gap'], y1 - w), (x0 - P['hook_gap'], y1), (a, y1)]
        lip_t = [(a, y0 + w), (x0 - P['hook_gap'], y0 + w), (x0 - P['hook_gap'], y0 + w + t_top), (a, y0 + w + t_top)]
        lip_b = [(a, y1 - w - t_bot), (x0 - P['hook_gap'], y1 - w - t_bot), (x0 - P['hook_gap'], y1 - w), (a, y1 - w)]
    else:
        a = PLATE_X1
        top = [(x1 + P['hook_gap'], y0), (a, y0), (a, y0 + w), (x1 + P['hook_gap'], y0 + w)]
        bot = [(x1 + P['hook_gap'], y1 - w), (a, y1 - w), (a, y1), (x1 + P['hook_gap'], y1)]
        lip_t = [(x1 + P['hook_gap'], y0 + w), (a, y0 + w), (a, y0 + w + t_top), (x1 + P['hook_gap'], y0 + w + t_top)]
        lip_b = [(x1 + P['hook_gap'], y1 - w - t_bot), (a, y1 - w - t_bot), (a, y1 - w), (x1 + P['hook_gap'], y1 - w)]
    return dict(web=[top, bot], lip=[lip_t, lip_b])


# hook lip z (must sit between the PCB bottom and the case floor)
HOOK_Z1 = P['pcb_bot'] - 0.6      # -7.2
HOOK_Z0 = HOOK_Z1 - P['plate_t']


def build_plate():
    doc, des, root = new_doc("PLATE")
    body = add_bodies(root, [map_poly(poly_rrect(PLATE_X0, PLATE_Y0, PLATE_X1, PLATE_Y1, R_OUT), -0.01)], P['plate_z0'], 0.0, "PLATE")[0]
    # switch / stab holes
    holes = []
    for k in KEYS:
        holes.append(poly_circle((k['x0'] + k['x1']) / 2, (k['y0'] + k['y1']) / 2, 14.0, 40))
    cut_z(root, [map_poly(h, 0.0) for h in holes], [body], P['plate_z0'] - 0.5, 0.5)
    # Cherry stab cut-outs
    slots = []
    for k in KEYS:
        for (sx, sy) in stab_holes_for(k):
            slots.append(poly_rrect(sx - PLATE_SLOT_W / 2, sy - PLATE_SLOT_H / 2, sx + PLATE_SLOT_W / 2, sy + PLATE_SLOT_H / 2, 0.0))
    cut_z(root, [map_poly(s, 0.0) for s in slots], [body], P['plate_z0'] - 0.5, 0.5)
    # uDB clearance + M2
    dy = db_centre_y() + 0.25
    port = poly_rrect(DB_CX - 7.0, db_centre_y() - 1.5, DB_CX + 7.0, P['db_y0'] + 0.05, 0.0)
    cut_z(root, [map_poly(port, 0.0)], [body], P['plate_z0'] - 0.5, 0.5)
    m2 = [poly_circle(DB_CX + dx, dy - P['db_dy0'], 2.2) for dx in (-P['db_dx'], P['db_dx'])]
    m2.append(poly_circle(DB_CX + P['db_dx'], dy + P['db_dy1'], 2.2))
    cut_z(root, [map_poly(h, 0.0) for h in m2], [body], P['plate_z0'] - 0.5, 0.5)
    # PCB reliefs: switch centre hole + two LED holes per switch
    rel = []
    for k in KEYS:
        cx, cy = (k['x0'] + k['x1']) / 2, (k['y0'] + k['y1']) / 2
        rel.append(poly_circle(cx, cy, 4.2))
        rel.append(poly_circle(cx - 5.08, cy + 2.54, 2.2))
        rel.append(poly_circle(cx + 5.08, cy + 2.54, 2.2))
    cut_z(root, [map_poly(h, 0.0) for h in rel], [body], P['plate_z0'] - 0.5, 0.5)
    # hooks
    for kind in ('left', 'right'):
        hp = hook_profiles(kind)
        add_bodies(root, [map_poly(p, P['plate_z0']) for p in hp['web']], P['plate_z0'], 0.0, "HOOK_WEB")
        add_bodies(root, [map_poly(p, HOOK_Z0) for p in hp['lip']], HOOK_Z0, HOOK_Z1, "HOOK_LIP")
    bs = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    join(root, body, bs[1:])
    body.name = "PLATE"
    print("plate", bbox_mm(body), round(body.volume * 1000, 1))
    return doc, des, root, body


def run(c=None):
    try:
        doc, des, root, body = build_plate()
        print("slice x=142.25 (between keys, through hooks)", slice_body(root, body, 142.25))
        print("slice x=95", slice_body(root, body, 95))
    except Exception:
        print(traceback.format_exc())
