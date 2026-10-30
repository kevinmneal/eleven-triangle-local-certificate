# Mathematical audit of the source local-optimality consumer

9 October 2026. **Accept the stated local theorem for the checked v2 artifact.**
I found no mathematical or arithmetic acceptance gap in the inspected consumer.
An independent standard-library replay with assertions disabled passed all 256
branches. The result is a strict local minimum in the stated coordinate
neighborhood; it is not a global minimum, a new source construction, or a new
packing record.

This audit inspected `check_source_local.py`,
`research/source_local_intervals.py`, and the arithmetic/trigonometric kernel
imported from `hardened_checker.py`. It independently reasoned through root
existence, every incidence rule, separator coverage, the derivative and Taylor
bounds, and the residual-aware growth inequality. The replay executes the same
consumer, rather than a second implementation of its entire proof. A separate
checker/code audit covers implementation tests and additional mutations.

## Artifact and replay binding

The reviewed certificate is `certificates/source_local_v2.json.gz`, SHA-256
`680ecd966e5391810df5d0d5782d9c78a3016e9f1c2544a4147f8af36353d4a8`.

Reviewed consumer hashes:

| File | SHA-256 |
| --- | --- |
| `check_source_local.py` | `56da30f41a2741208ab850b49bd8d439c839388226bf83e1cf27ec11d2363f7d` |
| `research/source_local_intervals.py` | `cce30170260c74847ddb434662185bbefa90a167033ad1b31db5f99a2a649258` |
| `hardened_checker.py` | `03f08966df9f03c6437f74bccf9b5426e3d40341a0e6e8bc1130e13cbb523ed7` |

The independent replay ran `python3 -B -S -O check_source_local.py` against v2
and wrote `verification/source_local_independent_math_replay.json`. It returned
exit code zero in approximately 5.91 wall-clock seconds. All four hashes were
unchanged before and after replay. The timing/hash record is
`verification/source_local_math_audit_replay_metadata.json`.

The replay proves an exact root in a box of coordinate radius `1e-24`, with
root-map contraction below `3.723e-15` and image radius below `3.723e-39`.
Its unit-side container-side enclosure is

```
[1.871814755164470141324697303905737649597897564590010074843743,
 1.871814755164470141324698661337632196603720100538979125264435].
```

It checks all 165 vertex/wall inequalities and all 55 triangle pairs: 38 pairs
are strictly separated at the root, and 17 have contacts. There are 12 active
wall rows, 256 enumerated local contact branches, and 77 excluded owned-edge
alternatives checked throughout the local neighborhood. Every branch matrix
has 36 rows and 34 physical-coordinate columns.

Let `p` be that exact root. In the internal unit-circumradius coordinate chart,
all translations and all eleven angles are independent, angles are in radians,
and the final coordinate is container radius R. A convenient conservative
statement supported by the replay is:

```
For every feasible labeled q with ||q-p||_infinity <= 1e-7,

R(q) - R(p) >= 0.000011159 * ||q-p||_infinity.
```

The consumer's exact rational lower bound is slightly stronger than this
decimal coefficient. The strict comparison with `0.000011159` is retained in
`verification/source_local_math_audit_checks.json`.

## Root existence and binding to the geometry

The input's decimal center, inverse, and row choices are proposals, not trusted
root facts. The consumer requires 34 distinct valid feature rows and checks
their values and full Jacobian over the proposed box. With rational inverse
proposal Y it verifies both

`sup_X ||I-Y DF(x)||_infinity < 1`

and strict self-mapping of `T(x)=x-YF(x)` into X. The interval evaluation of
`T(x)-x0` correctly uses `-YF(x0)+(I-Y DF(X))(X-x0)` and outward rounding.
Banach contraction therefore supplies exactly one fixed point in X.
Because `Y DF(x)` is invertible under the same norm bound, the square matrix Y
is invertible; its fixed point is an actual `F=0` root. Conversely every zero
in X is a fixed point. The unique-root claim is justified.

The analytic rows match the physical geometry. The outward normal of triangle
edge k is `-u_i,k`; its line has offset one half from the center. The pair row
is `(-u_owner,k) dot (c_other+u_other,a-c_owner)-1/2`. Its owner-angle
derivative rotates the owner normal, and its other-angle derivative rotates
the other vertex. Wall derivatives and the `cos(pi/5)` radius derivative also
have the correct signs. No global rotation or translation gauge is removed.

Every incidence added from a supplied row is consequently true at the same
certified root. Incidence closure is run on that root's box and those same
equations. It is not run on an unrelated floating endpoint or a tolerance-based
contact graph.

## Exact geometric closure

The closure engine's initial incidences are identities for exact equilateral
triangles and exact wall/contact equalities at the root. Its three inference
rules are sound:

1. Two distinct points determine one line. Distinctness is supplied either by
   two different vertices of the same nondegenerate triangle or by disjoint
   interval coordinate projections.
2. Two nonparallel lines have at most one common point. A determinant interval
   excluding zero proves nonparallelism. Both vertices already lie on both
   lines before they are identified.
3. Two triangle edges on the same line, with an identified common endpoint,
   have equal nonzero length `sqrt(3)`. A strictly positive interval dot
   product proves that their directed edge vectors point the same way.
   Collinearity, equal length, and common direction force the remaining
   endpoints to coincide.

Union-find representatives still denote original geometric points and lines;
their stored coordinate/normal intervals therefore remain valid after earlier
identifications. Transferring incidences across proved equivalence classes is
legitimate. The engine does not treat a small interval residual as an exact
zero. Its 16 successful inferences close the missing contact identities and
the alternative-owned support identities. The equal-length metric rule is
essential; pure incidence reasoning would not suffice for the shared-edge
endpoint conclusions.

The closure establishes exact zero features at the analytic root, whose
coordinates need not be finite decimals. The theorem does not claim that the
saved decimal center itself is a touching, locally optimal packing.

## Root feasibility and complete local branch coverage

For two closed convex triangles, nonoverlap of interiors is equivalent to
separation along at least one of the six owned-edge alternatives. This is the
planar polygon separating-axis statement: a supporting facet of the Minkowski
difference comes from an edge of one triangle. Each alternative requires all
three other-vertex features to be nonnegative. Contact is included by using
non-strict inequalities.

The catalog checks every wall vertex. It accepts a wall feature only when it
is an exact implied zero or has a positive interval lower bound. For each of
the 55 pairs it either finds a strictly positive separating alternative or
checks all six owned-edge alternatives. A retained alternative has only exact
zero or strictly positive support features, which proves separation at p.

For each rejected alternative of a contact pair, at least one support feature
has a negative upper bound throughout `X+[-r,r]^34`. Since p lies in X, this
wide box contains every point within max-coordinate distance r of p and the
straight segment from p to that point. Thus rejected alternatives cannot
become viable anywhere in the claimed neighborhood.

Every nearby feasible q therefore chooses at least one retained alternative
for each of the 17 contact pairs. The consumer explicitly forms the Cartesian
product, checks its exact length against the witness list, and compares each
witness's edge choices with the actual combination. It retains all tied zero
support rows within each choice. Alternatives are not mistakenly intersected;
the 256 branches are separately certified.

Ignoring the 38 strictly separated pairs, inactive wall inequalities, and
strictly positive support rows in the growth proof is safe: this discards
constraints and makes the branch model an outer approximation to nearby
feasible configurations. These discarded inequalities need not stay positive
throughout the entire neighborhood for the lower-bound argument. Root
feasibility itself has already checked them at p.

## Uniform Taylor bound

Write a displacement as d, `t=||d||_infinity`, let D be the current difference
between two centers on the segment, and let `omega_o,omega_t` be the owner's
and other's angular displacement components. Direct differentiation gives

```
F''[d,d] = -omega_o^2 * (a dot D)
           + 2*omega_o * (J a dot (dc_t-dc_o))
           - (omega_t-omega_o)^2 * (u_t dot a).
```

Unit normals/vertices and coordinate bounds give, respectively,

```
|first term|  <= ||D||_1 * t^2
|cross term|  <= 8 * t^2
|last term|   <= 4 * t^2.
```

The cross-term coefficient 8 follows from two translation differences, each
at most `2t`, and `|omega_o|<=t`. The last coefficient uses
`|omega_t-omega_o|<=2t` and the exact unit-vector dot bound.
Taylor's integral remainder is at most one half the second-derivative bound.
For a wall feature the second derivative is at most `t^2`; the chosen common
coefficient is larger than its required one half.

The code independently bounds all center differences over the wide box and
sets `h=(Dmax_L1+12)/2`, rounded upwards. For v2 it verifies

```
Dmax_L1 <= 4.884428581989467393821257894355400739886313481
h       <= 8.4422142909947336969106289471777003699431567405.
```

Hence every branch's exact zero-row vector satisfies
`g(p+d)=Cd+e`, with `|e_i|<=h*t^2`, uniformly over the claimed neighborhood.
This bound handles arbitrary independent rotations; it imposes no contact
preservation on the intervening segment.

## Residual-aware branch growth bound

The consumer uses the exact rational entries of the proposed positive stress
lambda and proposed left inverse L. It computes interval enclosures for the
true branch Jacobian C at p, then certifies

```
delta >= ||I-LC||_infinity < 1
M >= ||L||_infinity/(1-delta)
epsilon >= ||C^T lambda-e_R||_1
a = min(lambda_i) > 0.
```

For every d, the first bound gives `||d||_infinity <= M ||Cd||_infinity`.
For a feasible point in this branch, `g>=0`. Therefore

```
R(p+d)-R(p)
  = lambda^T g - lambda^T e + (e_R-C^T lambda)^T d
 >= a*||g||_infinity - h*sum(lambda)*t^2 - epsilon*t
 >= (a/M-epsilon)*t - h*(a+sum(lambda))*t^2.
```

The final step uses `||g||_infinity >= ||Cd||_infinity-h*t^2`.
The implementation uses the correct induced infinity norm for the matrix
defect/inverse and the correct one-norm for the stress residual. It does not
silently assume exact stress equilibrium. The positive-stress and full-column-
rank conclusions follow from the checked inequalities, not floating solver
statuses or singular values.

With `kappa=a/M-epsilon`, the code proves `kappa-h*(a+sum(lambda))*r>0` for
every branch and takes the minimum exact rational lower bound. Interval
division, subtraction, and multiplication all round in the safe direction.
This proves the displayed strict linear growth bound for every `0<t<=r` and
equality at `t=0`. No differentiable feasible path, second-order critical-cone
assumption, or optimizer convergence is required.

## Arithmetic and rejection behavior

Acceptance computations use integer endpoints on the `10^-60` grid and
`Fraction` rational arithmetic. Pi is enclosed by the Machin/arctangent
construction; sine/cosine enclosures use the degree-100 Taylor polynomial with
the explicit `8^101/101!` remainder and reject angles outside `[-8,8]`.
Natural interval dependency only enlarges enclosures. The actual v2 root and
wide box stay in the permitted angular range.

Root centers, inverse proposals, weights, and local radius must be finite
decimal strings exactly representable on this arithmetic grid. Matrix shapes,
integer indices, positive weights, distinct root equations, target counts,
branch coverage, and positive growth are explicitly checked. JSON duplicate
keys and nonfinite constants are rejected. No acceptance condition relies on
Python assertions, and the successful independent replay used `-O`.

As a targeted mathematical mutation, I changed only the local radius from
`1e-7` to `1e-5` in memory. The consumer rejected it with
`Strict local radius growth is not proved`. This confirms that acceptance of
the supplied neighborhood is obtained from the quantified inequality rather
than simply copying the requested radius. The mutation result is retained in
`verification/source_local_math_audit_checks.json`; the original certificate
was not modified.

## Limits

This is an audited computer-assisted local theorem for the identified root and
the exact checked artifacts. It does not prove global optimality, enlarge the
neighborhood beyond `1e-7`, identify every local minimum, establish uniqueness
up to distant relabelings/isometries, or demonstrate novelty. It is not a Lean
formalization or external peer review. The mathematical argument and arithmetic
consumer are reviewable; the supplied floating proposal generation carries no
proof authority.

No source input, accepted checker, certificate, or consumer was edited during
this audit. The new files contain only this audit, the independent replay,
hash/timing metadata, and the targeted in-memory mutation result. No nonlinear
packing search or dependency installation occurred.
