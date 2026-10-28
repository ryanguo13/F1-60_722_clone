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
    plate_t=1.5, plate_z0=-1.5, pivot_x=137.75, pivot_y=6.175,   # sketch pivot (0.95-grid aligned)
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


GRID = dict(dx=0.0, dy=0.0)   # (0.95 grid offset from the plate origin); set by calibrate()

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


def local_origin(poly_xy, z=0.0):
    """Sketch coordinates in this Fusion build snap to a 0.95 mm grid for every
    point above |109 mm| (the long 60% parts always exceed that), so every
    sketch is built around this 0.95-aligned pivot: at this exact pivot the
    snapped points are identical to the intended values."""
    return P['pivot_x'], P['pivot_y']


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


SWITCH_CSET = None


def switch_centres_in(polys):
    global SWITCH_CSET
    if SWITCH_CSET is None:
        SWITCH_CSET = set((round((k['x0'] + k['x1']) / 2, 2), round((k['y0'] + k['y1']) / 2, 2)) for k in KEYS)
    polys = [merge_loops(p) if isinstance(p[0][0], (list, tuple)) else p for p in polys]
    out = []
    for p in polys:
        if len(p) < 8:
            continue
        xs = [a for a, b in p]
        ys = [b for a, b in p]
        cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
        if (round(cx, 2), round(cy, 2)) in SWITCH_CSET and abs((max(xs) - min(xs)) - 14.0) < 0.1:
            out.append((cx, cy))
    return out


def build_sketch(root, polys):
    """One loop = one sketch segment loop (holes stay holes when each loop is
    extruded on its own)."""
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    for pts in polys:
        if not pts:
            continue
        sp = []
        for p in pts:
            pt = sk.sketchPoints.add(px(p[0], p[1]))
            if sp and abs((sp[-1].geometry.x - pt.geometry.x) * 10) < 1e-4 and                     abs((sp[-1].geometry.y - pt.geometry.y) * 10) < 1e-4:
                continue
            sp.append(pt)
        if len(sp) > 2 and abs((sp[0].geometry.x - sp[-1].geometry.x) * 10) < 1e-4 and                 abs((sp[0].geometry.y - sp[-1].geometry.y) * 10) < 1e-4:
            sp.pop()
        if len(sp) < 3:
            continue
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


class Part(object):
    """A set of bodies whose sketches are all built at z=0; the finished
    bodies are moved into place exactly once, at the end (moving a body that
    came from an extruded profile corrupts it for later boolean features)."""

    def __init__(self, name):
        self.doc, self.des, self.root = new_doc(name)
        self.bodies = []
        self.name = name

    # -- creation ------------------------------------------------------
    def solid(self, polys, z0, z1, name=None):
        polys = [p for p in polys if p]
        if not polys:
            return None
        bs = self._extrude_local(polys, abs(z1 - z0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation, name)
        self.bodies += bs
        for b in bs:
            print("  solid", b.name, bbox_mm(b), "place z", min(z0, z1))
        if abs(min(z0, z1)) > 1e-9:
            move_bodies(self.root, bs, 0, 0, min(z0, z1))
        return bs[0] if len(bs) == 1 else bs

    def _extrude_local(self, polys, height, op, name=None, targets=None):
        org = local_origin(polys, 0.0)
        sk = build_sketch(self.root, [map_poly(p, 0.0, org) for p in polys])
        sk.isVisible = False if op == adsk.fusion.FeatureOperations.CutFeatureOperation else sk.isVisible
        ext = self.root.features.extrudeFeatures
        out = []
        for i in range(sk.profiles.count):
            prof = sk.profiles.item(i)
            if prof.areaProperties().area * 100 < 1e-6:
                continue
            if op == adsk.fusion.FeatureOperations.CutFeatureOperation:
                # first try a native circle (robust), else the profile
                inp = ext.createInput(prof, op)
                inp.participantBodies = targets
            else:
                inp = ext.createInput(prof, op)
            inp.setDistanceExtent(False, vreal(height * MM))
            try:
                f = ext.add(inp)
            except Exception as ex:
                print("  feature skipped: %s" % str(ex)[:60])
                continue
            if op == adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
                for j in range(f.bodies.count):
                    out.append(f.bodies.item(j))
        if op == adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
            print("  extrude", len(polys), "polys ->", sk.profiles.count, "profiles ->", len(out), "bodies")
        if name and out:
            for i, b in enumerate(out):
                b.name = name if len(out) == 1 else "%s_%02d" % (name, i + 1)
        return out

    def cut(self, polys, targets, z0, z1):
        """Cut `polys` (through them by height z1-z0 starting at z0)."""
        polys = [p for p in polys if p]
        if not polys:
            return
        tg = [t for t in targets if t.isValid and t in self.bodies]
        if not tg:
            return
        made = self._extrude_local(polys, abs(z1 - z0), adsk.fusion.FeatureOperations.CutFeatureOperation, targets=tg)
        print("  cut", len(polys), "loops ->", made, "vol", round(tg[0].volume * 1000, 1))

    def join(self, target, tools):
        tools = [t for t in tools if t.isValid and t is not target and t in self.bodies]
        if not tools:
            return target
        coll = adsk.core.ObjectCollection.create()
        for t in tools:
            coll.add(t)
        cib = self.root.features.combineFeatures
        ci = cib.createInput(target, coll)
        ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        ci.isKeepToolBodies = False
        cib.add(ci)
        self.bodies = [b for b in self.bodies if b not in tools]
        return target

    def main(self):
        bs = [b for b in self.bodies if b.isValid]
        big = max(bs, key=lambda b: b.volume)
        return big

    def export(self, path):
        for b in self.bodies:
            if b.isValid:
                b.isLightBulbOn = False
        m = self.main()
        m.isLightBulbOn = True
        # export only the main body
        app = adsk.core.Application.get()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sty = app.exportManager.createSTEPExportOptions(path, self.root)
        app.exportManager.execute(sty)
        m.isLightBulbOn = True
        return path

    def report(self):
        for b in self.bodies:
            print("  body", b.name, bbox_mm(b), round(b.volume * 1000, 1))


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


def fillet_body(root, body, picker, radius):
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


def bottom_outline():
    return outline_polys(P['r_side'], P['r_back'])


def inner_outline(inset_front=P['front_wall'], inset_side=P['side_wall'], inset_rear=P['rear_wall']):
    """Inner face of the case walls (offset inwards by the wall thickness)."""
    rs = max(0.5, P['r_side'] - max(inset_side, inset_front))
    rb = max(0.5, P['r_back'] - max(inset_side, inset_rear))
    yr = H - inset_rear
    return [poly_ul(inset_side, W - inset_side, yr, H, rb, 'back'),
            poly_ul(inset_side, W - inset_side, inset_front, yr, rs, 'front')]


# =====================================================================
# TOP
# =====================================================================
def top_inner_top_levels():
    return


def build_top():
    doc, des, root = new_doc("TOP")
    polys = bottom_outline()
    org = local_origin(polys, P['top_lip_z'])
    sk = build_sketch(root, [map_poly(polys, P['top_bottom'], org)])
    ext = root.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.setDistanceExtent(False, vreal((P['top_bottom'] - P['top_lip_z']) * MM))
    body = ext.add(inp).bodies.item(0)
    move_bodies(root, [body], org[0], org[1], P['top_lip_z'])
    body.name = "TOP"

    # outer wall only below the band line (-5), then the side bands up to z=0
    top_outline = inner_outline(inset_front=P['front_wall'] + 0.15,
                                inset_side=P['side_wall'] + 0.15,
                                inset_rear=P['rear_wall'] + 0.15)
    cut_z(root, top_outline, [body], P['top_lip_z'], P['lip_z'])
    cut_z(root, inner_outline(inset_front=P['front_wall'] + 0.15, inset_side=P['side_wall'] + 0.15,
                              inset_rear=P['rear_wall'] + 0.15), [body], P['lip_z'], P['top_bottom'] + 0.001)
    # switch room above the PCB region
    pocket = inner_outline()
    cut_z(root, pocket, [body], P['pocket_z'], P['pocket_z'] + 0.001)
    # below the strap: open the rear corridor down to the deck
    print("top", bbox_mm(body), round(body.volume * 1000, 1))
    return doc, des, root, body


PLATE_SLOT_W = 7.2
PLATE_SLOT_H = 2.8
HOOK_OVER = 22.0


def keys_zone():
    xs = [k['x0'] for k in KEYS] + [k['x1'] for k in KEYS]
    ys = [k['y0'] for k in KEYS] + [k['y1'] for k in KEYS]
    return min(xs) + HOOK_OVER, max(xs) - HOOK_OVER, min(ys) + 0.25, max(ys) - 0.25


HOOK_Z1 = P['pcb_bot'] - 0.6
HOOK_Z0 = HOOK_Z1 - P['plate_t']


def hook_profiles(kind):
    x0, x1, y0, y1 = keys_zone()
    w = P['hook_w']
    t_top = P['hook_top_leg']
    t_bot = P['hook_bot_leg']
    g = P['hook_gap']
    if kind == 'left':
        a = PLATE_X0
        top = [(a, y0), (x0 - g, y0), (x0 - g, y0 + w), (a, y0 + w)]
        bot = [(a, y1 - w), (x0 - g, y1 - w), (x0 - g, y1), (a, y1)]
        lip = [(a, y0 + w), (x0 - g, y0 + w), (x0 - g, y0 + w + t_top), (a, y0 + w + t_top),
               (a, y1 - w - t_bot), (x0 - g, y1 - w - t_bot), (x0 - g, y1 - w), (a, y1 - w)]
    else:
        a = PLATE_X1
        top = [(x1 + g, y0), (a, y0), (a, y0 + w), (x1 + g, y0 + w)]
        bot = [(x1 + g, y1 - w), (a, y1 - w), (a, y1), (x1 + g, y1)]
        lip = [(x1 + g, y0 + w), (a, y0 + w), (a, y0 + w + t_top), (x1 + g, y0 + w + t_top),
               (x1 + g, y1 - w - t_bot), (a, y1 - w - t_bot), (a, y1 - w), (x1 + g, y1 - w)]
    return dict(web=[top, bot], lip=[lip])


def build_plate():
    part = Part("PLATE")
    body = part.solid([poly_rrect(PLATE_X0, PLATE_Y0, PLATE_X1, PLATE_Y1, 10.0)],
                      P['plate_z0'], 0.0, "PLATE")
    body = body[0] if isinstance(body, list) else body
    hole_c = [poly_circle((k['x0'] + k['x1']) / 2, (k['y0'] + k['y1']) / 2, 14.0, 40) for k in KEYS]
    part.cut(hole_c, [body], P['plate_z0'] - 0.1, 1.0)
    print("plate after switch holes", bbox_mm(body), round(body.volume * 1000, 1))
    return part, body


def run(c=None):
    try:
        part, body = build_plate()
        print("slice x=142.25", slice_body(part.root, body, 78.75))
    except Exception:
        print(traceback.format_exc())
