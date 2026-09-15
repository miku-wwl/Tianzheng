from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import sys
import time

import pythoncom
import win32com.client
import win32con
import win32gui
from PIL import Image, ImageDraw, ImageFont, ImageGrab


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "output"
SCREENSHOTS = ROOT / "screenshots"
LOGS = ROOT / "logs"

LISP_FILE = SRC / "day3_automation.lsp"
CREATED_DWG = OUTPUT / "day3_created.dwg"
MODIFIED_DWG = OUTPUT / "day3_modified.dwg"
QUERY_LOG = LOGS / "entity_query.txt"


def wait_until_idle(app, timeout_seconds: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = None
    while time.monotonic() < deadline:
        try:
            if bool(app.GetAcadState().IsQuiescent):
                return
        except Exception as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"AutoCAD did not become idle: {last_error}")


def send_command(app, doc, command: str, settle_seconds: float = 0.7) -> None:
    wait_until_idle(app)
    doc.SendCommand(command)
    time.sleep(settle_seconds)
    wait_until_idle(app)


def get_hwnd(app) -> int:
    hwnd = int(app.HWND)
    if hwnd:
        return hwnd
    candidates: list[int] = []
    def callback(candidate, _):
        if win32gui.IsWindowVisible(candidate) and "AutoCAD" in win32gui.GetWindowText(candidate):
            candidates.append(candidate)
    win32gui.EnumWindows(callback, None)
    if not candidates:
        raise RuntimeError("AutoCAD window not found")
    return candidates[0]


def capture_autocad(app, target: Path) -> bool:
    hwnd = get_hwnd(app)
    moved_topmost = False
    try:
        flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        # AutoCAD's graphics viewport is not reliably drawn in off-screen window
        # captures. Temporarily placing the target above other local windows lets
        # the ordinary screen capture record the real rendered viewport.
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
        moved_topmost = True
        time.sleep(1)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        ImageGrab.grab(bbox=(left, top, right, bottom), include_layered_windows=True).save(target)
        return True
    except Exception as exc:
        target.with_suffix(target.suffix + ".error.txt").write_text(str(exc), encoding="utf-8")
        return False
    finally:
        if moved_topmost:
            try:
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            except Exception:
                pass


def entity_row(entity) -> dict:
    row = {
        "type": str(entity.ObjectName),
        "layer": str(entity.Layer),
        "handle": str(entity.Handle),
    }
    for name in ("Color", "Linetype", "TextString", "Radius", "Length", "Closed"):
        try:
            value = getattr(entity, name)
            row[name.lower()] = value if isinstance(value, (int, float, bool)) else str(value)
        except Exception:
            pass
    for name in ("StartPoint", "EndPoint", "InsertionPoint"):
        try:
            row[name.lower()] = list(getattr(entity, name))
        except Exception:
            pass
    return row


def inventory(doc) -> dict:
    rows = [entity_row(entity) for entity in doc.ModelSpace]
    return {
        "document": str(doc.FullName),
        "entity_count": len(rows),
        "types": dict(sorted(Counter(row["type"] for row in rows).items())),
        "layers": dict(sorted(Counter(row["layer"] for row in rows).items())),
        "entities": rows,
    }


def select_and_capture_properties(app, doc, type_name: str, screenshot_name: str) -> dict:
    entity = next(entity for entity in doc.ModelSpace if str(entity.ObjectName) == type_name)
    send_command(app, doc, "_.LAYERCLOSE\n")
    send_command(app, doc, "_.PROPERTIESCLOSE\n")
    selection_lisp = f'(progn (sssetfirst nil (ssadd (handent "{entity.Handle}"))) (princ))\n'
    send_command(app, doc, selection_lisp)
    pickfirst = doc.PickfirstSelectionSet
    selected = [
        {
            "type": str(pickfirst.Item(index).ObjectName),
            "layer": str(pickfirst.Item(index).Layer),
            "handle": str(pickfirst.Item(index).Handle),
        }
        for index in range(int(pickfirst.Count))
    ]
    send_command(app, doc, "_.PROPERTIES\n", settle_seconds=1.5)
    saved = capture_autocad(app, SCREENSHOTS / screenshot_name)
    return {
        "expected_type": type_name,
        "selection_method": "AutoLISP sssetfirst implied selection, not physical mouse input",
        "selected": selected,
        "screenshot": screenshot_name,
        "saved": saved,
    }


def render_query_log() -> None:
    text = QUERY_LOG.read_text(encoding="utf-8")
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 23)
    lines = text.splitlines()
    image = Image.new("RGB", (1500, max(500, 56 + 31 * len(lines))), "#16202a")
    draw = ImageDraw.Draw(image)
    draw.text((28, 18), "Day 3 AutoLISP entity query — actual log output", font=font, fill="#ffffff")
    y = 60
    for line in lines:
        color = "#7de3ff" if line.startswith("===") else "#e6edf3"
        draw.text((28, y), line, font=font, fill=color)
        y += 31
    image.save(SCREENSHOTS / "04_entity_query.png")


def main() -> None:
    for path in (LISP_FILE,):
        if not path.exists():
            raise FileNotFoundError(path)
    if CREATED_DWG.exists() or MODIFIED_DWG.exists():
        raise FileExistsError("Day 3 output already exists; refusing to overwrite an existing drawing")

    resume_existing_document = "--resume" in sys.argv[1:]
    app = win32com.client.GetActiveObject("AutoCAD.Application.26")
    app.Visible = True
    wait_until_idle(app)
    if resume_existing_document:
        doc = app.ActiveDocument
        if any(True for _ in doc.ModelSpace):
            raise RuntimeError("Resume mode requires the active AutoCAD document to be empty")
    else:
        doc = app.Documents.Add()
        wait_until_idle(app)
        doc.Activate()
        wait_until_idle(app)
        load_expression = f'(load "{LISP_FILE.as_posix()}")\n'
        send_command(app, doc, load_expression)
    send_command(app, doc, "DAY3CREATE\n", settle_seconds=2.0)
    created_inventory = inventory(doc)
    if created_inventory["types"].get("AcDbLine") != 4 or created_inventory["types"].get("AcDbPolyline") != 1:
        raise RuntimeError("DAY3CREATE did not produce the expected AutoCAD entities; LISP may not be loaded")
    created_screenshot = capture_autocad(app, SCREENSHOTS / "01_created_entities.png")
    line_properties = select_and_capture_properties(app, doc, "AcDbLine", "02_line_properties.png")
    polyline_properties = select_and_capture_properties(app, doc, "AcDbPolyline", "03_polyline_properties.png")
    send_command(app, doc, "_.PROPERTIESCLOSE\n")
    before_modify_screenshot = capture_autocad(app, SCREENSHOTS / "05_before_modify.png")
    render_query_log()

    send_command(app, doc, "DAY3MODIFY\n", settle_seconds=2.0)
    modified_inventory = inventory(doc)
    after_modify_screenshot = capture_autocad(app, SCREENSHOTS / "06_after_modify.png")

    send_command(app, doc, "DAY3DELETE\n", settle_seconds=2.0)
    deleted_inventory = inventory(doc)
    after_delete_screenshot = capture_autocad(app, SCREENSHOTS / "07_after_delete.png")
    wait_until_idle(app)
    doc.Close(False)
    wait_until_idle(app)
    reopened_doc = app.Documents.Open(str(MODIFIED_DWG), False)
    wait_until_idle(app)
    reopened_doc.Activate()
    wait_until_idle(app)
    reopened_inventory = inventory(reopened_doc)
    reopened_screenshot = capture_autocad(app, SCREENSHOTS / "08_reopened_drawing.png")

    report = {
        "collected_at": datetime.now().astimezone().isoformat(),
        "autocad_version": str(app.Version),
        "autocad_executable": str(app.FullName),
        "lisp_loaded": True,
        "created_dwg": {"path": str(CREATED_DWG), "exists": CREATED_DWG.exists()},
        "modified_dwg": {"path": str(MODIFIED_DWG), "exists": MODIFIED_DWG.exists()},
        "created": created_inventory,
        "line_properties": line_properties,
        "polyline_properties": polyline_properties,
        "modified": modified_inventory,
        "deleted": deleted_inventory,
        "reopened": reopened_inventory,
        "screenshots": {
            "created": created_screenshot,
            "before_modify": before_modify_screenshot,
            "after_modify": after_modify_screenshot,
            "after_delete": after_delete_screenshot,
            "reopened": reopened_screenshot,
        },
        "limitations": [
            "The AutoCAD desktop was automated through COM and AutoLISP because native Windows click control was unavailable.",
            "Properties screenshots use AutoCAD implied selection, not physical mouse input.",
            "04_entity_query.png is a rendering of the actual AutoLISP-produced text log, not an AutoCAD window capture.",
        ],
    }
    (LOGS / "day3_execution_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (LOGS / "day3_execution_report.txt").write_text(
        "\n".join(
            [
                "Day 3 execution report",
                f"AutoCAD: {report['autocad_version']}",
                f"Created types: {created_inventory['types']}",
                f"Modified types: {modified_inventory['types']}",
                f"After delete types: {deleted_inventory['types']}",
                f"Reopened types: {reopened_inventory['types']}",
                f"LINE Properties selection: {line_properties['selected']}",
                f"Polyline Properties selection: {polyline_properties['selected']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("DAY3_AUTOCAD_LAB_PASS")
    print(json.dumps({"created": created_inventory["types"], "modified": modified_inventory["types"], "deleted": deleted_inventory["types"], "reopened": reopened_inventory["types"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
