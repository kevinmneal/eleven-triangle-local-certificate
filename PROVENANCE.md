# Packet provenance

The public release extracts the compact 9 October 2026 local-proof packet
from a separate research archive. It contains everything needed to replay
the stated 1e-7 local theorem; none of the global-search machinery is required.

The original `PACKET_MANIFEST.json` SHA-256 was:

```text
d767e8e8413d3599ad9aeece4cdc6e9b93ef1b36000b9ba99d93021f8e6336c6
```

For this public extraction, `certificate/READ_ME_FIRST.md` was updated to
describe the release and `certificate/PACKET_MANIFEST.json` was updated to
hash that introduction, remove a machine-specific source path, and record
the original manifest identity. **Every other packet file retains its original
bytes**, including proof code, exact certificate, mathematical derivation,
audits, accepted verdicts, tests, source data and figures. The original
private snapshot remains unchanged.

The exact local certificate SHA-256 is:

```text
680ecd966e5391810df5d0d5782d9c78a3016e9f1c2544a4147f8af36353d4a8
```

Its exact-root proposal and inverse/stress witnesses are untrusted inputs to
the consumer. The fresh proof replay checks them; these hashes alone do not
establish the theorem. `RELEASE_MANIFEST.json` identifies the public release
files, and `tools/check_release.py` checks their identities. Neither replaces
the exact mathematical replay.

The numerical starting coordinates come from the authors' repository at
revision `27f71632d8655ae4b6a049410a401976748b94e3`. The included source audit
records a byte-for-byte comparison. It also mentions the ten-triangle
neighbor, which was checked during the original source audit; that neighbor
is not needed or included in this packet. The construction attribution is
preserved in the main README and theorem document.

The historical 134-test log covers a larger earlier research checkout. The
public packet contains **32 local-proof tests**, which are rerun for this
release. Numerical plotting dependencies are optional and never imported by
the proof commands. The included internal reviews use the same consumer and
arithmetic components; no external peer review is claimed.

`validation/` records the fresh public-packet replay. The short research notes
report later negative search outcomes as project history. Their large raw
search archives are not part of this release, so those experiment summaries
are not independently reproducible from this repository alone. They are not
premises of the local theorem.
