"""Draw the saved local-proof construction; floating arithmetic is illustration only."""
import gzip
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CERTIFICATE = ROOT / "certificates/source_local_v2.json.gz"
VERDICT = ROOT / "verification/source_local_radius_1e_minus_7_verdict.json"
OUTPUT = ROOT / "figures/source_local_packing"
EXPECTED_CERTIFICATE_SHA256 = "680ecd966e5391810df5d0d5782d9c78a3016e9f1c2544a4147f8af36353d4a8"
PAIRS = [(1, 9), (3, 6), (7, 8)]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT.parents[1] / "work/matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import numpy as np

from geometry import boundary_vertices, vertices


def render():
    certificate_bytes = CERTIFICATE.read_bytes()
    certificate_hash = hashlib.sha256(certificate_bytes).hexdigest()
    assert certificate_hash == EXPECTED_CERTIFICATE_SHA256
    certificate = json.loads(gzip.decompress(certificate_bytes))
    verdict_bytes = VERDICT.read_bytes()
    verdict = json.loads(verdict_bytes)
    assert verdict["certificate_sha256"] == certificate_hash
    assert verdict["status"].startswith("PASS: exact contact packing and strict local minimum")
    assert verdict["root_unique_in_box"] is True
    assert verdict["complete_local_branch_count"] == 256
    assert certificate["target"] == dict(container_sides=5, piece_sides=3, piece_count=11, inner_circumradius=1)
    center_strings = certificate["root"]["center"]
    assert len(center_strings) == 34

    # This conversion is solely for drawing. It supplies no feasibility or proof test.
    center = np.array([float(x) for x in center_strings])
    poses, radius = center[:-1].reshape(11, 3), center[-1]
    scale = 1 / math.sqrt(3)
    triangles = vertices(poses, 3) * scale
    boundary = boundary_vertices(5, radius) * scale
    label_positions = poses[:, :2] * scale
    side_text = f"{float(verdict['unit_side_container_side_interval'][0]):.14f}"

    ink, muted = "#233540", "#5a6b75"
    neutral = "#e7ecef"
    pair_colors = ["#b4dce0", "#f2d4a3", "#decaea"]
    pair_edges = ["#227b84", "#a76d25", "#855798"]
    piece_colors = {piece: pair_colors[i] for i, pair in enumerate(PAIRS) for piece in pair}
    piece_edges = {piece: pair_edges[i] for i, pair in enumerate(PAIRS) for piece in pair}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "svg.fonttype": "none"})
    fig = plt.figure(figsize=(11.4, 9.3), facecolor="white")
    ax = fig.add_axes([.055, .20, .655, .65])
    ax.add_patch(Polygon(boundary, closed=True, facecolor="#fafbfc", edgecolor="none", zorder=0))
    for i, triangle in enumerate(triangles, 1):
        ax.add_patch(Polygon(triangle, closed=True,
                             facecolor=piece_colors.get(i, neutral),
                             edgecolor=piece_edges.get(i, "#65747d"),
                             linewidth=1.15, joinstyle="round", zorder=2))
    ax.add_patch(Polygon(boundary, closed=True, fill=False, edgecolor=ink,
                         linewidth=2.2, joinstyle="round", zorder=4))
    for i, (x, y) in enumerate(label_positions, 1):
        ax.text(x, y, str(i), ha="center", va="center", fontsize=14,
                weight="bold", color=ink, zorder=5)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(boundary[:, 0].min() - .09, boundary[:, 0].max() + .09)
    ax.set_ylim(boundary[:, 1].min() - .09, boundary[:, 1].max() + .09)
    ax.set_axis_off()

    fig.text(.063, .945, "Known construction: certified local minimum", fontsize=23,
             weight="bold", color=ink)
    fig.text(.063, .900, "Eleven unit-side equilateral triangles", fontsize=14, color=muted)
    fig.text(.063, .865, f"Regular pentagon side  s ≈ {side_text}", fontsize=14, color=ink)

    legend_x = .753
    fig.text(legend_x, .735, "Shared-edge rhombi", fontsize=13, color=ink, weight="bold")
    for i, pair in enumerate(PAIRS):
        y = .682 - .075 * i
        patch = Rectangle((legend_x, y - .012), .025, .027, transform=fig.transFigure,
                          facecolor=pair_colors[i], edgecolor=pair_edges[i], linewidth=1)
        fig.add_artist(patch)
        fig.text(legend_x + .040, y, f"Triangles {pair[0]} and {pair[1]}", fontsize=12,
                 va="center", color=ink)
    patch = Rectangle((legend_x, .441), .025, .027, transform=fig.transFigure,
                      facecolor=neutral, edgecolor="#65747d", linewidth=1)
    fig.add_artist(patch)
    fig.text(legend_x + .040, .453, "Other triangles", fontsize=12, va="center", color=ink)
    fig.text(legend_x, .382, "All 11 rotations remain\nindependent in the theorem.",
             fontsize=11, linespacing=1.55, color=muted)
    fig.text(legend_x, .291, "Global optimum\nremains open.", fontsize=15,
             weight="bold", linespacing=1.45, color=ink)

    fig.text(.063, .153,
             "Rounded illustration of the certified contact point. Exact arithmetic and neighborhood bounds are in the separate proof.",
             fontsize=10, color=muted)
    fig.text(.063, .122,
             "Highlighted rhombi describe the contact arrangement; the proof allows every triangle to translate and rotate independently.",
             fontsize=10, color=muted)
    fig.text(.063, .091,
             "Coordinates are scaled to unit triangle side. Removing the source's clearance does not supply a new packing record.",
             fontsize=10, color=muted)
    fig.text(.063, .050, "Certificate: source_local_v2.json.gz  ·  256 local contact branches checked", fontsize=9,
             color=muted)
    for ext in ["png", "svg"]:
        fig.savefig(OUTPUT.with_suffix("." + ext), dpi=180, facecolor="white")
    plt.close(fig)

    provenance = {
        "purpose": "Static illustration of the saved certified contact point; no discovery or proof calculation performed.",
        "certificate": str(CERTIFICATE.relative_to(ROOT)),
        "certificate_sha256": certificate_hash,
        "verdict": str(VERDICT.relative_to(ROOT)),
        "verdict_sha256": hashlib.sha256(verdict_bytes).hexdigest(),
        "verdict_status": verdict["status"],
        "exact_unit_side_interval_from_verdict": verdict["unit_side_container_side_interval"],
        "displayed_approximate_side": side_text,
        "source_coordinates": "certificate.root.center: 34 exact decimal strings; first 33 are 11 x,y,theta triples, last is pentagon circumradius",
        "drawing_geometry": "geometry.vertices and geometry.boundary_vertices in floating point, used only to draw",
        "drawing_normalization": "Multiply all planar coordinates by 1/sqrt(3), leaving angles unchanged, for unit triangle side",
        "labels": "One-based piece indices from the certificate",
        "highlighted_shared_edge_pairs": [list(pair) for pair in PAIRS],
        "local_radius_depicted_spatially": False,
        "scope": "Known construction and strict local result only; global optimality and packing novelty are not claimed.",
        "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "geometry_source_sha256": hashlib.sha256((ROOT / "geometry.py").read_bytes()).hexdigest(),
        "matplotlib_version": matplotlib.__version__,
        "numpy_version": np.__version__,
        "figure_sha256": {OUTPUT.with_suffix("." + ext).name: hashlib.sha256(OUTPUT.with_suffix("." + ext).read_bytes()).hexdigest() for ext in ["png", "svg"]},
    }
    OUTPUT.with_name(OUTPUT.name + "_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    render()
