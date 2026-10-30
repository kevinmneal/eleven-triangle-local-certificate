"""Exact standard-library consumer for a local eleven-triangle theorem.

The input supplies untrusted decimal centers, inverse proposals and weights.
All acceptance inequalities use outward-rounded integer intervals. It proves
an exact contact packing and a stated local growth bound, never global
optimality or a new record. See source_local_proof.md for the argument.
"""
from fractions import Fraction
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path

from hardened_checker import _decimal_scalar, _unique_object, _reject_nonfinite
from research.source_local_intervals import (
    I, D, PI, RHO, sincos, dec_grid, magnitude, values, matvec, matmul,
    residual_identity, infinity_norm_bound, root_box, contact_catalog,
)


def scalar(text, label):
    _decimal_scalar(text,label)
    value = I.point(Fraction(text))
    if value.lo != value.hi:
        raise ValueError(label+': proposal must be exact on the arithmetic grid')
    return value


def matrix(data, rows, cols, label):
    if type(data) is not list or len(data) != rows or any(type(row) is not list or len(row) != cols for row in data):
        raise ValueError(label+': bad dimensions')
    return [[scalar(x,label) for x in row] for row in data]


def branch_bound(C, weights, left_inverse, remainder, radius):
    m = len(C)
    if m < 34 or any(len(row) != 34 for row in C):
        raise ValueError('Invalid branch derivative dimensions')
    if len(weights) != m or any(w.lo <= 0 or w.lo != w.hi for w in weights):
        raise ValueError('Strictly positive exact stress weights required')
    if len(left_inverse) != 34 or any(len(row) != m for row in left_inverse):
        raise ValueError('Invalid branch left-inverse dimensions')
    delta = infinity_norm_bound(residual_identity(matmul(left_inverse,C)))
    if delta >= D:
        raise ValueError('Branch left-inverse defect is too large')
    lnorm = infinity_norm_bound(left_inverse)
    inverse_bound = I.point(Fraction(lnorm,D)) / I.point(Fraction(D-delta,D))
    residual = matvec(list(map(list,zip(*C))),weights)
    residual[-1] = residual[-1]-1
    epsilon = I.point(Fraction(sum(map(magnitude,residual)),D))
    minimum_weight = I(min(w.lo for w in weights),min(w.lo for w in weights))
    sum_weights = sum(weights,I.point(0))
    kappa = minimum_weight / inverse_bound - epsilon
    quadratic = remainder*(minimum_weight+sum_weights)
    # For t<=radius, dR >= (kappa - quadratic*radius)*t.
    growth = kappa-quadratic*radius
    if kappa.lo <= 0 or growth.lo <= 0:
        raise ValueError('Strict local radius growth is not proved')
    return dict(left_inverse_defect=dec_grid(delta), inverse_norm_bound=dec_grid(inverse_bound.hi),
        minimum_weight=dec_grid(minimum_weight.lo), sum_weights=dec_grid(sum_weights.hi),
        stress_residual_l1_bound=dec_grid(epsilon.hi), kappa_lower=dec_grid(kappa.lo),
        quadratic_upper=dec_grid(quadratic.hi), radius_growth_lower=dec_grid(growth.lo))


def check(data):
    if type(data) is not dict or data.get('schema') != 'eleven-triangle-source-local-v1':
        raise ValueError('Unsupported local-certificate schema')
    if data.get('target') != {'container_sides':5,'piece_sides':3,'piece_count':11,'inner_circumradius':1}:
        raise ValueError('Wrong packing problem')
    if any(type(v) is not int for v in data['target'].values()):
        raise ValueError('Target counts must be strict integers')
    root = data['root']
    if type(root.get('center')) is not list or len(root['center']) != 34:
        raise ValueError('Exactly 34 center coordinates required')
    center = [scalar(x,'root center') for x in root['center']]
    labels = root['rows']
    if type(labels) is not list or any(type(x) is not list for x in labels):
        raise ValueError('Root labels must be arrays')
    radius = scalar(root['radius'],'root radius')
    inverse = matrix(root['inverse'],34,34,'root inverse')
    root_verdict = root_box(center,radius,labels,inverse)
    box = root_verdict['box']
    local_radius = scalar(data['local_radius'],'local radius')
    catalog = contact_catalog(box,labels,local_radius)
    if catalog['wall_checks'] != 165 or catalog['positive_pairs']+len(catalog['contacts']) != 55:
        raise ValueError('Incomplete root feasibility coverage')
    combinations = list(itertools.product(*[contact['options'] for contact in catalog['contacts']]))
    witnesses = data.get('branches')
    if type(witnesses) is not list or len(witnesses) != len(combinations):
        raise ValueError('Missing or extra local branch witness')
    records = []
    for index,(selection,witness) in enumerate(zip(combinations,witnesses)):
        edges = [x['edge'] for x in selection]
        if witness.get('selected_edges') != edges or any(type(x) is not int for x in witness['selected_edges']):
            raise ValueError('Branch order/coverage mismatch')
        row_labels = catalog['walls']+[label for option in selection for label in option['rows']]
        C = [catalog['rows'][label] for label in row_labels]
        if type(witness.get('weights')) is not list or len(witness['weights']) != len(C):
            raise ValueError('Wrong stress weight count')
        weights = [scalar(x,'weight') for x in witness['weights']]
        left = matrix(witness['left_inverse'],34,len(C),'left inverse')
        bounds = branch_bound(C,weights,left,catalog['remainder_bound'],local_radius)
        records.append(dict(index=index,selected_edges=edges,row_count=len(C),**bounds))
    growth = min(Fraction(x['radius_growth_lower']) for x in records)
    side = box[-1]*sincos(PI/5)[0]/sincos(PI/3)[0]
    return dict(status='PASS: exact contact packing and strict local minimum with quantified growth',
        target=data['target'], root_unique_in_box=True,
        root_box_radius=root['radius'],root_contraction_bound=dec_grid(root_verdict['contraction_bound']),
        root_image_radius_bound=dec_grid(root_verdict['image_radius_bound']),
        radius_interval=[dec_grid(box[-1].lo),dec_grid(box[-1].hi)],
        unit_side_container_side_interval=[dec_grid(side.lo),dec_grid(side.hi)],
        local_pose_and_radius_infinity_neighborhood=data['local_radius'],
        growth_statement='For every feasible labeled configuration q within the stated infinity distance of the exact root p, R(q)-R(p) >= growth_lower*||q-p||_infinity. Angles are independent and measured in radians in the local chart.',
        radius_growth_lower=str(growth),
        wall_inequalities=165,pair_nonoverlap_checks=55,strictly_separated_pairs=catalog['positive_pairs'],
        contact_pairs=len(catalog['contacts']),active_walls=len(catalog['walls']),
        complete_local_branch_count=len(records),excluded_contact_edges=len(catalog['excluded_edges']),
        center_distance_l1_upper=dec_grid(catalog['center_distance_l1_upper']),
        taylor_remainder_coefficient=dec_grid(catalog['remainder_bound'].hi),
        incidence_derivation=catalog['incidence_events'],branches=records,
        scope='LOCAL ONLY. No global lower bound, global optimality, novelty or new packing record is established.',
        grid_denominator=str(D))


def load(path):
    path = Path(path)
    raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
    return json.loads(raw,object_pairs_hook=_unique_object,parse_constant=_reject_nonfinite)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('certificate',type=Path)
    parser.add_argument('--out',type=Path)
    args = parser.parse_args()
    try:
        result = check(load(args.certificate))
        result['certificate_sha256'] = hashlib.sha256(args.certificate.read_bytes()).hexdigest()
        rendered = json.dumps(result,indent=2)+'\n'
        if args.out:
            if args.out.exists(): raise FileExistsError('Refusing to overwrite a saved verdict')
            args.out.write_text(rendered)
        else: print(rendered,end='')
    except Exception as error:
        raise SystemExit('FAIL: '+str(error))
