from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import time

import win32com.client

from run_autocad_lab import NOTES, OUTPUT, SCREENSHOTS, capture_window, open_document, wait_for_com


def safe_get(obj, attr: str):
    try:
        return getattr(obj, attr)
    except Exception:
        return None


def send(doc, text: str, wait_seconds: float = 2.0) -> None:
    wait_for_com(doc.Activate)
    doc.SendCommand(text)
    time.sleep(wait_seconds)


def pickfirst_details(doc) -> list[dict]:
    try:
        pickfirst = doc.PickfirstSelectionSet
        rows = []
        for index in range(int(pickfirst.Count)):
            entity = pickfirst.Item(index)
            rows.append({
                "object_name": str(safe_get(entity, "ObjectName")),
                "layer": str(safe_get(entity, "Layer")),
                "handle": str(safe_get(entity, "Handle")),
            })
        return rows
    except Exception as exc:
        return [{"error": str(exc)}]


def select_by_handle(doc, handle: str) -> None:
    # sssetfirst updates AutoCAD's implied (pre-)selection set without editing geometry.
    expression = f'(progn (sssetfirst nil (ssadd (handent "{handle}"))) (princ))\n'
    send(doc, expression, wait_seconds=2.0)


def select_and_capture(app, doc, label: str, entity) -> dict:
    handle = str(entity.Handle)
    result = {
        "label": label,
        "expected_type": str(entity.ObjectName),
        "expected_layer": str(entity.Layer),
        "handle": handle,
        "preselection_sent": False,
        "properties_command_sent": False,
        "pickfirst_after_command": [],
        "screenshot": None,
        "error": None,
    }
    try:
        select_by_handle(doc, handle)
        result["preselection_sent"] = True
        result["pickfirst_after_command"] = pickfirst_details(doc)
        # PROPERTIES brings the palette to the foreground when it is already visible,
        # or opens it when it is not.
        send(doc, "_.PROPERTIES\n", wait_seconds=3.0)
        result["properties_command_sent"] = True
        shot = SCREENSHOTS / f"09_properties_selected_{label}.png"
        result["screenshot"] = str(shot)
        result["screenshot_saved"] = capture_window(app, shot)
    except Exception as exc:
        result["error"] = str(exc)
    return result


def main() -> None:
    app = win32com.client.GetActiveObject("AutoCAD.Application.26")
    app.Visible = True
    report = {
        "collected_at": datetime.now().astimezone().isoformat(),
        "version": str(app.Version),
        "selection_mechanism": "AutoLISP sssetfirst implied-selection set; not native mouse input",
        "records": [],
        "limitations": [
            "The selection was created by AutoCAD's internal preselection set, not by physical mouse input.",
            "Each record should be treated as Properties-palette evidence only when its screenshot visibly shows the selected object type.",
        ],
    }

    line_doc = open_document(app, OUTPUT / "day2_line_based.dwg")
    send(line_doc, "_.TILEMODE\n1\n", wait_seconds=2.0)
    samples_a = [
        ("line", next(entity for entity in line_doc.ModelSpace if str(entity.ObjectName) == "AcDbLine" and str(entity.Layer) == "A-WALL")),
        ("arc", next(entity for entity in line_doc.ModelSpace if str(entity.ObjectName) == "AcDbArc")),
        ("text", next(entity for entity in line_doc.ModelSpace if str(entity.ObjectName) == "AcDbText" and str(entity.TextString) == "OFFICE")),
        ("dimension", next(entity for entity in line_doc.ModelSpace if str(entity.ObjectName) == "AcDbRotatedDimension")),
    ]
    for label, entity in samples_a:
        report["records"].append(select_and_capture(app, line_doc, label, entity))

    poly_doc = open_document(app, OUTPUT / "day2_polyline_based.dwg")
    send(poly_doc, "_.TILEMODE\n1\n", wait_seconds=2.0)
    polyline = next(entity for entity in poly_doc.ModelSpace if str(entity.ObjectName) == "AcDbPolyline" and str(entity.Layer) == "A-WALL")
    report["records"].append(select_and_capture(app, poly_doc, "polyline", polyline))

    (NOTES / "autocad_properties_preselection.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "AutoCAD Properties verification through internal preselection",
        "============================================================",
        f"Collected: {report['collected_at']}",
        f"Version: {report['version']}",
        f"Selection mechanism: {report['selection_mechanism']}",
    ]
    for record in report["records"]:
        lines += ["", json.dumps(record, ensure_ascii=False)]
    lines += ["", "Limitations:"]
    lines.extend(f"- {item}" for item in report["limitations"])
    (NOTES / "autocad_properties_preselection.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("AUTOCAD_PROPERTIES_PRESELECTION_PASS")
    print(json.dumps(report["records"], ensure_ascii=True))


if __name__ == "__main__":
    main()
