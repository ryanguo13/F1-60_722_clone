# -*- coding: utf-8 -*-
"""F1-60 722 clone -- parametric Fusion 360 build script (WKL, 3D-print ready).

Three printable parts, one Fusion document each, exported to out/ as STEP
(and STL) for 嘉立创 3D printing with heat-set inserts:

  BOTTOM   bottom case: 7.22 deg wedge, weight well with a 1.2 mm floor (for a
           later steel plate), uDB cut-out in the rear wall, inner floor
  TOP      top case: 3 mm bezel walls, WKL blockers in the plate, 5.3 mm switch
           pocket, seam with the bottom, rear strap that carries the two uDB
           M2 taps, four M3 clearance holes, 6 x 6 mm corner pads at z -2..-1.5
  PLATE    1.5 mm ANSI/WKL plate: cherry switch/stab cut-outs, four paddle
           hooks on the two inner edges, uDB M2 holes, PCB led reliefs

See docs/DESIGN.md for where every number comes from.

HOW THIS BUILD WORKS (Fusion 2705.1 through the MCP endpoint)
-------------------------------------------------------------
The parametric kernel only gives reliable booleans for short sketches and
long-distance features. Long 60% parts break it in several ways, so:
  * everything is drawn in 2D and extruded along the sketch's z-axis only
    (no "distance into the part"), using one sketch per loop;
  * circle-like loops are drawn once and never touched again (any later edit
    corrupts them), rectangles are drawn as native segments;
  * all 2D coordinates are produced by `map_model()` from LAYOUT coordinates
    (x left->right, y front->back, z up, 0 = plate top). The model's +Y is the
    PCB's -y (the back row faces the case's printed back edge).
Parts are built as separate documents and exported; no attempt is made to
keep them parametric: the script IS the parameter set.
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
    pivot_x=137.75, pivot_y=6.175,       # sketch pivot (0.95 mm grid aligned)
    # vertical stack, layout z (0 = plate top)
    plate_t=1.5,
    plate_room=5.3,                      # top underside above the plate surface
    pcb_top=-5.0, pcb_bot=-6.6,
    floor_z=-10.5,                       # bottom floor under the PCB
    deck_z=-16.0,                        # bottom deck behind the PCB (top rests on it)
    top_lip_z=-9.0,                      # top's outer wall starts here (covers the seam)
    weight_floor=1.2,                    # metal plate well keeps this much floor
    # walls
    side_wall=3.0, front_wall=3.0, rear_wall=3.0,
    # uDB (ai03 Unified Daughterboard, C series: 18 x 16.5, M2 14 x 12.5)
    db_w=18.0, db_h=16.5,
    db_y0=84.6,                          # window in the rear wall
    db_dx=7.0, db_dy0=11.3, db_dy1=17.0,   # M2 holes from the window centre
    # weight well
    weight_x0=11.5, weight_x1=273.0, weight_y0=11.5, weight_y1=76.5, weight_r=3.0,
    # screws (space-key centred at the rear, walls at the front)
    screw_inset=6.0, screw_y_bottom=6.0, screw_y_top=14.25,
    boss=8.0, insert_d=3.6, insert_len=6.0, screw_d=3.4,
    # plate hooks
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
W, H = P['W'], P['H']


# =====================================================================
# LAYOUT (pure python)
# =====================================================================
def build_keys():
    rows = [
        [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1),
         (10, 1), (11, 1), (12, 2)],
        [(0, 1.5)] + [(1.5, 1)] * 10 + [(11.5, 1), (12.5, 1), (13.5, 1.5), (15.0, 1.5), (16.5, 1.5)],
        [(0, 1.75)] + [(1.75, 1)] * 9 + [(10.75, 1), (11.75, 1), (12.75, 2.25), (15.0, 1.5), (16.5, 1.5)],
        [(0, 2.25)] + [(2.25, 1)] * 7 + [(9.25, 1), (10.25, 1), (11.25, 1), (12.25, 1.75), (14.0, 2.75),
                                       (16.75, 1.25)],
        [(0, 1.25), (1.25, 1.25), (2.5, 1.25), (3.75, 6.25), (10.0, 1.25), (11.25, 1.25),
         (12.5, 1.25), (13.75, 1.25)],
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
SPACE = [k for k in KEYS if k['row'] == 4 and abs(k['w'] - 6.25) < 1e-6][0]
DB_CX = (SPACE['x0'] + SPACE['x1']) / 2.0


def stab_holes_for(k):
    out = []
    for (row, off, kw, wire) in STABS:
        if row != k['row'] or abs(k['w'] - kw) > 1e-6:
            continue
        half = (wire - 1) * U / 2.0
        kc = (k['x0'] + k['x1']) / 2.0 + (0.2 if row == 3 else 0.0)
        out += [(kc - half, KEY_Y[row]), (kc + half, KEY_Y[row])]
    return out


def top_edge(x):
    r = P['r_back']
    if x < r:
        return H - r + math.sqrt(max(0.0, r * r - (r - x) ** 2))
    if x > W - r:
        return H - r + math.sqrt(max(0.0, r * r - (x - (W - r)) ** 2))
    return H


def bottom_edge(x):
    r = P['r_side']
    if x < r:
        return r - math.sqrt(max(0.0, r * r - (r - x) ** 2))
    if x > W - r:
        return r - math.sqrt(max(0.0, r * r - (x - (W - r)) ** 2))
    return 0.0


def screw_positions():
    out = []
    for x in (P['screw_inset'], W - P['screw_inset']):
        out.append((x, bottom_edge(x) + P['screw_y_bottom']))
        out.append((x, top_edge(x) - P['screw_y_top']))
    return out


def db_centre_y():
    return (P['db_y0'] + H) / 2.0 - 0.5


# =====================================================================
# SHAPES (layout XY loops as point lists)
# =====================================================================
def poly_ul(x0, x1, y0, y1, r, side, n=6):
    """Rectangle whose two corners toward `side` are rounded (polygonal arc)."""
    def arc(cx, cy, a0):
        return [(cx + r * math.cos(a0 + (math.pi / 2) * i / n),
                 cy + r * math.sin(a0 + (math.pi / 2) * i / n)) for i in range(n + 1)]
    if side == 'front':
        return ([(x0, y1), (x0, y0 + r)] + arc(x0 + r, y0 + r, math.pi) +
                arc(x1 - r, y0 + r, 1.5 * math.pi) + [(x1, y1)])
    return ([(x0, y0), (x0, y1 - r)] + arc(x0 + r, y1 - r, math.pi) +
            arc(x1 - r, y1 - r, 1.5 * math.pi) + [(x1, y0)])


def poly_rrect(x0, y0, x1, y1, r):
    """Rectangle rounded on all four corners (16 points, elliptical arcs)."""
    r = max(0.0, min(r, (x1 - x0) / 2.0 - 0.001, (y1 - y0) / 2.0 - 0.001))
    if r <= 0.01:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    k = 0.55 * r
    return [
        (x0 + r, y0), (x1 - r, y0), (x1 - r + k, y0), (x1, y0 + r - k), (x1, y0 + r),
        (x1, y1 - r), (x1, y1 - r + k), (x1 - r + k, y1), (x1 - r, y1),
        (x0 + r, y1), (x0 + r - k, y1), (x0, y1 - r + k), (x0, y1 - r),
        (x0, y0 + r), (x0, y0 + r - k), (x0 + r - k, y0), (x0 + r, y0)]


def poly_circle(cx, cy, dia, n=40):
    r = dia / 2.0
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def outline_polys(r_side, r_back):
    yr = H - P['rear_wall']
    return [poly_ul(0, W, yr, H, r_back, 'back'),
            poly_ul(0, W, 0, yr, r_side, 'front')]


def inner_outline(gap=0.0):
    f = P['front_wall'] + gap
    s = P['side_wall'] + gap
    r = P['rear_wall'] + gap
    rs = max(0.5, P['r_side'] - max(s, f))
    rb = max(0.5, P['r_back'] - max(s, r))
    yr = H - r
    return [poly_ul(s, W - s, yr, H, rb, 'back'),
            poly_ul(s, W - s, f, yr, rs, 'front')]


# =====================================================================
# LAYOUT -> MODEL
# =====================================================================
def map_pt(x, y, z):
    """Layout (x, y, z) -> model point of a part lying on the print bed.
    Model +Y is the PCB's -y, so the keyboard's back row faces model +Y."""
    L = H - y
    return (W - x, -z + L * TAN, L * COS)


def local_origin():
    return P['pivot_x'], P['pivot_y']


def map_model(x, y, z):
    """Layout -> 2D model sketch coordinates (pivot-relative, rounded)."""
    q = map_pt(x, y, z)
    ox, oy = local_origin()
    return round(q[0] - ox, 3), round(q[1] - oy, 3)


def map_loop(loop, z):
    return [map_model(x, y, z) for (x, y) in loop]


def loop_area(loop):
    a = 0.0
    for i in range(len(loop)):
        x0, y0 = loop[i - 1]
        x1, y1 = loop[i]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


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
    doc.name = name
    des = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    return doc, des, des.rootComponent


def one_sketch(root, loop2d):
    """Sketch a single closed loop as native segment lines. Each loop gets its
    own sketch; loops are never re-drawn or edited afterwards."""
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    pts = loop2d[:-1] if (len(loop2d) > 2 and loop2d[0] == loop2d[-1]) else loop2d
    sp = [sk.sketchPoints.add(px(a, b)) for (a, b) in pts]
    for i in range(len(sp)):
        lines.addByTwoPoints(sp[i], sp[(i + 1) % len(sp)])
    sk.isComputeDeferred = False
    if sk.profiles.count != 1:
        raise RuntimeError("loop gave %d profiles" % sk.profiles.count)
    return sk


# =====================================================================
# PART BUILDER
# =====================================================================
class Part(object):
    """Builds one solid from 2D loops. Every sketch lies on model z = 0; a
    loop drawn at the model XY plane is given its layout height by the extrude
    direction: `sk(loop)` uses layout z 0, `sk(loop, z)` maps the loop as if
    it were at layout z (used for the tilted horizontal faces)."""

    def __init__(self, name):
        self.doc, self.des, self.root = new_doc(name)
        self.body = None
        self.name = name

    def sk(self, loop, z=0.0):
        return one_sketch(self.root, [map_model(x, y, z) for (x, y) in loop])

    def extrude(self, sk, z_from, z_to, op=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, targets=None):
        """Extrude from layout z_from (down/up in model z) to z_to."""
        h = abs(z_to - z_from)
        ext = self.root.features.extrudeFeatures
        inp = ext.createInput(sk.profiles.item(0), op)
        if op == adsk.fusion.FeatureOperations.CutFeatureOperation:
            inp.participantBodies = targets or [self.body]
        inp.setDistanceExtent(False, vreal(h * MM))
        f = ext.add(inp)
        if op == adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
            self.body = f.bodies.item(0)
        return f

    def cut(self, loop, z_from, z_to, targets=None):
        self.extrude(self.sk(loop, z_from), z_from, z_to, adsk.fusion.FeatureOperations.CutFeatureOperation,
                     targets)

    def add(self, loop, z_from, z_to):
        """Extrude a loop and join it to the part (bridges a level)."""
        self.extrude(self.sk(loop, z_from), z_from, z_to, adsk.fusion.FeatureOperations.JoinFeatureOperation,
                     [self.body])

    def report(self):
        b = self.body
        bb = b.boundingBox
        print("  %s  x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f  vol %.1f" % (
            self.name, bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
            bb.minPoint.z * 10, bb.maxPoint.z * 10, b.volume * 1000))


# =====================================================================
# BOTTOM
# =====================================================================
def uDB_loop():
    yc = db_centre_y()
    return poly_rrect(DB_CX - P['db_w'] / 2 - 0.3, yc - P['db_h'] / 2 - 0.3,
                      DB_CX + P['db_w'] / 2 + 0.3, yc + P['db_h'] / 2 + 0.3, 0.8)


def weight_loop():
    return poly_rrect(P['weight_x0'], P['weight_y0'], P['weight_x1'], P['weight_y1'], P['weight_r'])


def boss_loops(dia):
    return [poly_circle(x, y, dia) for (x, y) in screw_positions()]


def build_bottom():
    part = Part("BOTTOM")
    # 1 outer prism: outline, full height
    part.extrude(part.sk(outline_polys(P['r_side'], P['r_back'])[0]), 0.0, P['top_bottom'] - P['deck_z'])
    part.add(outline_polys(P['r_side'], P['r_back'])[1], 0.0, P['top_bottom'] - P['deck_z'])
    # 2 cavity down to the floor
    part.cut(inner_outline()[0], 0.0, P['floor_z'] - P['deck_z'])
    part.cut(inner_outline()[1], 0.0, P['floor_z'] - P['deck_z'])
    # 3 weight well (1.2 mm floor kept)
    part.cut(weight_loop(), 0.0, P['floor_z'] + P['weight_floor'] - P['deck_z'])
    # 4 screw bosses (support the top's corner pads) and their insert bores
    for loop in boss_loops(P['boss']):
        part.add(loop, 0.0, P['top_bottom'] - P['deck_z'])
    for loop in boss_loops(P['insert_d']):
        part.cut(loop, 0.0, P['insert_len'] + (0.0 - 0.0))
    part.report()
    return part


# =====================================================================
# PLATE
# =====================================================================
def build_plate():
    part = Part("PLATE")
    part.extrude(part.sk(poly_rrect(PLATE_X0, PLATE_Y0, PLATE_X1, PLATE_Y1, 10.0)), 0.0, P['plate_t'])
    for k in KEYS:
        part.cut(poly_circle((k['x0'] + k['x1']) / 2, (k['y0'] + k['y1']) / 2, 14.0, 40), 0.0, P['plate_t'])
    part.report()
    return part


def run(c=None):
    try:
        part = build_plate()
        print("ok plate")
    except Exception:
        print(traceback.format_exc())
