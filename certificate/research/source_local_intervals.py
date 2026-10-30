"""Standard-library interval geometry for a prospective local certificate.

Imports the unchanged feasibility consumer's outward-rounded arithmetic only.
This module alone makes no packing, contact-closure or optimality claim.
"""
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hardened_checker import I, D, PI, sincos, dot, dec_grid

ZERO = I.point(0)
ONE = I.point(1)
HALF = I.point(Fraction(1, 2))
RHO = sincos(PI / 5)[1]
NORMALS = [sincos(PI * Fraction(2*k, 5)) for k in range(5)]


def magnitude(x): return max(abs(x.lo), abs(x.hi))
def cw(v): return (v[1], -v[0])


def geometry(z):
    if len(z) != 34:
        raise ValueError('Exactly 34 coordinates required')
    poses = [z[3*i:3*i+3] for i in range(11)]
    units = [[sincos(poses[i][2]+PI*Fraction(2*k, 3)) for k in range(3)] for i in range(11)]
    return poses, units


def row(z, label, geom=None):
    q, u = geometry(z) if geom is None else geom
    jac = [ZERO]*34
    if label[0] == 'w' and len(label) == 4:
        _, i, k, a = label
        if any(type(v) is not int for v in (i,k,a)) or not (0 <= i < 11 and 0 <= k < 5 and 0 <= a < 3):
            raise ValueError('Invalid wall row')
        n = NORMALS[k]
        value = dot(n, [q[i][v]+u[i][a][v] for v in range(2)]) + RHO*z[-1]
        jac[3*i:3*i+2] = n
        jac[3*i+2] = dot(n, cw(u[i][a]))
        jac[-1] = RHO
    elif label[0] == 'p' and len(label) == 5:
        _, i, j, e, a = label
        if any(type(v) is not int for v in (i,j,e,a)) or not (0 <= i < j < 11 and 0 <= e < 6 and 0 <= a < 3):
            raise ValueError('Invalid pair row')
        owner, other, k = (i,j,e) if e < 3 else (j,i,e-3)
        n = tuple(-v for v in u[owner][k])
        difference = [q[other][v]+u[other][a][v]-q[owner][v] for v in range(2)]
        value = dot(n, difference)-HALF
        jac[3*owner:3*owner+2] = [-v for v in n]
        jac[3*other:3*other+2] = n
        jac[3*owner+2] = dot(cw(n), difference)
        jac[3*other+2] = dot(n, cw(u[other][a]))
    else:
        raise ValueError('Invalid feature label')
    return value, jac


def values(z, labels):
    geom = geometry(z)
    return [row(z, label, geom) for label in labels]


def matvec(a, b):
    if any(len(row) != len(b) for row in a):
        raise ValueError('Matrix/vector dimensions disagree')
    return [sum((x*y for x,y in zip(row,b) if (x.lo or x.hi) and (y.lo or y.hi)), ZERO) for row in a]


def matmul(a, b):
    if not a or not b or any(len(row) != len(b[0]) for row in b) or any(len(row) != len(b) for row in a):
        raise ValueError('Matrix dimensions disagree')
    columns = list(zip(*b))
    return [[sum((x*y for x,y in zip(row,col) if (x.lo or x.hi) and (y.lo or y.hi)), ZERO) for col in columns] for row in a]


def residual_identity(a):
    if not a or any(len(row) != len(a) for row in a):
        raise ValueError('Square matrix required')
    return [[I.point(int(i == j))-x for j,x in enumerate(row)] for i,row in enumerate(a)]


def infinity_norm_bound(a):
    return max(sum(magnitude(x) for x in row) for row in a)


def root_box(center, radius, labels, inverse):
    """Verify a contraction of x-CF(x) on the closed coordinate box.

    Every returned inequality is checked with integer comparisons. No numerical
    tolerances or floating matrices are trusted as conclusions. Invertibility
    follows because ||I-CJ||<1, so a fixed point is an actual F=0 root.
    """
    if len(center) != 34 or len(labels) != 34 or len({tuple(x) for x in labels}) != 34:
        raise ValueError('A square system of 34 distinct rows is required')
    if len(inverse) != 34 or any(len(row) != 34 for row in inverse):
        raise ValueError('34 by 34 inverse proposal required')
    if any(x.lo != x.hi for x in center) or radius.lo != radius.hi or radius.lo <= 0:
        raise ValueError('Exact grid center and positive radius required')
    box = [I(x.lo-radius.lo, x.hi+radius.hi) for x in center]
    f0 = [v for v,j in values(center, labels)]
    jbox = [j for v,j in values(box, labels)]
    error = residual_identity(matmul(inverse, jbox))
    contraction = infinity_norm_bound(error)
    if contraction >= D:
        raise ValueError('Root map contraction not proved')
    correction = matvec(inverse, f0)
    spreads = matvec(error, [I(-radius.hi, radius.hi)]*34)
    deviations = [-a+b for a,b in zip(correction, spreads)]
    if any(magnitude(x) >= radius.lo for x in deviations):
        raise ValueError('Root map not strictly inside coordinate box')
    return dict(box=box, contraction_bound=contraction,
                image_radius_bound=max(map(magnitude, deviations)),
                center_residual_bound=max(map(magnitude, f0)))


def incidence_closure(box, equations):
    """Derive exact incidences at the equation root by elementary geometry.

    Triangle edge k contains its two vertices a != k. Selected root equations
    supply additional incidences. Rules use distinct points, nonparallel lines,
    and equal-length triangle edges with a certified common direction. No small
    interval residual is ever promoted to an exact zero.
    """
    q,u = geometry(box)
    points = [[q[i][v]+u[i][a][v] for v in range(2)] for i in range(11) for a in range(3)]
    normals = [tuple(-v for v in u[i][k]) for i in range(11) for k in range(3)] + NORMALS
    vp, lp = list(range(33)), list(range(38))
    def find(parents, x):
        while parents[x] != x:
            x = parents[x]
        return x
    def unite(parents, a, b):
        a,b = find(parents,a),find(parents,b)
        if a == b:
            return False
        parents[max(a,b)] = min(a,b)
        return True
    incidences = {(3*i+a,3*i+k) for i in range(11) for k in range(3) for a in range(3) if a != k}
    for label in equations:
        if label[0] == 'w':
            _,i,k,a = label
            incidences.add((3*i+a,33+k))
        else:
            _,i,j,e,a = label
            owner,other,k = (i,j,e) if e < 3 else (j,i,e-3)
            incidences.add((3*other+a,3*owner+k))
    def distinct(a,b):
        if a//3 == b//3 and a != b:
            return True
        return any(x.hi < y.lo or y.hi < x.lo for x,y in zip(points[a],points[b]))
    events = []
    while True:
        normalized = {(find(vp,v),find(lp,l)) for v,l in incidences}
        vertices = sorted({find(vp,v) for v in range(33)})
        lines = sorted({find(lp,l) for l in range(38)})
        line_points = {l:{v for v,ll in normalized if ll == l} for l in lines}
        changed = False
        for index,l in enumerate(lines):
            for m in lines[index+1:]:
                common = sorted(line_points[l] & line_points[m])
                witness = next(((a,b) for index,a in enumerate(common) for b in common[index+1:] if distinct(a,b)), None)
                if witness:
                    unite(lp,l,m)
                    events.append(dict(rule='two_distinct_points_determine_line',lines=[l,m],vertices=list(witness)))
                    changed = True
                    break
            if changed: break
        if changed: continue
        vertex_lines = {v:{l for vv,l in normalized if vv == v} for v in vertices}
        for index,a in enumerate(vertices):
            for b in vertices[index+1:]:
                common = sorted(vertex_lines[a] & vertex_lines[b])
                witness = None
                for ii,l in enumerate(common):
                    for m in common[ii+1:]:
                        det = normals[l][0]*normals[m][1]-normals[l][1]*normals[m][0]
                        if det.lo > 0 or det.hi < 0:
                            witness=(l,m,det)
                            break
                    if witness: break
                if witness:
                    l,m,det = witness
                    unite(vp,a,b)
                    events.append(dict(rule='two_nonparallel_lines_determine_point',vertices=[a,b],lines=[l,m],
                                       determinant_interval=[dec_grid(det.lo),dec_grid(det.hi)]))
                    changed = True
                    break
            if changed: break
        if changed: continue
        # Every triangle edge has the exact same nonzero length sqrt(3).
        for l in range(33):
            left = [3*(l//3)+a for a in range(3) if a != l%3]
            for m in range(l+1,33):
                if find(lp,l) != find(lp,m): continue
                right = [3*(m//3)+a for a in range(3) if a != m%3]
                for il,a in enumerate(left):
                    for ir,b in enumerate(right):
                        if find(vp,a) != find(vp,b): continue
                        other_a,other_b = left[1-il],right[1-ir]
                        if find(vp,other_a) == find(vp,other_b): continue
                        va = [x-y for x,y in zip(points[other_a],points[a])]
                        vb = [x-y for x,y in zip(points[other_b],points[b])]
                        alignment = dot(va,vb)
                        if alignment.lo > 0:
                            unite(vp,other_a,other_b)
                            events.append(dict(rule='equal_edges_common_origin_and_direction',lines=[l,m],
                                origins=[a,b],vertices=[other_a,other_b],dot_lower=dec_grid(alignment.lo)))
                            changed = True
                            break
                    if changed: break
                if changed: break
            if changed: break
        if not changed: break
    normalized = {(find(vp,v),find(lp,l)) for v,l in incidences}
    def implied(label):
        if label[0] == 'w':
            _,i,k,a = label
            vertex,line = 3*i+a,33+k
        else:
            _,i,j,e,a = label
            owner,other,k = (i,j,e) if e < 3 else (j,i,e-3)
            vertex,line = 3*other+a,3*owner+k
        return (find(vp,vertex),find(lp,line)) in normalized
    return implied, events


def contact_catalog(box, equations, local_radius):
    """Prove root feasibility and exhaust the branches near that exact root."""
    if local_radius.lo != local_radius.hi or local_radius.lo <= 0:
        raise ValueError('Positive exact neighborhood radius required')
    implied, events = incidence_closure(box, equations)
    wide = [I(x.lo-local_radius.lo, x.hi+local_radius.hi) for x in box]
    if wide[-1].lo <= 0:
        raise ValueError('Nonpositive container radius in neighborhood')
    geom = geometry(box)
    wide_geom = geometry(wide)
    walls, contacts, rows = [], [], {}
    wall_checks = 0
    for i in range(11):
        for k in range(5):
            for a in range(3):
                label = ('w',i,k,a)
                value,jac = row(box,label,geom)
                wall_checks += 1
                if implied(label):
                    walls.append(label)
                    rows[label] = jac
                elif value.lo <= 0:
                    raise ValueError('Root wall feasibility not proved: '+str(label))
    positive_pairs = 0
    excluded = []
    for i in range(11):
        for j in range(i+1,11):
            features = [[row(box,('p',i,j,e,a),geom) for a in range(3)] for e in range(6)]
            strictly_separated = any(all(f.lo > 0 for f,jac in branch) for branch in features)
            if strictly_separated:
                positive_pairs += 1
                continue
            options = []
            for e,branch in enumerate(features):
                blocking = [a for a,(f,jac) in enumerate(branch) if f.hi < 0]
                if blocking:
                    witnesses = [(a,row(wide,('p',i,j,e,a),wide_geom)[0]) for a in blocking]
                    witness = next(((a,f) for a,f in witnesses if f.hi < 0), None)
                    if witness is None:
                        raise ValueError('An excluded contact branch is not excluded throughout neighborhood')
                    excluded.append(dict(pair=[i,j],edge=e,vertex=witness[0],upper=dec_grid(witness[1].hi)))
                    continue
                active = []
                for a,(f,jac) in enumerate(branch):
                    label = ('p',i,j,e,a)
                    if implied(label):
                        active.append(label)
                        rows[label] = jac
                    elif f.lo <= 0:
                        raise ValueError('Unresolved contact feature at root: '+str(label))
                if not active:
                    raise ValueError('Contact branch has no proved zero feature')
                options.append(dict(edge=e,rows=active))
            if not options:
                raise ValueError('Root pair separation not proved')
            contacts.append(dict(pair=[i,j],options=options))
    # For a displacement ||d||inf=t, translations change by <=2t per
    # coordinate, |omega|<=t, |omega_other-omega_owner|<=2t. Unit normals
    # imply |F''[d,d]| <= (||center_other-center_owner||1+12)*t^2.
    # Taylor's integral remainder is at most half this bound; walls need .5.
    center_distance = max(sum(magnitude(wide[3*i+k]-wide[3*j+k]) for k in (0,1))
                          for i in range(11) for j in range(i+1,11))
    remainder = I.point(Fraction(center_distance, D)+12)/2
    return dict(walls=walls,contacts=contacts,rows=rows,incidence_events=events,
                excluded_edges=excluded,positive_pairs=positive_pairs,wall_checks=wall_checks,
                remainder_bound=I(remainder.hi,remainder.hi),center_distance_l1_upper=center_distance)
