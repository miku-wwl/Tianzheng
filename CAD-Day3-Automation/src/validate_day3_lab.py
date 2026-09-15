from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
SCREENSHOTS = ROOT / "screenshots"
LOGS = ROOT / "logs"
DOCS = ROOT / "docs"
SRC = ROOT / "src"

EXPECTED_CREATED = {
    "AcDbLine": 4,
    "AcDbCircle": 1,
    "AcDbText": 1,
    "AcDbPolyline": 1,
}
EXPECTED_FINAL = {
    "AcDbLine": 4,
    "AcDbText": 1,
    "AcDbPolyline": 1,
}
FORMAL_SCREENSHOTS = (
    "01_created_entities.png",
    "02_line_properties.png",
    "03_polyline_properties.png",
    "04_entity_query.png",
    "05_before_modify.png",
    "06_after_modify.png",
    "07_after_delete.png",
    "08_reopened_drawing.png",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def is_png(path: Path) -> bool:
    return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def main() -> None:
    report = json.loads((LOGS / "day3_execution_report.json").read_text(encoding="utf-8"))
    query_log = (LOGS / "entity_query.txt").read_text(encoding="utf-8")

    for path in (
        SRC / "day3_automation.lsp",
        SRC / "AutoCadDotNetExample.cs",
        DOCS / "DAY3_AUTOCAD_AUTOMATION_TUTORIAL.md",
        OUTPUT / "day3_created.dwg",
        OUTPUT / "day3_modified.dwg",
    ):
        require(path.exists() and path.stat().st_size > 0, f"Missing or empty required artifact: {path}")

    require(report["lisp_loaded"] is True, "Execution report does not record a loaded AutoLISP program")
    require(report["created"]["types"] == EXPECTED_CREATED, "Created entity counts differ from the required inventory")
    require(report["modified"]["types"] == EXPECTED_CREATED, "Modified entity counts should retain the circle before delete")
    require(report["deleted"]["types"] == EXPECTED_FINAL, "Deleted entity counts do not show the circle removed")
    require(report["reopened"]["types"] == EXPECTED_FINAL, "Reopened DWG inventory differs from final inventory")

    modified = {row["handle"]: row for row in report["modified"]["entities"]}
    require(modified["84"]["startpoint"] == [0.0, 300.0, 0.0], "Line 84 was not moved by 300")
    require(modified["88"]["layer"] == "DAY3-CHANGED" and modified["88"]["radius"] == 650.0,
            "Circle 88 was not moved to the changed layer with radius 650")
    require(modified["89"]["textstring"] == "DAY 3 AUTOMATION", "Text 89 was not updated")

    for section in ("=== AFTER CREATE ===", "=== AFTER MODIFY ===", "=== AFTER DELETE ==="):
        require(section in query_log, f"Missing query section: {section}")
    require("CIRCLE x 0" in query_log, "Query log does not prove the circle deletion")

    for filename in FORMAL_SCREENSHOTS:
        path = SCREENSHOTS / filename
        require(path.exists() and path.stat().st_size > 1024 and is_png(path), f"Invalid evidence screenshot: {path}")

    print("DAY3_VALIDATION_PASS")
    print("CREATE: PASS")
    print("QUERY: PASS")
    print("MODIFY: PASS")
    print("DELETE: PASS")
    print("SAVE: PASS")
    print("REOPEN: PASS")


if __name__ == "__main__":
    main()
