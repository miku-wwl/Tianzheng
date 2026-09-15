from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys
import time

import win32com.client

from run_autocad_lab import NOTES, OUTPUT, SCREENSHOTS, capture_window, wait_for_com


def wait_until_idle(app, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            if bool(app.GetAcadState().IsQuiescent):
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("AutoCAD did not become idle after the command")


def send(app, doc, command: str, wait_seconds: float = 0.5) -> None:
    wait_until_idle(app)
    doc.SendCommand(command)
    time.sleep(wait_seconds)
    wait_until_idle(app)


def active_document_for(app, path: Path):
    target = str(path.resolve()).lower()
    for doc in app.Documents:
        if str(doc.FullName).lower() == target:
            wait_for_com(doc.Activate)
            wait_until_idle(app)
            return doc
    doc = wait_for_com(lambda: app.Documents.Open(str(path.resolve()), False))
    wait_until_idle(app)
    return doc


def selected_rows(doc) -> list[dict]:
    pickfirst = doc.PickfirstSelectionSet
    return [
        {
            "object_name": str(pickfirst.Item(index).ObjectName),
            "layer": str(pickfirst.Item(index).Layer),
            "handle": str(pickfirst.Item(index).Handle),
        }
        for index in range(int(pickfirst.Count))
    ]


def main() -> None:
    label = sys.argv[1] if len(sys.argv) == 2 else "line"
    targets = {
        "line": (OUTPUT / "day2_line_based.dwg", "AcDbLine", "A-WALL"),
        "arc": (OUTPUT / "day2_line_based.dwg", "AcDbArc", "A-DOOR"),
        "text": (OUTPUT / "day2_line_based.dwg", "AcDbText", "A-TEXT"),
        "dimension": (OUTPUT / "day2_line_based.dwg", "AcDbRotatedDimension", "A-DIMS"),
        "polyline": (OUTPUT / "day2_polyline_based.dwg", "AcDbPolyline", "A-WALL"),
    }
    if label not in targets:
        raise SystemExit("usage: capture_focused_properties.py [line|arc|text|dimension|polyline]")
    path, expected_type, expected_layer = targets[label]

    app = win32com.client.GetActiveObject("AutoCAD.Application.26")
    app.Visible = True
    doc = active_document_for(app, path)
    entity = next(
        item
        for item in doc.ModelSpace
        if str(item.ObjectName) == expected_type and str(item.Layer) == expected_layer
    )

    # These commands only alter palette visibility and current selection; they do not edit geometry.
    wait_for_com(doc.Activate)
    if int(doc.GetVariable("TILEMODE")) != 1:
        send(app, doc, "_.TILEMODE\n1\n")
    send(app, doc, "_.LAYERCLOSE\n")
    send(app, doc, "_.PROPERTIESCLOSE\n")
    lisp = f'(progn (sssetfirst nil (ssadd (handent "{entity.Handle}"))) (princ))\n'
    send(app, doc, lisp)
    selection = selected_rows(doc)
    send(app, doc, "_.PROPERTIES\n", wait_seconds=2.0)
    screenshot = SCREENSHOTS / f"10_properties_selected_{label}_focused.png"
    saved = capture_window(app, screenshot)

    report = {
        "collected_at": datetime.now().astimezone().isoformat(),
        "document": str(doc.FullName),
        "expected_type": expected_type,
        "expected_layer": expected_layer,
        "expected_handle": str(entity.Handle),
        "selection_method": "AutoLISP sssetfirst implied selection; not physical mouse input",
        "pickfirst_selection_after_command": selection,
        "properties_command": "_.PROPERTIES",
        "screenshot": str(screenshot),
        "screenshot_saved": saved,
    }
    (NOTES / f"autocad_properties_{label}_focused.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (NOTES / f"autocad_properties_{label}_focused.txt").write_text(
        "\n".join(f"{key}: {value}" for key, value in report.items()) + "\n",
        encoding="utf-8",
    )
    print("FOCUSED_PROPERTIES_PASS")
    print(json.dumps(report, ensure_ascii=True))


if __name__ == "__main__":
    main()
