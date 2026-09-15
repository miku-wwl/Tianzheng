from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import time

import pythoncom
import win32com.client

from run_day3_autocad_lab import (
    OUTPUT,
    SCREENSHOTS,
    LOGS,
    capture_autocad,
    select_and_capture_properties,
    wait_until_idle,
)


def find_or_open(app, path: Path):
    target = str(path.resolve()).lower()
    for doc in app.Documents:
        if str(doc.FullName).lower() == target:
            doc.Activate()
            wait_until_idle(app)
            return doc
    doc = app.Documents.Open(str(path.resolve()), True)
    wait_until_idle(app)
    doc.Activate()
    wait_until_idle(app)
    return doc


def type_counts(doc) -> dict[str, int]:
    return dict(sorted(Counter(str(entity.ObjectName) for entity in doc.ModelSpace).items()))


def zoom_extents(app) -> None:
    try:
        lower_left = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, (-800.0, -1000.0, 0.0)
        )
        upper_right = win32com.client.VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, (9000.0, 5000.0, 0.0)
        )
        app.ZoomWindow(lower_left, upper_right)
        time.sleep(2)
        wait_until_idle(app)
    except Exception:
        pass


def close_matching_document(app, path: Path) -> None:
    target = str(path.resolve()).lower()
    for doc in list(app.Documents):
        if str(doc.FullName).lower() == target:
            doc.Close(False)
            wait_until_idle(app)
            return


def main() -> None:
    created = OUTPUT / "day3_created.dwg"
    after_modify = OUTPUT / "day3_after_modify_before_delete.dwg"
    final = OUTPUT / "day3_modified.dwg"
    for path in (created, after_modify, final):
        if not path.exists():
            raise FileNotFoundError(path)

    app = win32com.client.GetActiveObject("AutoCAD.Application.26")
    app.Visible = True
    wait_until_idle(app)

    created_doc = find_or_open(app, created)
    zoom_extents(app)
    created_saved = capture_autocad(app, SCREENSHOTS / "01_created_entities.png")
    line_properties = select_and_capture_properties(app, created_doc, "AcDbLine", "02_line_properties.png")
    polyline_properties = select_and_capture_properties(app, created_doc, "AcDbPolyline", "03_polyline_properties.png")
    created_doc.SendCommand("_.PROPERTIESCLOSE\n")
    wait_until_idle(app)
    before_modify_saved = capture_autocad(app, SCREENSHOTS / "05_before_modify.png")

    modified_doc = find_or_open(app, after_modify)
    zoom_extents(app)
    modified_counts = type_counts(modified_doc)
    after_modify_saved = capture_autocad(app, SCREENSHOTS / "06_after_modify.png")

    final_doc = find_or_open(app, final)
    zoom_extents(app)
    after_delete_counts = type_counts(final_doc)
    after_delete_saved = capture_autocad(app, SCREENSHOTS / "07_after_delete.png")

    # Reopen the real final DWG once more, rather than merely reusing an already-open tab.
    close_matching_document(app, final)
    reopened_doc = app.Documents.Open(str(final.resolve()), False)
    wait_until_idle(app)
    reopened_doc.Activate()
    wait_until_idle(app)
    zoom_extents(app)
    reopened_counts = type_counts(reopened_doc)
    reopened_saved = capture_autocad(app, SCREENSHOTS / "08_reopened_drawing.png")

    report = {
        "collected_at": datetime.now().astimezone().isoformat(),
        "created_counts": type_counts(created_doc),
        "after_modify_counts": modified_counts,
        "after_delete_counts": after_delete_counts,
        "reopened_counts": reopened_counts,
        "line_properties": line_properties,
        "polyline_properties": polyline_properties,
        "screenshots": {
            "01_created_entities.png": created_saved,
            "02_line_properties.png": line_properties["saved"],
            "03_polyline_properties.png": polyline_properties["saved"],
            "05_before_modify.png": before_modify_saved,
            "06_after_modify.png": after_modify_saved,
            "07_after_delete.png": after_delete_saved,
            "08_reopened_drawing.png": reopened_saved,
        },
        "note": "day3_after_modify_before_delete.dwg is a non-destructive copy of AutoCAD's generated .bak file, used only to capture the verified post-modification/pre-deletion state.",
    }
    (LOGS / "day3_screenshot_recovery_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DAY3_SCREENSHOT_RECOVERY_PASS")
    print(json.dumps(report["screenshots"], ensure_ascii=True))


if __name__ == "__main__":
    main()
