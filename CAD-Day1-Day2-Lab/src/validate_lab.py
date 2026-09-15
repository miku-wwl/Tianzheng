from __future__ import annotations

from collections import Counter
from pathlib import Path

import ezdxf


LAB = Path(__file__).resolve().parents[1]
OUTPUT = LAB / "output"
SCREENSHOTS = LAB / "screenshots"
NOTES = LAB / "notes"


def main() -> None:
    line_path = OUTPUT / "day2_line_based.dxf"
    poly_path = OUTPUT / "day2_polyline_based.dxf"
    assert line_path.exists(), line_path
    assert poly_path.exists(), poly_path

    line_doc = ezdxf.readfile(line_path)
    poly_doc = ezdxf.readfile(poly_path)
    line_counts = Counter(entity.dxftype() for entity in line_doc.modelspace())
    poly_counts = Counter(entity.dxftype() for entity in poly_doc.modelspace())

    wall_lines = [e for e in line_doc.modelspace() if e.dxf.get("layer") == "A-WALL"]
    wall_polylines = [e for e in poly_doc.modelspace() if e.dxf.get("layer") == "A-WALL"]
    assert len(wall_lines) == 4 and all(e.dxftype() == "LINE" for e in wall_lines)
    assert len(wall_polylines) == 1 and wall_polylines[0].dxftype() == "LWPOLYLINE"
    assert wall_polylines[0].closed
    assert line_counts["ARC"] == 1 and poly_counts["ARC"] == 1
    assert line_counts["DIMENSION"] == 2 and poly_counts["DIMENSION"] == 2
    assert line_counts["TEXT"] >= 1 and poly_counts["TEXT"] >= 1
    assert (NOTES / "entity_inventory.txt").exists()
    expected_previews = {
        "01_ezdxf_line_preview.png",
        "02_ezdxf_polyline_preview.png",
        "03_line_vs_polyline_comparison.png",
    }
    expected_autocad_evidence = {
        "06_autocad_properties_line.png",
        "06_autocad_properties_polyline.png",
        "07_autocad_layers_line.png",
        "07_autocad_layers_polyline.png",
        "08_autocad_paper_space_line.png",
        "08_autocad_paper_space_polyline.png",
        "10_properties_selected_line_focused.png",
        "10_properties_selected_arc_focused.png",
        "10_properties_selected_text_focused.png",
        "10_properties_selected_dimension_focused.png",
        "10_properties_selected_polyline_focused.png",
        "04_autocad_line_overview.png",
        "05_autocad_polyline_overview.png",
    }
    formal_screenshots = expected_previews | expected_autocad_evidence
    actual_previews = {p.name for p in SCREENSHOTS.glob("*.png") if p.name in formal_screenshots}
    assert expected_previews.issubset(actual_previews)

    print("VALIDATION_PASS")
    print(f"LINE_EXPERIMENT: {dict(line_counts)}")
    print(f"POLYLINE_EXPERIMENT: {dict(poly_counts)}")
    print("A_WALL_MODEL: 4 LINE")
    print("B_WALL_MODEL: 1 closed LWPOLYLINE")
    print(f"SCREENSHOTS: {sorted(actual_previews)}")


if __name__ == "__main__":
    main()
