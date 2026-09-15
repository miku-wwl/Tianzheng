from __future__ import annotations

from collections import Counter
from pathlib import Path
import math

import ezdxf
from ezdxf.enums import TextEntityAlignment


LAB = Path(__file__).resolve().parents[1]
OUTPUT = LAB / "output"
SCREENSHOTS = LAB / "screenshots"
NOTES = LAB / "notes"

LAYERS = {
    "A-WALL": 7,
    "A-DOOR": 2,
    "A-WINDOW": 4,
    "A-TEXT": 3,
    "A-DIMS": 1,
    "A-GRID": 6,
}


def configure_layers(doc: ezdxf.document.Drawing) -> None:
    for name, color in LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name=name, color=color)


def add_room_boundary(msp, mode: str) -> None:
    if mode == "lines":
        # The four main wall edges are intentionally four independent LINE entities.
        msp.add_line((0, 0), (6000, 0), dxfattribs={"layer": "A-WALL"})
        msp.add_line((6000, 0), (6000, 4000), dxfattribs={"layer": "A-WALL"})
        msp.add_line((6000, 4000), (0, 4000), dxfattribs={"layer": "A-WALL"})
        msp.add_line((0, 4000), (0, 0), dxfattribs={"layer": "A-WALL"})
    elif mode == "polyline":
        # The same visible boundary is one closed LWPOLYLINE entity.
        msp.add_lwpolyline(
            [(0, 0), (6000, 0), (6000, 4000), (0, 4000)],
            close=True,
            dxfattribs={"layer": "A-WALL"},
        )
    else:
        raise ValueError(f"Unknown boundary mode: {mode}")


def add_door(msp) -> None:
    # A primitive swing door at the bottom wall: 900 mm leaf + ARC swing.
    hinge = (2550, 0)
    msp.add_line(hinge, (2550, 900), dxfattribs={"layer": "A-DOOR"})
    msp.add_arc(
        center=hinge,
        radius=900,
        start_angle=0,
        end_angle=90,
        dxfattribs={"layer": "A-DOOR"},
    )
    # Short jamb marks make the opening readable without pretending it is a semantic Door.
    msp.add_line((2550, 0), (2550, 120), dxfattribs={"layer": "A-DOOR"})
    msp.add_line((3450, 0), (3450, 120), dxfattribs={"layer": "A-DOOR"})


def add_windows(msp) -> None:
    # Two simple 1200 mm window symbols on the upper wall.
    for x1, x2 in ((900, 2100), (3900, 5100)):
        msp.add_line((x1, 3940), (x2, 3940), dxfattribs={"layer": "A-WINDOW"})
        msp.add_line((x1, 4060), (x2, 4060), dxfattribs={"layer": "A-WINDOW"})
        msp.add_line((x1, 3940), (x1, 4060), dxfattribs={"layer": "A-WINDOW"})
        msp.add_line((x2, 3940), (x2, 4060), dxfattribs={"layer": "A-WINDOW"})


def add_labels(msp, mode: str) -> None:
    boundary_label = {
        "lines": "4 independent LINE entities",
        "polyline": "1 closed LWPOLYLINE entity",
    }[mode]
    office = msp.add_text(
        "OFFICE",
        dxfattribs={"layer": "A-TEXT", "height": 300},
    )
    office.set_placement((3000, 2100), align=TextEntityAlignment.MIDDLE_CENTER)

    note = msp.add_mtext(
        f"6000 x 4000 mm\\PWall concept: 200 mm\\PBoundary model: {boundary_label}",
        dxfattribs={"layer": "A-TEXT", "char_height": 120},
    )
    note.set_location((300, 3600), attachment_point=1)

    # A small grid marker keeps the A-GRID layer concrete without changing the lesson.
    msp.add_circle((5500, 650), 70, dxfattribs={"layer": "A-GRID"})
    grid_label = msp.add_text("G1", dxfattribs={"layer": "A-GRID", "height": 100})
    grid_label.set_placement((5500, 650), align=TextEntityAlignment.MIDDLE_CENTER)


def add_dimensions(msp) -> None:
    width = msp.add_linear_dim(
        base=(3000, -700),
        p1=(0, 0),
        p2=(6000, 0),
        dimstyle="Standard",
        dxfattribs={"layer": "A-DIMS"},
    )
    width.render()

    height = msp.add_linear_dim(
        base=(6800, 2000),
        p1=(6000, 0),
        p2=(6000, 4000),
        angle=90,
        dimstyle="Standard",
        dxfattribs={"layer": "A-DIMS"},
    )
    height.render()


def create_dxf(path: Path, mode: str) -> None:
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4  # millimetres
    configure_layers(doc)
    msp = doc.modelspace()
    add_room_boundary(msp, mode)
    add_door(msp)
    add_windows(msp)
    add_labels(msp, mode)
    add_dimensions(msp)
    doc.saveas(path)


def entity_summary(path: Path) -> tuple[Counter, list[str]]:
    doc = ezdxf.readfile(path)
    counts: Counter = Counter()
    details: list[str] = []
    for index, entity in enumerate(doc.modelspace(), start=1):
        kind = entity.dxftype()
        counts[kind] += 1
        layer = entity.dxf.get("layer", "0")
        detail = f"Object {index:03d} | Type: {kind:<12} | Layer: {layer}"
        if kind == "TEXT":
            detail += f" | Content: {entity.dxf.text}"
        elif kind == "MTEXT":
            detail += f" | Content: {entity.text.replace('\\P', ' / ')}"
        details.append(detail)
    return counts, details


def write_inventory(paths: list[Path]) -> None:
    lines = [
        "CAD Day 1 + Day 2 entity inventory",
        "====================================",
        "Units: millimetres (DXF header $INSUNITS=4)",
        "",
    ]
    for path in paths:
        counts, details = entity_summary(path)
        lines.append(path.name)
        lines.append("-" * len(path.name))
        for kind in sorted(counts):
            lines.append(f"{kind:<12} x {counts[kind]}")
        lines.append("")
        lines.extend(details)
        lines.append("")
    lines.extend(
        [
            "Interpretation",
            "--------------",
            "Experiment A has four independent LINE entities for the main room boundary.",
            "Experiment B has one closed LWPOLYLINE entity for the main room boundary.",
            "The files can therefore look almost identical while their entity data models differ.",
        ]
    )
    (NOTES / "entity_inventory.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_previews(paths: list[Path]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        (NOTES / "preview_note.txt").write_text(
            "matplotlib was unavailable; no raster previews were generated.\n",
            encoding="utf-8",
        )
        return

    def draw_doc(ax, path: Path, title: str) -> None:
        doc = ezdxf.readfile(path)
        colors = {
            "A-WALL": "#1f2937",
            "A-DOOR": "#dc2626",
            "A-WINDOW": "#2563eb",
            "A-TEXT": "#047857",
            "A-GRID": "#7c3aed",
        }
        for entity in doc.modelspace():
            layer = entity.dxf.get("layer", "0")
            color = colors.get(layer, "#6b7280")
            if entity.dxftype() == "LINE":
                a, b = entity.dxf.start, entity.dxf.end
                ax.plot([a.x, b.x], [a.y, b.y], color=color, linewidth=1.8)
            elif entity.dxftype() == "LWPOLYLINE":
                points = [(p[0], p[1]) for p in entity.get_points("xy")]
                if entity.closed:
                    points.append(points[0])
                ax.plot([p[0] for p in points], [p[1] for p in points], color=color, linewidth=1.8)
            elif entity.dxftype() == "ARC":
                center = entity.dxf.center
                radius = entity.dxf.radius
                start = math.radians(entity.dxf.start_angle)
                end = math.radians(entity.dxf.end_angle)
                if end < start:
                    end += 2 * math.pi
                samples = [start + (end - start) * i / 60 for i in range(61)]
                ax.plot(
                    [center.x + radius * math.cos(t) for t in samples],
                    [center.y + radius * math.sin(t) for t in samples],
                    color=color,
                    linewidth=1.8,
                )
            elif entity.dxftype() == "CIRCLE":
                center = entity.dxf.center
                circle = plt.Circle((center.x, center.y), entity.dxf.radius, fill=False, color=color)
                ax.add_patch(circle)
            elif entity.dxftype() == "TEXT":
                insert = entity.dxf.insert
                ax.text(insert.x, insert.y, entity.dxf.text, color=color, ha="center", va="center")
        ax.annotate("6000 mm", (3000, 0), (3000, -450), ha="center", va="top", color="#111827")
        ax.annotate("4000 mm", (6000, 2000), (6400, 2000), ha="left", va="center", color="#111827")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-800, 7400)
        ax.set_ylim(-1100, 4500)
        ax.grid(True, alpha=0.2)
        ax.set_xlabel("mm")
        ax.set_ylabel("mm")
        ax.set_title(title)

    for path, name, title in (
        (paths[0], "01_ezdxf_line_preview.png", "Experiment A — four LINE boundary"),
        (paths[1], "02_ezdxf_polyline_preview.png", "Experiment B — one closed LWPOLYLINE boundary"),
    ):
        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        draw_doc(ax, path, title)
        fig.tight_layout()
        fig.savefig(SCREENSHOTS / name, bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), dpi=150)
    for ax, title, label in (
        (axes[0], "Visual: same rectangle", "4 LINE entities"),
        (axes[1], "Visual: same rectangle", "1 closed LWPOLYLINE"),
    ):
        ax.plot([0, 6, 6, 0, 0], [0, 0, 4, 4, 0], color="#1f2937", linewidth=3)
        ax.text(3, 2, "OFFICE", ha="center", va="center", fontsize=12)
        ax.set_title(title)
        ax.text(3, -0.7, label, ha="center", va="top", color="#b91c1c", fontweight="bold")
        ax.set_aspect("equal")
        ax.set_xlim(-1, 7)
        ax.set_ylim(-1.2, 5)
        ax.axis("off")
    fig.suptitle("Same visual appearance, different CAD entity model", fontsize=14)
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "03_line_vs_polyline_comparison.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    line_path = OUTPUT / "day2_line_based.dxf"
    poly_path = OUTPUT / "day2_polyline_based.dxf"
    create_dxf(line_path, "lines")
    create_dxf(poly_path, "polyline")
    write_inventory([line_path, poly_path])
    make_previews([line_path, poly_path])
    print(f"Generated: {line_path}")
    print(f"Generated: {poly_path}")
    print(f"Inventory: {NOTES / 'entity_inventory.txt'}")


if __name__ == "__main__":
    main()
