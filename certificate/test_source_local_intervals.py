"""Independent regression/mutation checks for the local-root interval kernel.

No packing optimizer is called. The retained source root is replayed once;
synthetic maps test proof boundaries separately. Numerical derivative checks
are implementation tests, not a substitute for the interval proof.
"""
from __future__ import annotations

import cmath
import copy
from fractions import Fraction
import itertools
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import source_local_intervals as kernel
import check_source_local as consumer

ROOT = Path(__file__).resolve().parent
PROPOSAL = ROOT / 'research/source_local_root_proposal.json'
CERTIFICATE = ROOT / 'certificates/source_local_v2.json.gz'
I, D = kernel.I, kernel.D


def middle(x):
    return (x.lo + x.hi) / (2 * D)


def point(value):
    return I.point(str(value))


def all_labels():
    return ([['w', i, k, a] for i in range(11) for k in range(5) for a in range(3)]
            + [['p', i, j, e, a] for i in range(11) for j in range(i + 1, 11)
               for e in range(6) for a in range(3)])


def independent_polygon_features(z, labels):
    """Reference from actual edge endpoints, with complex-step compatibility.

    Unlike the tested pair formula, this constructs the directed edge normal
    from the other two owner vertices and subtracts one edge endpoint.
    """
    vertices = []
    for i in range(11):
        x, y, theta = z[3*i:3*i+3]
        vertices.append([(x + cmath.sin(theta + 2 * math.pi * a / 3),
                          y + cmath.cos(theta + 2 * math.pi * a / 3)) for a in range(3)])
    values = []
    for label in labels:
        if label[0] == 'w':
            _, i, k, a = label
            normal = (math.sin(2*math.pi*k/5), math.cos(2*math.pi*k/5))
            v = vertices[i][a]
            values.append(normal[0]*v[0] + normal[1]*v[1] + math.cos(math.pi/5)*z[-1])
        else:
            _, i, j, e, a = label
            owner, other, k = (i, j, e) if e < 3 else (j, i, e - 3)
            start, end = vertices[owner][(k + 1) % 3], vertices[owner][(k + 2) % 3]
            normal = (-(end[1] - start[1]) / math.sqrt(3),
                      (end[0] - start[0]) / math.sqrt(3))
            other_vertex = vertices[other][a]
            values.append(sum(normal[v] * (other_vertex[v] - start[v]) for v in range(2)))
    return values


def fraction_bounds(x):
    return Fraction(x.lo, D), Fraction(x.hi, D)


class MatrixAndGeometryTests(unittest.TestCase):
    def test_sparse_products_keep_nonzero_subgrid_and_zero_straddling_intervals(self):
        a = [[I(0, 0), I(-1, 1), I(0, 1)],
             [point('-2.125'), I(0, 0), point('0.37')]]
        b = [[point('1.7'), I(-D, D)],
             [point('-0.4'), point('3.125')],
             [point('4.2'), point('-5.5')]]
        result = kernel.matmul(a, b)
        for i in range(2):
            for j in range(2):
                low = high = Fraction(0)
                for k in range(3):
                    products = [x*y for x in fraction_bounds(a[i][k]) for y in fraction_bounds(b[k][j])]
                    low += min(products)
                    high += max(products)
                self.assertLessEqual(Fraction(result[i][j].lo, D), low)
                self.assertGreaterEqual(Fraction(result[i][j].hi, D), high)
        self.assertNotEqual((result[0][0].lo, result[0][0].hi), (0, 0))
        vector = [row[0] for row in b]
        self.assertEqual(kernel.matvec(a, vector), [row[0] for row in result])

    def test_matrix_shape_errors_are_not_silently_zipped(self):
        with self.assertRaises(ValueError):
            kernel.matvec([[point(1), point(2)]], [point(3)])
        with self.assertRaises(ValueError):
            kernel.matmul([[point(1)]], [[point(1), point(2)], [point(3)]])
        with self.assertRaises(ValueError):
            kernel.residual_identity([[point(1), point(2)]])

    def test_all_features_and_jacobian_against_independent_complex_edge_geometry(self):
        proposal = json.loads(PROPOSAL.read_text())
        # Deliberately leave the contact manifold to exercise the full formulas.
        floats = [float(x) + 0.013 * math.sin(i + 0.2) for i, x in enumerate(proposal['center'])]
        z = [point(x) for x in floats]
        labels = all_labels()
        actual = kernel.values(z, labels)
        reference = independent_polygon_features(floats, labels)
        maximum_value_error = max(abs(middle(v) - ref.real) for (v, _), ref in zip(actual, reference))
        maximum_jacobian_error = 0.
        h = 1e-25
        for coordinate in range(34):
            trial = list(map(complex, floats))
            trial[coordinate] += h * 1j
            reference = independent_polygon_features(trial, labels)
            maximum_jacobian_error = max(maximum_jacobian_error,
                max(abs(middle(j[coordinate]) - ref.imag / h) for (_, j), ref in zip(actual, reference)))
        self.assertLess(maximum_value_error, 2e-12)
        self.assertLess(maximum_jacobian_error, 2e-11)

    def test_interval_feature_and_derivative_bounds_contain_interior_samples(self):
        # Wide enough to exercise interval uncertainty, including rotated owners.
        proposal = json.loads(PROPOSAL.read_text())
        center = [point(x) for x in proposal['center']]
        radius = point('0.001').lo
        box = [I(x.lo-radius, x.hi+radius) for x in center]
        labels = [['p', 0, 8, e, a] for e in range(6) for a in range(3)]
        labels += [['p', 3, 10, e, a] for e in range(6) for a in range(3)]
        labels += [['w', 4, k, a] for k in range(5) for a in range(3)]
        bounds = kernel.values(box, labels)
        for sample in range(5):
            z = [I(x.lo + ((7*i + 3*sample) % 9 - 4)*radius//5,
                   x.hi + ((7*i + 3*sample) % 9 - 4)*radius//5) for i, x in enumerate(center)]
            for (value_bound, gradient_bound), (value, gradient) in zip(bounds, kernel.values(z, labels)):
                self.assertLessEqual(value_bound.lo, value.lo)
                self.assertGreaterEqual(value_bound.hi, value.hi)
                for a, b in zip(gradient_bound, gradient):
                    self.assertLessEqual(a.lo, b.lo)
                    self.assertGreaterEqual(a.hi, b.hi)

    def test_feature_labels_reject_boolean_reversed_and_out_of_range_indices(self):
        z = [point(0)] * 33 + [point(3)]
        labels = [['w', True, 0, 0], ['w', 0, -1, 0], ['w', 11, 0, 0],
                  ['w', 0, 0, 3], ['p', 1, 0, 0, 0], ['p', 0, 0, 0, 0],
                  ['p', 0, 1, 6, 0], ['p', 0, 1, 0, False], ['unknown', 0, 1, 0, 0]]
        for label in labels:
            with self.subTest(label=label), self.assertRaises(ValueError):
                kernel.row(z, label)


class RootMapBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.center = [point(0)] * 34
        self.labels = [['w', i // 15, (i % 15) // 3, i % 3] for i in range(34)]
        self.identity = [[point(int(i == j)) for j in range(34)] for i in range(34)]

    def linear_values(self, scale, target):
        def evaluate(z, labels):
            return [(scale*z[i] - target[i],
                     [scale if i == j else point(0) for j in range(34)]) for i in range(34)]
        return evaluate

    def test_synthetic_affine_root_is_proved(self):
        with patch.object(kernel, 'values', self.linear_values(point('0.5'), [point('0.1')] * 34)):
            result = kernel.root_box(self.center, point(1), self.labels, self.identity)
        self.assertEqual(result['contraction_bound'], D // 2)
        self.assertEqual(result['image_radius_bound'], 3 * D // 5)

    def test_contraction_equal_to_one_is_rejected(self):
        with patch.object(kernel, 'values', self.linear_values(point(2), [point(0)] * 34)):
            with self.assertRaisesRegex(ValueError, 'contraction'):
                kernel.root_box(self.center, point(1), self.labels, self.identity)

    def test_image_touching_box_boundary_is_rejected(self):
        # T(x)=x/2+1/2 touches the boundary; strict inclusion is not established.
        with patch.object(kernel, 'values', self.linear_values(point('0.5'), [point('0.5')] * 34)):
            with self.assertRaisesRegex(ValueError, 'strictly inside'):
                kernel.root_box(self.center, point(1), self.labels, self.identity)

    def test_zero_inverse_cannot_turn_arbitrary_equations_into_a_proof(self):
        with patch.object(kernel, 'values', self.linear_values(point(1), [point(7)] * 34)):
            with self.assertRaisesRegex(ValueError, 'contraction'):
                kernel.root_box(self.center, point(1), self.labels, [[point(0)] * 34 for _ in range(34)])

    def test_duplicate_rows_nongrid_center_and_zero_radius_are_rejected(self):
        duplicate = self.labels[:-1] + [self.labels[0]]
        with self.assertRaises(ValueError):
            kernel.root_box(self.center, point(1), duplicate, self.identity)
        uncertain = self.center.copy()
        uncertain[0] = I(0, 1)
        with self.assertRaises(ValueError):
            kernel.root_box(uncertain, point(1), self.labels, self.identity)
        with self.assertRaises(ValueError):
            kernel.root_box(self.center, point(0), self.labels, self.identity)


class IncidenceDirectionTests(unittest.TestCase):
    @staticmethod
    def triangles(second_center_x):
        z = []
        for i in range(11):
            z.extend([point(10*i), point(10*i), point(0)])
        z[0:3] = [point(0), point(0), point(0)]
        z[3:6] = [second_center_x, point(0), point(0)]
        z.append(point(100))
        return z

    def test_equal_collinear_edges_with_same_origin_and_direction_merge_other_endpoints(self):
        z = self.triangles(point(0))
        equations = [['p', 0, 1, 0, 1], ['p', 0, 1, 0, 2], ['p', 0, 1, 2, 1]]
        implied, events = kernel.incidence_closure(z, equations)
        self.assertTrue(implied(['p', 0, 1, 1, 2]))
        self.assertIn('equal_edges_common_origin_and_direction', {x['rule'] for x in events})

    def test_equal_collinear_edges_with_opposite_direction_do_not_merge_other_endpoints(self):
        # A and B have adjacent equal bottom edges, sharing A.v1 == B.v2.
        # Their vectors from that common endpoint have dot product -3.
        sqrt3 = 2 * kernel.sincos(kernel.PI * Fraction(2, 3))[0]
        z = self.triangles(sqrt3)
        equations = [['p', 0, 1, 0, 1], ['p', 0, 1, 0, 2], ['p', 0, 1, 2, 2]]
        implied, events = kernel.incidence_closure(z, equations)
        self.assertFalse(implied(['p', 0, 1, 1, 1]))
        self.assertNotIn('equal_edges_common_origin_and_direction', {x['rule'] for x in events})

    def test_one_common_point_does_not_identify_lines(self):
        # This one supplied vertex incidence must not merge either whole edge.
        implied, events = kernel.incidence_closure(self.triangles(point(0)), [['p', 0, 1, 0, 1]])
        self.assertTrue(implied(['p', 0, 1, 0, 1]))
        self.assertFalse(implied(['p', 0, 1, 0, 2]))
        self.assertEqual(events, [])


class RetainedSourceRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal = json.loads(PROPOSAL.read_text())
        cls.center = [point(x) for x in cls.proposal['center']]
        cls.radius = point(cls.proposal['root_radius'])
        cls.labels = cls.proposal['root_rows']
        cls.inverse = [[point(x) for x in row] for row in cls.proposal['inverse']]
        # The actual retained proposal is independently replayed exactly once.
        cls.root = kernel.root_box(cls.center, cls.radius, cls.labels, cls.inverse)
        implied, cls.events = kernel.incidence_closure(cls.root['box'], cls.labels)
        cls.implied = staticmethod(implied)

    def test_retained_source_root_has_strict_integer_margins(self):
        self.assertLess(self.root['contraction_bound'], D)
        self.assertLess(self.root['image_radius_bound'], self.radius.lo)
        self.assertGreater(self.radius.lo, 0)
        # Nontrivial regression guard without trusting displayed floating bounds.
        self.assertLess(self.root['contraction_bound'], D // 10**12)
        self.assertLess(self.root['image_radius_bound'], self.radius.lo // 10**12)

    def test_all_derived_source_incidences_have_zero_in_interval_and_match_saved_pattern(self):
        reconstruction = json.loads((ROOT / 'research/source_template_reconstruction.json').read_text())
        expected = {tuple(x) for x in reconstruction['all_near_zero_feature_labels']
                    + reconstruction['all_near_zero_wall_labels']}
        labels = all_labels()
        derived = {tuple(label) for label in labels if self.implied(label)}
        self.assertEqual(len(derived), 67)
        self.assertEqual(derived, expected)
        for label in derived:
            value, _ = kernel.row(self.root['box'], label)
            self.assertLessEqual(value.lo, 0)
            self.assertGreaterEqual(value.hi, 0)
        self.assertTrue(self.implied(['p', 3, 6, 2, 2]))
        self.assertTrue(self.implied(['p', 8, 9, 4, 1]))
        self.assertEqual({x['rule'] for x in self.events}, {
            'two_distinct_points_determine_line', 'two_nonparallel_lines_determine_point',
            'equal_edges_common_origin_and_direction'})

    def test_small_interval_residuals_without_equations_do_not_create_incidences(self):
        implied, events = kernel.incidence_closure(self.root['box'], [])
        self.assertFalse(any(implied(label) for label in all_labels()))
        self.assertEqual(events, [])

    def test_each_independent_root_equation_is_essential_to_its_own_incidence_proof(self):
        # Deleting any one premise must not be silently repaired from numerical
        # proximity to the source. The square Jacobian has full rank.
        for index, label in enumerate(self.labels):
            implied, _ = kernel.incidence_closure(self.root['box'], self.labels[:index] + self.labels[index+1:])
            with self.subTest(removed=label):
                self.assertFalse(implied(label))

    def test_permuting_equations_without_corresponding_inverse_is_rejected(self):
        labels = self.labels.copy()
        labels[0], labels[1] = labels[1], labels[0]
        with self.assertRaises(ValueError):
            kernel.root_box(self.center, self.radius, labels, self.inverse)

    def test_contact_catalog_covers_all_pairs_walls_and_every_local_edge_choice(self):
        catalog = kernel.contact_catalog(self.root['box'], self.labels, point('1e-7'))
        self.assertEqual(catalog['wall_checks'], 165)
        self.assertEqual((len(catalog['walls']), len(catalog['contacts']), catalog['positive_pairs']), (12, 17, 38))
        self.assertEqual(len(list(itertools.product(*[x['options'] for x in catalog['contacts']]))), 256)
        excluded = {}
        for edge in catalog['excluded_edges']:
            excluded.setdefault(tuple(edge['pair']), set()).add(edge['edge'])
            self.assertLess(Fraction(edge['upper']), 0)
        for contact in catalog['contacts']:
            kept = {option['edge'] for option in contact['options']}
            removed = excluded.get(tuple(contact['pair']), set())
            self.assertFalse(kept & removed)
            self.assertEqual(kept | removed, set(range(6)))
            self.assertTrue(all(option['rows'] for option in contact['options']))

    def test_catalog_does_not_use_small_residuals_without_proven_equations(self):
        with self.assertRaisesRegex(ValueError, 'Root wall feasibility'):
            kernel.contact_catalog(self.root['box'], [], point('1e-7'))

    def test_catalog_rejects_a_neighborhood_where_branch_exclusion_is_unproved(self):
        with self.assertRaisesRegex(ValueError, 'excluded contact branch'):
            kernel.contact_catalog(self.root['box'], self.labels, point('0.1'))


class FullConsumerTrustBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certificate = consumer.load(CERTIFICATE)
        # Negative schema/branch mutations do not require re-proving identical
        # premises each time. Cache only this exact, actually validated root and
        # catalog; changed root/radius arguments fall back to the real functions.
        root = cls.certificate['root']
        cls.root_args = ([consumer.scalar(x, 'center') for x in root['center']],
                         consumer.scalar(root['radius'], 'root radius'), root['rows'],
                         consumer.matrix(root['inverse'], 34, 34, 'inverse'))
        cls.root_verdict = kernel.root_box(*cls.root_args)
        cls.catalog_args = (cls.root_verdict['box'], root['rows'],
                            consumer.scalar(cls.certificate['local_radius'], 'local radius'))
        cls.catalog = kernel.contact_catalog(*cls.catalog_args)

    def reject(self, mutate, message):
        data = copy.deepcopy(self.certificate)
        mutate(data)
        def root_call(*args):
            return self.root_verdict if args == self.root_args else kernel.root_box(*args)
        def catalog_call(*args):
            return self.catalog if args == self.catalog_args else kernel.contact_catalog(*args)
        with patch.object(consumer, 'root_box', side_effect=root_call), \
                patch.object(consumer, 'contact_catalog', side_effect=catalog_call):
            with self.assertRaisesRegex(ValueError, message):
                consumer.check(data)

    def test_untouched_certificate_completes_all_256_actual_branch_checks(self):
        # One full consumer pass, without mocked proof calculations.
        verdict = consumer.check(self.certificate)
        self.assertEqual(verdict['complete_local_branch_count'], 256)
        self.assertEqual(verdict['pair_nonoverlap_checks'], 55)
        self.assertEqual(verdict['wall_inequalities'], 165)
        self.assertEqual(verdict['local_pose_and_radius_infinity_neighborhood'], '1e-7')
        self.assertGreater(Fraction(verdict['radius_growth_lower']), 0)
        self.assertEqual(len(verdict['branches']), 256)

    def test_missing_extra_and_duplicated_branch_witnesses_are_rejected(self):
        self.reject(lambda d: d['branches'].pop(), 'Missing or extra')
        self.reject(lambda d: d['branches'].append(d['branches'][0]), 'Missing or extra')
        self.reject(lambda d: d['branches'].__setitem__(0, d['branches'][1]), 'Branch order/coverage')

    def test_boolean_edge_selector_is_not_accepted_as_integer_one(self):
        self.assertEqual(self.certificate['branches'][0]['selected_edges'][0], 1)
        self.reject(lambda d: d['branches'][0]['selected_edges'].__setitem__(0, True), 'Branch order/coverage')

    def test_zero_and_negative_weights_are_rejected(self):
        for value in ['0', '-1e-30']:
            with self.subTest(value=value):
                self.reject(lambda d: d['branches'][0]['weights'].__setitem__(0, value), 'Strictly positive')

    def test_zero_left_inverse_is_rejected(self):
        def mutate(d):
            d['branches'][0]['left_inverse'] = [['0'] * 36 for _ in range(34)]
        self.reject(mutate, 'left-inverse defect')

    def test_positive_weights_do_not_bypass_the_equilibrium_residual_penalty(self):
        def mutate(d):
            d['branches'][0]['weights'] = [kernel.dec_grid(2 * point(x).lo)
                                          for x in d['branches'][0]['weights']]
        self.reject(mutate, 'Strict local radius growth')

    def test_wrong_target_and_boolean_circumradius_are_rejected(self):
        self.reject(lambda d: d['target'].__setitem__('piece_count', 10), 'Wrong packing problem')
        self.reject(lambda d: d['target'].__setitem__('inner_circumradius', True), 'strict integers')

    def test_float_geometry_and_malformed_or_nongrid_scalar_are_rejected(self):
        self.reject(lambda d: d['root']['center'].__setitem__(0, float(d['root']['center'][0])), 'decimal string')
        self.reject(lambda d: d['branches'][0]['weights'].__setitem__(0, 0.25), 'decimal string')
        self.reject(lambda d: d['root']['inverse'][0].__setitem__(0, '1/3'), 'decimal string')
        self.reject(lambda d: d['branches'][0]['left_inverse'][0].__setitem__(0, 'NaN'), 'decimal string')
        self.reject(lambda d: d['root']['center'].__setitem__(0, '1e-80'), 'arithmetic grid')

    def test_invalid_local_radii_are_rejected(self):
        for value in ['0', '-1e-7']:
            with self.subTest(value=value):
                self.reject(lambda d: d.__setitem__('local_radius', value), 'Positive exact neighborhood')
        self.reject(lambda d: d.__setitem__('local_radius', 1e-7), 'decimal string')
        self.reject(lambda d: d.__setitem__('local_radius', '1e-80'), 'arithmetic grid')

    def test_changed_root_geometry_and_duplicate_rows_are_not_trusted(self):
        self.reject(lambda d: d['root']['center'].__setitem__(0, '1.45'), 'Root map')
        self.reject(lambda d: d['root']['rows'].__setitem__(0, d['root']['rows'][1]), '34 distinct')

    def test_json_duplicate_keys_and_nonfinite_constants_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='packing-local-audit-') as directory:
            path = Path(directory) / 'bad.json'
            for raw, message in [(' {"x": 1, "x": 2}', 'duplicate'),
                                 ('{"x": NaN}', 'nonfinite')]:
                path.write_text(raw)
                with self.assertRaisesRegex(ValueError, message):
                    consumer.load(path)


if __name__ == '__main__':
    unittest.main()
