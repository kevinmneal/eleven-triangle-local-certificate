# Eleven triangles: a verified strict local minimum

This public packet proves a local theorem for the limiting contact version
of the known eleven-triangle packing in a regular pentagon. The side is about
1.87181475516447 when each triangle has side one. Every independent translation
and rotation is allowed in a max-coordinate neighborhood of radius 1e-7, in the
source's unit-circumradius coordinates. Every distinct feasible point in that
neighborhood requires a larger pentagon.

**Global optimality remains open. This is not a new packing record.** The small
change from the source decimal construction removes its numerical clearance.

Read `source_local_proof.md` for the statement, derivation, illustration and
source attribution. The two audit reports in `research/` independently review
the mathematics and implementation. They replay the same consumer, rather than
providing a wholly independent second implementation or external peer review.

## Replay without third-party dependencies

From this extracted directory, Python 3.10 or newer suffices:

```sh
python3 -B -S -O verify_packet.py
python3 -B -S -m unittest -v test_source_local_intervals
```

The first command verifies file identities and freshly checks the complete
exact-root and local-minimum certificate, including all 256 contact branches.
It compares the fresh verdict with the saved accepted verdict. The second runs
32 regression and mutation tests, including another full certificate replay.
No nonlinear optimization, internet access or dependency installation is used.

The proof consumer can also be called directly:

```sh
python3 -B -S -O check_source_local.py certificates/source_local_v2.json.gz
```

The trusted computations are explicit rational comparisons with outward
rounding. Assertions are not used for proof acceptance. Decimal coordinates,
inverse matrices and positive weights are untrusted proposals checked by the
consumer. All eleven rotations remain independent.

## Scope and provenance

`PACKET_MANIFEST.json` hashes every included file except itself. Hashes establish
identity, not mathematical validity. The included 134-test log records the full
scratch project's test run; this selected packet contains the 32 local-proof
tests and their fixtures. Historical discovery trajectories and earlier proof
candidates remain in the canonical private project, not in this compact bundle.

Source attribution and pinned coordinate identity are in `sources/source_audit.json`.
The figure is a rounded illustration; its optional renderer uses the numerical
and plotting packages listed in `environment_lock.txt`, which are not required
for either proof command. Figure provenance identifies the original inputs.

The proof, code, certificates, audits and figures preserve the original
9 October 2026 packet bytes. This introduction and manifest metadata were
updated for public release on 30 October; see `../PROVENANCE.md`.
Reproduce derived files in a copy so the released artifact's identity remains
intact. Publication does not establish novelty or external peer review.
