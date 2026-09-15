from __future__ import annotations

import sys
import time

import win32com.client
import win32gui

from run_day3_autocad_lab import SCREENSHOTS, capture_autocad, send_command, wait_until_idle


def main() -> None:
    target_type = sys.argv[1] if len(sys.argv) == 2 else "AcDbLine"
    target_name = "line" if target_type == "AcDbLine" else "polyline"
    app = win32com.client.GetActiveObject("AutoCAD.Application.26")
    app.Visible = True
    doc = app.ActiveDocument
    doc.Activate()
    # The palette command is UI-bound.  Bring AutoCAD forward before asking it
    # to lay out the palette; this is focus control only, not mouse input.
    win32gui.SetForegroundWindow(int(app.HWND))
    if int(doc.GetVariable("TILEMODE")) != 1:
        send_command(app, doc, "_.TILEMODE\n1\n")
    entity = next(entity for entity in doc.ModelSpace if str(entity.ObjectName) == target_type)

    send_command(app, doc, "_.LAYERCLOSE\n")
    send_command(app, doc, "_.PROPERTIESCLOSE\n")
    selection = f'(progn (sssetfirst nil (ssadd (handent "{entity.Handle}"))) (princ))\n'
    send_command(app, doc, selection)
    pickfirst = doc.PickfirstSelectionSet
    if int(pickfirst.Count) != 1 or str(pickfirst.Item(0).ObjectName) != target_type:
        raise RuntimeError(f"AutoCAD did not retain the expected implied selection: {target_type}")
    send_command(app, doc, "_.PROPERTIES\n", settle_seconds=3.0)
    # Give palette layout one additional render cycle before screen capture.
    time.sleep(3)
    wait_until_idle(app)
    saved = capture_autocad(app, SCREENSHOTS / f"0{2 if target_name == 'line' else 3}_{target_name}_properties.png")
    print(f"DAY3_PROPERTIES_{target_name.upper()}_PASS saved={saved}")


if __name__ == "__main__":
    main()
