# Independent audit of the local source certificate kernel

**Decision: accept the reviewed v2 consumer for its stated local theorem.** I found no mathematical or implementation blocker in the interval root argument, incidence closure, exhaustive local contact catalog, or residual-aware growth bound. The complete v2 certificate passed an independent, unmocked consumer replay through all 256 branches. All **32** new regression and mutation tests pass.

This is a certificate for an exact packing and a strict local minimum near that packing. It does not provide a global lower bound, global optimality, a new record, or a formal proof-assistant development. The limiting construction removes the old source's small numerical clearance; that alone is not geometric novelty.

## Reviewed identities and reproducibility

| File | SHA256 reviewed |
|---|---|
| `hardened_checker.py` | `03f08966df9f03c6437f74bccf9b5426e3d40341a0e6e8bc1130e13cbb523ed7` |
| `research/source_local_intervals.py` | `cce30170260c74847ddb434662185bbefa90a167033ad1b31db5f99a2a649258` |
| `check_source_local.py` | `56da30f41a2741208ab850b49bd8d439c839388226bf83e1cf27ec11d2363f7d` |
| `research/source_local_root_proposal.json` | `1122559bbc821a50e7bd016ebb0adecc073b2501014e41ad89d204c0b49f10a1` |
| `research/source_template_reconstruction.json` | `c0bf182cd0bf29d8f103a3e579776f9a79ea167dd56dd47d63aff10685a21dee` |
| `certificates/source_local_v2.json.gz` | `680ecd966e5391810df5d0d5782d9c78a3016e9f1c2544a4147f8af36353d4a8` |
| `test_source_local_intervals.py` | `41954aa78e7b5cd0d10cadc6e98ec76e07a3a7312f0d2ee771aa11e81a14ab8a` |

Run the new suite from the project directory with:

```text
../../work/.venv/bin/python -B -m unittest -v test_source_local_intervals
```

The final run passed 32 tests in **12.907 seconds**. The suite and consumer use the standard library. Tests modify only in-memory copies of the actual certificate and temporary invalid JSON fixtures. This audit changes no kernel, checker, source certificate, reconstruction, historical experiment or incoming Pro file.

The saved full verdict reports a root-box radius `1e-24`, root contraction bound below `3.73e-15`, image radius below `3.73e-39`, and a local infinity-neighborhood radius `1e-7`. Its minimum growth coefficient is greater than `0.00001115964`. The test's full consumer pass verifies positive growth and complete 256/55/165 coverage without trusting those displayed rounded numbers.

## Interval geometry and root argument

The new kernel imports the unchanged, previously audited grid interval arithmetic and certified trigonometric enclosures from `hardened_checker.py`. It makes no floating-point acceptance decision. The new exact-zero product shortcuts are valid: they skip a multiplication only when both endpoints of an operand equal zero. Tests include subgrid-width and zero-straddling intervals so that “near zero” cannot silently receive the same treatment.

For a pair feature, the implementation uses outward normal `n=-u_owner,k`, with value

`n · (c_other + u_other,a − c_owner) − 1/2`.

Its owner-angle derivative rotates the normal as well as retaining the other vertex's position. The other-angle derivative rotates that vertex. Translation derivatives and wall derivatives have the correct signs and units. This is the full independent-rotation derivative, not a derivative with frozen owner axes.

An independent reference constructs each edge from its two endpoints, obtains the outward normal by rotating that edge and dividing by the exact side length, then projects from an edge endpoint. Complex-step checks at a deliberately off-contact state cover **1,155 feature values and 39,270 derivative entries**. Maximum discrepancies were `2.22e-15` and `2.66e-15`, respectively. Separate interval tests enclose feature and derivative values at interior samples of a finite coordinate box. These numerical tests check implementation; the interval operations supply the proof bounds.

For the root map, let `F` be the 34 selected feature equations and `C` the proposed inverse. The consumer checks

`||I − C DF(X)||_infinity < 1`

on the complete closed box X, and verifies that `x0 − C F(x0) + (I − C DF(X))(X − x0)` lies strictly inside X. The mean-value theorem and the interval matrix enclosure give a contraction of `T(x)=x−CF(x)` on X. Banach's theorem supplies a unique fixed point. Because `C DF(x)` is invertible when its distance from identity is below one, C is invertible; therefore the fixed point is an actual `F=0` root. Conversely, every root in X is a fixed point, giving uniqueness in X.

The supplied inverse is an untrusted proposal. Its entries do not need to be a numerically accurate inverse by assumption: the contraction and inclusion inequalities validate their use. The retained source proposal passes those inequalities. Tests reject a zero inverse, an incorrectly permuted equation/inverse association, duplicate equations, uncertain centers, zero radius, contraction equal to one, and an image that merely touches the box boundary.

## Incidence closure and its premise boundary

The closure rules are sound for genuine circumradius-one equilateral triangles:

1. Two **distinct** common points identify an infinite line. Distinct vertices of one triangle are known distinct; other distinctions require disjoint coordinate intervals.
2. Two common **nonparallel** lines identify a point. The determinant interval must exclude zero.
3. Two triangle edges have the same nonzero length. If they lie on the same line, have a proved common endpoint and their vectors from that endpoint have strictly positive dot product, their other endpoints coincide. Collinearity plus positive direction distinguishes this conclusion from the opposite-direction case.

The union-find representation preserves these exact equivalences. Once a point or line is merged, any representative remains a valid object for subsequent normal, coordinate or incidence checks. No numerical smallness test creates an equality.

The helper `incidence_closure` is conditional: it does not establish or independently validate its input equations. The reviewed consumer satisfies this premise by passing **exactly the same root rows** through the validated root construction and then into `contact_catalog`. The final consumer also parses exact decimal strings and validates root labels before closure. Passing additional unproved equations directly to this helper would be outside its contract.

On the source, the closure derives **55 pair-feature incidences and twelve wall incidences**, including the two equations omitted from the square root system. These are 55 features, not 55 pairwise nonoverlap checks; some incidences concern extensions of edges. They must not be substituted for the separate all-pairs feasibility verification.

Tests verify that every derived zero's interval contains zero, and that the resulting incidence set matches the saved reconstruction's pattern. More decisively, deleting **each of the 34 independent premises in turn** prevents the omitted premise from being re-derived. Supplying no equations gives no cross-triangle or wall incidences, even inside the tiny source box. Synthetic same-direction and opposite-direction examples exercise the equal-edge rule, and a single common point cannot merge two lines.

## Complete root feasibility and local branch coverage

`contact_catalog` checks all 165 wall features. Each must either be an exactly derived incidence or have strictly positive lower bound. For every one of the 55 pairs, it verifies the complete three-support condition on a separating owner edge. At the root, 38 pairs have a strictly positive separating branch; the other 17 pairs have exact zero supports plus strictly positive remaining supports.

For each of those 17 contact pairs, every one of its six owner-edge choices is accounted for. An excluded edge has a feature whose upper bound is negative throughout the full neighborhood, not only at the root. Every retained alternative keeps all its zero supports. The complete product is 256 branches; 77 individual owner-edge choices are excluded by certified negative witnesses. The tests verify the disjoint kept/excluded partition of all six edges for each contact pair.

Ignoring the other 38 pair constraints in the local lower-bound argument is safe: it only enlarges the set to which the bound is applied. Their root feasibility is still checked. Their remaining separated throughout the neighborhood is unnecessary for this argument.

An incidence list without the proved root equations fails the root wall checks. A deliberately excessive `0.1` neighborhood fails the negative-edge exclusion checks. The consumer computes its own contact rows and branch ordering; certificate-provided branch selectors cannot silently remove alternatives.

## Hessian remainder and residual-aware growth bound

Let `t=||h||_infinity`. Each translation-coordinate difference changes at speed at most `2t`; each angular speed is at most t, and relative angular speed at most `2t`. For a pair feature, the second derivative consists of:

- the rotating-normal/center term, bounded by `||c_other−c_owner||_1 t²`;
- the normal/translation cross term, bounded by `8t²`;
- the relative-angle term, bounded by `4t²`.

Thus `M=(Dmax+12)/2` is a valid uniform Taylor remainder coefficient when Dmax bounds center L1 distance over the root box enlarged by the local radius. The code computes that enlarged-domain bound. A wall needs only `1/2`, which is covered by M. The segment from the exact root to any configuration in the stated infinity neighborhood lies in that domain.

The growth argument correctly permits imperfect proposed stresses. Let A be an actual branch Jacobian at the exact root, L its proposed left inverse, and positive lambda its proposed stress. The interval consumer obtains

`K >= ||L||_infinity/(1−||I−LA||_infinity)`

and `epsilon >= ||A^T lambda−e_R||_1`. Hence `||Ah||_infinity >= t/K`. For feasible h, set `y=Ah`; Taylor's theorem gives every `y_i >= −Mt²`. With `a=min lambda_i` and `Lambda=sum lambda_i`,

`lambda·y >= a ||y||_infinity − (a+Lambda) M t²`.

One way to see this is to add `Mt²` to each component, apply the positive weights to the resulting nonnegative vector, then use the triangle inequality. The stress residual contributes at most `epsilon t`, so

`R(p+h)−R(p) >= (a/K−epsilon)t − (a+Lambda)Mt²`.

This is precisely the implemented `kappa` and `quadratic` bound. The consumer requires a positive lower bound after subtracting `quadratic * local_radius`. Taking the minimum over all complete branches gives the stated strict local minimum and quantified growth for every feasible labeled configuration in that neighborhood. All eleven rotations remain independent.

## Trust-boundary mutations

The new suite uses the actual compressed v2 certificate and rejects:

- missing, extra and duplicated branch witnesses, including a same-length replacement;
- a Boolean edge selector that otherwise compares equal to integer one;
- zero or negative stress weights and a zero left-inverse matrix;
- doubling every positive weight, which must fail through the equilibrium-residual penalty rather than positivity alone;
- a wrong target and a Boolean circumradius masquerading as integer one;
- floating geometry or weights, malformed scalars, nonfinite strings, and values that are not exact on the arithmetic grid;
- zero, negative, floating and subgrid local radii;
- a shifted root center, duplicate root equations, duplicate JSON keys and nonfinite JSON constants.

One positive-control test calls the full consumer without mocked proof calculations and checks all 256 actual branch certificates. To avoid repeatedly proving identical premises for negative parser/branch mutations, those tests cache only the exact already-validated root and catalog arguments. Changed root or radius arguments fall back to their real validation functions. This caching does not bypass the altered stress, left inverse, branch selector or parser being tested.

No known obligation remains within the reviewed consumer's stated **local** theorem. The independent full mathematical audit is recorded separately in `source_local_proof_audit.md`. Global exclusion, a wider geometric neighborhood, novelty, and public packaging remain separate work.
