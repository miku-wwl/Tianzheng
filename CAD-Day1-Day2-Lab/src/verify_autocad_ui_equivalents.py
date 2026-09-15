from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import time

import win32com.client

from run_autocad_lab import LAB, OUTPUT, NOTES, SCREENSHOTS, capture_window, inventory, open_document, wait_for_com


def safe_get(obj, attr: str):
    try:
        return getattr(obj, attr)
    except Exception:
        return None


def entity_properties(entity) -> dict:
    return {
        "object_name": str(safe_get(entity, "ObjectName")),
        "layer": str(safe_get(entity, "Layer")),
        "handle": str(safe_get(entity, "Handle")),
        "color": safe_get(entity, "Color"),
        "linetype": str(safe_get(entity, "Linetype")),
        "lineweight": safe_get(entity, "Lineweight"),
    }


def layer_properties(doc) -> list[dict]:
    rows = []
    for layer in doc.Layers:
        rows.append({
            "name": str(safe_get(layer, "Name")),
            "color": safe_get(layer, "Color"),
            "linetype": str(safe_get(layer, "Linetype")),
            "layer_on": safe_get(layer, "LayerOn"),
            "freeze": safe_get(layer, "Freeze"),
            "lock": safe_get(layer, "Lock"),
        })
    return sorted(rows, key=lambda row: row["name"])


def document_spaces(doc) -> dict:
    layouts = []
    for layout in doc.Layouts:
        layouts.append({
            "name": str(safe_get(layout, "Name")),
            "tab_order": safe_get(layout, "TabOrder"),
        })
    return {
        "active_space": safe_get(doc, "ActiveSpace"),
        "tilemode": safe_get(doc, "GetVariable")("TILEMODE") if safe_get(doc, "GetVariable") else None,
        "active_layout": str(safe_get(safe_get(doc, "ActiveLayout"), "Name")),
        "model_space_count": len(list(doc.ModelSpace)),
        "paper_space_count": len(list(doc.PaperSpace)),
        "layouts": layouts,
    }


def send_command_and_capture(app, doc, command: str, screenshot_name: str, wait_seconds: float = 3.0) -> dict:
    result = {"command": command, "sent": False, "screenshot": False, "error": None}
    try:
        wait_for_com(doc.Activate)
        doc.SendCommand(command + "\n")
        result["sent"] = True
        time.sleep(wait_seconds)
        result["screenshot"] = capture_window(app, SCREENSHOTS / screenshot_name)
    except Exception as exc:
        result["error"] = str(exc)
    return result


def main() -> None:
    app = win32com.client.GetActiveObject("AutoCAD.Application.26")
    app.Visible = True

    report = {
        "collected_at": datetime.now().astimezone().isoformat(),
        "autocad_version": str(app.Version),
        "executable": str(app.FullName),
        "native_cua_available": False,
        "documents": [],
        "ui_command_attempts": [],
        "limitations": [
            "Native Windows click/element automation was unavailable; these are AutoCAD COM and command-interface checks, not mouse-click evidence.",
            "The Properties command can open the palette, but selecting a specific object through the native palette was not simulated as a click.",
        ],
    }

    targets = [
        (OUTPUT / "day2_line_based.dwg", "line"),
        (OUTPUT / "day2_polyline_based.dwg", "polyline"),
    ]
    for path, label in targets:
        doc = open_document(app, path)
        inv = inventory(doc)
        wall_entities = [entity for entity in doc.ModelSpace if str(safe_get(entity, "Layer")) == "A-WALL"]
        sample_entities = []
        for entity in doc.ModelSpace:
            if len(sample_entities) >= 6:
                break
            sample_entities.append(entity_properties(entity))
        report["documents"].append({
            "label": label,
            "path": str(path),
            "object_type_counts": inv["type_counts"],
            "sample_properties": sample_entities,
            "a_wall_properties": [entity_properties(entity) for entity in wall_entities],
            "layers": layer_properties(doc),
            "spaces": document_spaces(doc),
        })

        report["ui_command_attempts"].append({
            "document": label,
            "properties": send_command_and_capture(app, doc, "_.PROPERTIES", f"06_autocad_properties_{label}.png"),
            "layers": send_command_and_capture(app, doc, "_.LAYER", f"07_autocad_layers_{label}.png", wait_seconds=4.0),
        })
        paper_result = {"command": "_.TILEMODE 0", "sent": False, "screenshot": False, "error": None}
        try:
            wait_for_com(doc.Activate)
            doc.SendCommand("_.TILEMODE\n0\n")
            paper_result["sent"] = True
            time.sleep(4)
            paper_result["screenshot"] = capture_window(app, SCREENSHOTS / f"08_autocad_paper_space_{label}.png")
            paper_result["state_after_command"] = document_spaces(doc)
            doc.SendCommand("_.TILEMODE\n1\n")
            time.sleep(3)
        except Exception as exc:
            paper_result["error"] = str(exc)
        report["ui_command_attempts"][-1]["paper_space"] = paper_result

    (NOTES / "autocad_ui_equivalent_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "AutoCAD UI-equivalent verification",
        "===================================",
        f"Collected: {report['collected_at']}",
        f"Version: {report['autocad_version']}",
        f"Executable: {report['executable']}",
        "",
        "This report uses AutoCAD COM and SendCommand; it is not native mouse-click evidence.",
    ]
    for doc_report in report["documents"]:
        lines += [
            "",
            f"[{doc_report['label']}] {doc_report['path']}",
            f"Object types: {doc_report['object_type_counts']}",
            f"A-WALL properties: {doc_report['a_wall_properties']}",
            f"Spaces: {doc_report['spaces']}",
            f"Layers: {doc_report['layers']}",
        ]
    lines += ["", "UI command attempts:"]
    lines.extend(json.dumps(item, ensure_ascii=False) for item in report["ui_command_attempts"])
    lines += ["", "Limitations:"]
    lines.extend(f"- {item}" for item in report["limitations"])
    (NOTES / "autocad_ui_equivalent_check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("AUTOCAD_UI_EQUIVALENT_CHECK_PASS")
    print(json.dumps(report["ui_command_attempts"], ensure_ascii=True))


if __name__ == "__main__":
    main()
