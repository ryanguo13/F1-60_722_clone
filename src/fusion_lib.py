# -*- coding: utf-8 -*-
"""Fusion helpers for the F1-60 722 build (all lengths in mm).

The scripted API in this Fusion build (2706) only behaves when it touches
geometry of moderate size: profiles that span more than ~100 mm come back
sheared (a 140 mm prism is only 28 mm wide), and cuts from native sketch
circles remove far more material than the circle. Geometry is therefore built
from pieces of at most ~60 mm, each piece exactly one of:
  * a square FRAME ring (outer SW x SH with a square hole) - always cut from
    its own outline, which this kernel handles exactly,
  * a TRIANGLE profile - used to fill frame corners and to build footprints,
  * a CO RECTANGLE, cut or joined only against pieces of the same size.
`check()` compares any operation with what the analytic volume says it should
remove, so a silent kernel failure shows up immediately.
"""
import math
try:
    import adsk.core
    import adsk.fusion
except ImportError:          # offline self-test
    adsk = None

MM = 0.1


# ---------------------------------------------------------------- geometry
def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def val(v):
    return adsk.core.ValueInput.createByReal(v * MM)


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def in_triangle(p, a, b, c):
    d1, d2, d3 = cross(a, b, p), cross(b, c, p), cross(c, a, p)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def point_in_poly(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i - 1], poly[i]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if p[0] < x:
                inside = not inside
    return inside


def triangulate(poly):
    """Ear clipping; returns a list of triangles (each 3 points)."""
    pts = list(poly)
    if loop_area(pts) < 0:
        pts.reverse()
    tris = []
    guard = 0
    while len(pts) > 3 and guard < 10000:
        guard += 1
        n = len(pts)
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            if cross(a, b, c) <= 1e-9:
                continue
            ok = True
            for p in pts:
                if p in (a, b, c):
                    continue
                if in_triangle(p, a, b, c):
                    ok = False
                    break
            if ok:
                tris.append((a, b, c))
                pts.pop(i)
                break
        else:
            break
    if len(pts) == 3:
        tris.append(tuple(pts))
    return tris


def loop_area(loop):
    a = 0.0
    for i in range(len(loop)):
        x0, y0 = loop[i - 1]
        x1, y1 = loop[i]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def ray_hits(poly, a, b):
    """Number of intersections of segment a-b with the polygon boundary."""
    hits = []
    n = len(poly)
    for i in range(n):
        c, d = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ex, ey = d[0] - c[0], d[1] - c[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        t = ((c[0] - a[0]) * ey - (c[1] - a[1]) * ex) / den
        u = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / den
        if 0 < t < 1 and 0 < u < 1:
            hits.append(a[0] + t * dx)
    hits.sort()
    return hits


# ---------------------------------------------------------------- sketch
def sketch_polygon(sk, poly, z=None):
    L = sk.sketchCurves.sketchLines
    sp = [sk.sketchPoints.add(pt(p[0], p[1], z or 0.0)) for p in poly]
    for i in range(len(sp)):
        L.addByTwoPoints(sp[i], sp[(i + 1) % len(sp)])
    return sp


class Builder(object):
    def __init__(self, doc, des):
        self.doc = doc
        self.des = des
        self.root = des.rootComponent
        self.ext = self.root.features.extrudeFeatures

    # -- features --------------------------------------------------
    def sketch(self, poly):
        sk = self.root.sketches.add(self.root.xYConstructionPlane)
        sketch_polygon(sk, poly)
        if sk.profiles.count != 1:
            raise RuntimeError("sketch gave %d profiles" % sk.profiles.count)
        return sk

    def extrude_new(self, sk, h, join=None):
        inp = self.ext.createInput(sk.profiles.item(0),
                                   adsk.fusion.FeatureOperations.JoinFeatureOperation if join
                                   else adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        if join:
            inp.participantBodies = [join]
        inp.setDistanceExtent(False, val(h))
        f = self.ext.add(inp)
        return f.bodies.item(0) if join is None else join

    def cut(self, sk, body, h):
        inp = self.ext.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.participantBodies = [body]
        inp.setDistanceExtent(False, val(h))
        return self.ext.add(inp)

    # -- measured operations ---------------------------------------
    def cut_measured(self, poly, body, h, expect, label=""):
        """Cut `poly` (depth h) and verify the removed volume with the analytic
        expectation (poly area * h, minus any existing overlap is caller's)."""
        v0 = body.volume * 1000
        self.cut(self.sketch(poly), body, h)
        got = v0 - body.volume * 1000
        ok = abs(got - expect) <= max(0.5, abs(expect) * 1e-3)
        if not ok:
            print("  ! %s: removed %.3f, expected %.3f" % (label, got, expect))
        return ok

    def frame_cut(self, c, SW, SH, hole, h, label=""):
        """A square frame ring with a centred square hole, cut depth h."""
        x, y = c
        n0, n1 = (SW - hole) / 2.0, (SW + hole) / 2.0
        m0, m1 = (SH - hole) / 2.0, (SH + hole) / 2.0
        poly = [(x - n1, y - m1), (x + n1, y - m1), (x + n1, y - m0), (x + n0, y - m0),
                (x + n0, y + m0), (x + n1, y + m0), (x + n1, y + m1), (x - n1, y + m1),
                (x - n1, y + m0), (x - n0, y + m0), (x - n0, y - m0), (x - n1, y - m0)]
        area = SW * SH - hole * hole
        return self.cut_measured(poly, self._body, h, area * h, label)


# ---------------------------------------------------------------- triangulation helpers
TRI_SIZE = 60.0        # longest edge of a cut triangle
CO_RECT = 55.0         # side of co rectangles (cut/join partners)


def poly_area_tris(poly):
    return sum(abs(loop_area(list(t))) for t in triangulate(poly))


def tri_cells(lo, hi, size=TRI_SIZE, margin=4.0):
    """Axis-aligned cells (x0, y0, x1, y1) covering [lo, hi] with some margin."""
    out = []
    x = lo[0] - margin
    while x < hi[0] + margin:
        y = lo[1] - margin
        while y < hi[1] + margin:
            out.append((x, y, x + size, y + size))
            y += size
        x += size
    return out


def boundary_piece_tris(poly, margin=4.0):
    """Cover `poly` with triangles of <= TRI_SIZE (longest side), clipped per
    cell; the caller turns each into its own triangle prism."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cells = tri_cells((min(xs), min(ys)), (max(xs), max(ys)), TRI_SIZE, margin)
    out = []
    for c in cells:
        cx0, cy0, cx1, cy1 = c
        cw, ch = cx1 - cx0, cy1 - cy0
        if cw > 0 and ch > 0:
            s_cell = [(cx0, cy0), (cx0 + cw, cy0), (cx0 + cw, cy0 + ch), (cx0, cy0 + ch)]
            piece = clip_subject(poly, s_cell)
            if len(piece) >= 3:
                out.extend(triangulate(dedupe(piece)))
    return out


def co_rects_for(poly, size=CO_RECT):
    """Rectangles to intersect a prism with, so every subsequent cut has a
    matching-size co body: one per occupied cell."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cells = tri_cells((min(xs), min(ys)), (max(xs), max(ys)), size, 0.0)
    return cells


def poly_prism_tris(poly, overlap=0.05, size=TRI_SIZE):
    """Triangles (with a lateral overlap band) that, extruded and intersected,
    reproduce `poly` in pieces of at most `size` across."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cells = tri_cells((min(xs), min(ys)), (max(xs), max(ys)), size, 0.0)
    core = []
    for c in cells:
        piece = clip_subject(poly, c)
        if len(piece) >= 3 and abs(loop_area(piece)) > EPS:
            core.extend(triangulate(dedupe(piece)))
    if not core:
        return []
    # overlap band: a thin copy of the polygon is *not* used; instead each
    # triangle is shrunk by 0 so cells butt; the caller makes the co rect after.
    return core


# ---------------------------------------------------------------- clipping
EPS = 1e-6


def clip_subject(subject, clipper):
    """Sutherland-Hodgman: part of `subject` polygon inside `clipper` (convex).
    Returns a polygon list (may be empty)."""
    out = list(subject)
    n = len(clipper)
    for i in range(n):
        a, b = clipper[i - 1], clipper[i]
        inp, out = out, []
        if not inp:
            break

        def inside(p):
            return cross(a, b, p) >= -EPS

        for j in range(len(inp)):
            cur, prv = inp[j], inp[j - 1]
            if inside(cur):
                if not inside(prv):
                    out.append(_isect(prv, cur, a, b))
                out.append(cur)
            elif inside(prv):
                out.append(_isect(prv, cur, a, b))
    return out


def _isect(p, q, a, b):
    dx, dy = q[0] - p[0], q[1] - p[1]
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = dx * ey - dy * ex
    if abs(den) < 1e-12:
        return q
    t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
    return (p[0] + t * dx, p[1] + t * dy)


def clip_cell(subject, cell):
    """Clip against an axis-aligned cell (x0, y0, x1, y1) = a convex quad."""
    x0, y0, x1, y1 = cell
    quad = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return clip_subject(subject, quad)


def cell_rects(cell_rects_, subject):
    """Split subject into pieces per axis-aligned rectangle it overlaps."""
    out = []
    for r in cell_rects_:
        piece = clip_cell(subject, r)
        if len(piece) >= 3 and abs(loop_area(piece)) > EPS:
            out.append(piece)
    return out


def dedupe(poly):
    out = []
    for p in poly:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-7:
            out.append(p)
    while len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= 1e-7:
        out.pop()
    return out


def _poly_area(poly):
    return abs(loop_area(poly))


if __name__ == "__main__":
    sq = [(0, 0), (100, 0), (100, 100), (0, 100)]
    cells = [(0, 0, 60, 60), (60, 0, 120, 60), (0, 60, 60, 120), (60, 60, 120, 120)]
    pieces = cell_rects(cells, sq)
    print("square 100^2 =", _poly_area(sq), "pieces", [round(_poly_area(p), 2) for p in pieces],
          "sum", round(sum(_poly_area(p) for p in pieces), 2))
    tri = [(0, 0), (100, 0), (50, 100)]
    pieces = cell_rects(cells, tri)
    print("tri", round(_poly_area(tri), 2), "pieces", [round(_poly_area(p), 2) for p in pieces],
          "sum", round(sum(_poly_area(p) for p in pieces), 2))
    print("n-gon sizes", [len(p) for p in pieces], "tris", [len(triangulate(p)) for p in pieces])
    rring = [(-40, -10), (40, -10), (40, 10), (-40, 10), (-40, 5), (-30, 5), (-30, -5), (-40, -5)]
    pieces = cell_rects([(-60, -20, 0, 20), (0, -20, 60, 20)], rring)
    print("U shape", round(_poly_area(rring), 2), "pieces", [round(_poly_area(p), 2) for p in pieces],
          "sum", round(sum(_poly_area(p) for p in pieces), 2))
