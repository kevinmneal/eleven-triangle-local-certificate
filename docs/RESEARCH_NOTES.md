# Research notes and stopping point

The durable result in this release is the exact local theorem. The broader
project attempted both improved constructions and global optimality, without
achieving either. The summaries below are project history; the raw exploratory
archives are not included and are not needed for the theorem.

## Sustained rearrangement search

A fixed 30 October 2026 comparison started both methods from the same polished
known construction. Sixteen paired chains compared contact-guided group
release with relocation proposals. All triangles stayed full-sized and the
pentagon was allowed at most 0.5% side expansion during reconstruction.

| Method | Trials | Numerical restorations | Certified improvement leads |
|---|---:|---:|---:|
| Contact-guided shaking | 14,457 | 10,867 | 0 |
| Relocation comparison | 20,924 | 11,260 | 0 |

Search used 14,077.344515 aggregate CPU seconds in 59.08 elapsed minutes.
Separate exact checking used 43.680089 CPU seconds and accepted 448 distinct
saved endpoints plus the common source. The larger counts of numerical
restorations are not all exact-certified endpoints. Retaining the source was
not counted as discovery.

Three relocation variants passed a numerical change screen, but symmetry and
label alignment showed small distortions of the familiar packing. Their
largest center movements were at most 0.00154 triangle sides and angle changes
at most 0.175 degrees. Changes in a tolerance-based contact graph did not
establish a new dense packing pattern or a distinct optimization basin.

No improvement lead reached the predeclared 1e-7 side-reduction threshold.
The best saved side remained above the exact contact construction certified
in this repository. This is a negative result for the fixed tested procedures,
not evidence that all shaking, lifting or rearrangement methods must fail.

## Global proof work

The project constructed reusable, exactly checked exclusions for portions of
a larger search. A later diagnostic found a finite assignment satisfying the
entire accepted reusable rule bank for one open branch. That assignment is
not a physical packing, but it shows that the unchanged finite model remains
satisfiable: adding proof logging alone cannot make it an exclusion proof.
Further geometric restrictions or complete refinement would be necessary.

Partial exclusions and counts of rules do not measure distance to a global
proof. No practical completion-time estimate was established. The global
optimality question remains unresolved.

## Stopping decision

The sustained allocation is closed. Repeating it unchanged has no demonstrated
path to a materially stronger result. This release makes the independently
replayable local theorem available as a modest, useful stopping point.
It does not present the unsuccessful search campaign as a solved packing
problem, a new construction or a generally superior search method.
