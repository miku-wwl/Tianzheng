from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import os
import time
import winreg

import win32com.client
import pythoncom
import win32gui
import win32process
from PIL import ImageGrab


LAB = Path(__file__).resolve().parents[1]
OUTPUT = LAB / "output"
SCREENSHOTS = LAB / "screenshots"
NOTES = LAB / "notes"


def installed_autodesk_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for root_path in (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ):
        try:
            root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root_path)
        except OSError:
            continue
        with root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                try:
                    sub_name = winreg.EnumKey(root, i)
                    sub = winreg.OpenKey(root, sub_name)
                except OSError:
                    continue
                with sub:
                    values = {}
                    for name in ("DisplayName", "DisplayVersion", "InstallLocation", "Publisher"):
                        try:
                            values[name] = str(winreg.QueryValueEx(sub, name)[0])
                        except OSError:
                            values[name] = ""
                    if "autodesk" in values["DisplayName"].lower() or "autocad" in values["DisplayName"].lower():
                        entries.append(values)
    return sorted(entries, key=lambda x: (x["DisplayName"], x["DisplayVersion"]))


def wait_for_com(callable_, attempts: int = 10, delay: float = 2.0):
    last_error = None
    for _ in range(attempts):
        try:
            return callable_()
        except Exception as exc:  # AutoCAD may temporarily reject RPC while busy.
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"AutoCAD COM call failed after retries: {last_error}")


def open_document(app, path: Path):
    full = str(path.resolve())
    for doc in list(app.Documents):
        try:
            if str(doc.FullName).lower() == full.lower():
                wait_for_com(doc.Activate)
                time.sleep(2)
                return doc
        except Exception:
            pass
    doc = wait_for_com(lambda: app.Documents.Open(full, False))
    wait_for_com(doc.Activate)
    time.sleep(4)
    return doc


def inventory(doc) -> dict:
    type_counts: Counter[str] = Counter()
    layer_counts: Counter[str] = Counter()
    details: list[str] = []
    index = 0
    for entity in doc.ModelSpace:
        index += 1
        obj_type = str(entity.ObjectName)
        layer = str(entity.Layer)
        type_counts[obj_type] += 1
        layer_counts[layer] += 1
        details.append(f"Object {index:03d} | Type: {obj_type} | Layer: {layer}")
    layers = []
    for layer in doc.Layers:
        try:
            color = int(layer.Color)
        except Exception:
            color = None
        layers.append({"name": str(layer.Name), "color": color})
    units = None
    try:
        units = int(doc.GetVariable("$INSUNITS"))
    except Exception:
        pass
    return {
        "name": str(doc.Name),
        "full_name": str(doc.FullName),
        "units_header": units,
        "type_counts": dict(sorted(type_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "layers": sorted(layers, key=lambda x: x["name"]),
        "details": details,
    }


def hwnd_for_app(app) -> int:
    hwnd = int(app.HWND)
    if hwnd:
        return hwnd
    candidates = []
    def callback(handle, _):
        if win32gui.IsWindowVisible(handle) and "AutoCAD" in win32gui.GetWindowText(handle):
            candidates.append(handle)
    win32gui.EnumWindows(callback, None)
    if not candidates:
        raise RuntimeError("No visible AutoCAD window found")
    return candidates[0]


def capture_window(app, path: Path) -> bool:
    try:
        hwnd = hwnd_for_app(app)
        win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(1)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        image = ImageGrab.grab(bbox=(left, top, right, bottom), include_layered_windows=True)
        image.save(path)
        return True
    except Exception as exc:
        path.with_suffix(path.suffix + ".error.txt").write_text(str(exc), encoding="utf-8")
        return False


def zoom_extents(app, doc) -> None:
    try:
        wait_for_com(doc.Activate)
        # Use a bounded window so the complete 6000 x 4000 room is visible in the capture.
        lower_left = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (-800.0, -1100.0, 0.0))
        upper_right = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (7400.0, 4500.0, 0.0))
        wait_for_com(lambda: app.ZoomWindow(lower_left, upper_right))
        time.sleep(3)
    except Exception:
        pass


def close_document_if_open(app, path: Path) -> None:
    target = str(path.resolve()).lower()
    for candidate in list(app.Documents):
        try:
            if str(candidate.FullName).lower() == target:
                wait_for_com(lambda: candidate.Close(False))
                time.sleep(1)
        except Exception:
            pass


def save_as_dwg(app, doc, path: Path) -> dict:
    result = {"path": str(path), "exists": False, "error": None}
    try:
        close_document_if_open(app, path)
        if path.exists():
            path.unlink()
        wait_for_com(lambda: doc.SaveAs(str(path)))
        time.sleep(3)
        result["exists"] = path.exists() and path.stat().st_size > 0
    except Exception as exc:
        result["error"] = str(exc)
    return result


def main() -> None:
    line_dxf = OUTPUT / "day2_line_based.dxf"
    poly_dxf = OUTPUT / "day2_polyline_based.dxf"
    line_dwg = OUTPUT / "day2_line_based.dwg"
    poly_dwg = OUTPUT / "day2_polyline_based.dwg"
    for path in (line_dxf, poly_dxf):
        if not path.exists():
            raise FileNotFoundError(path)

    # Attach to the existing AutoCAD instance through the Running Object Table.
    app = win32com.client.GetActiveObject("AutoCAD.Application.26")
    app.Visible = True

    line_doc = open_document(app, line_dxf)
    line_inventory = inventory(line_doc)
    zoom_extents(app, line_doc)
    line_shot_ok = capture_window(app, SCREENSHOTS / "04_autocad_line_overview.png")
    line_dwg_result = save_as_dwg(app, line_doc, line_dwg)

    poly_doc = open_document(app, poly_dxf)
    poly_inventory = inventory(poly_doc)
    zoom_extents(app, poly_doc)
    poly_shot_ok = capture_window(app, SCREENSHOTS / "05_autocad_polyline_overview.png")
    poly_dwg_result = save_as_dwg(app, poly_doc, poly_dwg)

    reopen_results = []
    reopen_inventories = {}
    for path in (line_dwg, poly_dwg):
        if not path.exists():
            reopen_results.append({"path": str(path), "opened": False, "error": "DWG not created"})
            continue
        try:
            doc = open_document(app, path)
            inv = inventory(doc)
            reopen_inventories[path.name] = inv
            reopen_results.append({"path": str(path), "opened": True, "entity_count": len(inv["details"]), "error": None})
        except Exception as exc:
            reopen_results.append({"path": str(path), "opened": False, "error": str(exc)})

    process_rows = []
    def enum_window(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if "AutoCAD" in title:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_rows.append({"hwnd": hwnd, "pid": pid, "title": title, "visible": bool(win32gui.IsWindowVisible(hwnd))})
    win32gui.EnumWindows(enum_window, None)

    report = {
        "collected_at": datetime.now().astimezone().isoformat(),
        "com_progid": "AutoCAD.Application.26",
        "version": str(app.Version),
        "executable": str(app.FullName),
        "visible": bool(app.Visible),
        "installed_entries": installed_autodesk_entries(),
        "windows": process_rows,
        "experiment_a": line_inventory,
        "experiment_b": poly_inventory,
        "dwg_save": {"a": line_dwg_result, "b": poly_dwg_result},
        "dwg_reopen": reopen_results,
        "dwg_reopen_inventories": reopen_inventories,
        "screenshots": {
            "line_overview": line_shot_ok,
            "polyline_overview": poly_shot_ok,
        },
        "limitations": [
            "Native GUI Properties palette, Layers palette, and Paper Space tab were not clicked because native window-control APIs were unavailable in this session.",
            "Entity types and layers were verified through AutoCAD COM ModelSpace and Layer collections.",
        ],
    }
    (NOTES / "autocad_resource_inventory.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "AutoCAD resource and hands-on execution report",
        "===============================================",
        f"Collected: {report['collected_at']}",
        f"Version: {report['version']}",
        f"Executable: {report['executable']}",
        f"COM: {report['com_progid']}",
        f"Visible: {report['visible']}",
        "",
        "Installed Autodesk entries:",
    ]
    lines.extend(f"{x['DisplayName']} | {x['DisplayVersion']} | {x['InstallLocation']}" for x in report["installed_entries"])
    lines += [
        "",
        "Experiment A (line-based) AutoCAD COM inventory:",
        f"Document: {line_inventory['full_name']}",
        f"Units header: {line_inventory['units_header']}",
        f"Types: {line_inventory['type_counts']}",
        f"Layers: {line_inventory['layer_counts']}",
        f"A-WALL objects: {[x for x in line_inventory['details'] if 'Layer: A-WALL' in x]}",
        "",
        "Experiment B (polyline-based) AutoCAD COM inventory:",
        f"Document: {poly_inventory['full_name']}",
        f"Units header: {poly_inventory['units_header']}",
        f"Types: {poly_inventory['type_counts']}",
        f"Layers: {poly_inventory['layer_counts']}",
        f"A-WALL objects: {[x for x in poly_inventory['details'] if 'Layer: A-WALL' in x]}",
        "",
        f"DWG A: {line_dwg_result}",
        f"DWG B: {poly_dwg_result}",
        f"DWG reopen: {reopen_results}",
        f"AutoCAD screenshots: line={line_shot_ok}, polyline={poly_shot_ok}",
        "",
        "Limitations:",
        *[f"- {x}" for x in report["limitations"]],
    ]
    (NOTES / "autocad_resource_inventory.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("AUTOCAD_COM_LAB_PASS")
    print(json.dumps({"save": report["dwg_save"], "reopen": report["dwg_reopen"], "screenshots": report["screenshots"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
