;;; Day 3 — AutoCAD automation lab
;;; Every command below edits the active drawing database through AutoLISP.
;;; The drawing unit convention is millimetres.

(vl-load-com)

(setq day3-created-path "C:/Users/weila/Desktop/CAD-Day3-Automation/output/day3_created.dwg")
(setq day3-modified-path "C:/Users/weila/Desktop/CAD-Day3-Automation/output/day3_modified.dwg")
(setq day3-log-path "C:/Users/weila/Desktop/CAD-Day3-Automation/logs/entity_query.txt")

;;; Global entity references are populated by DAY3CREATE.
(setq day3-line-1 nil day3-line-2 nil day3-line-3 nil day3-line-4 nil)
(setq day3-circle nil day3-text nil day3-polyline nil)

(defun day3:ensure-layer (name color)
  ;; Create a named layer only when it does not already exist.
  (if (not (tblsearch "LAYER" name))
    (entmakex
      (list
        '(0 . "LAYER")
        '(100 . "AcDbSymbolTableRecord")
        '(100 . "AcDbLayerTableRecord")
        (cons 2 name)
        '(70 . 0)
        (cons 62 color)
        '(6 . "Continuous")
      )
    )
  )
  name
)

(defun day3:create-line (start-point end-point layer)
  ;; Return the ename of a newly created LINE.
  (entmakex
    (list
      '(0 . "LINE")
      '(100 . "AcDbEntity")
      (cons 8 layer)
      '(100 . "AcDbLine")
      (cons 10 start-point)
      (cons 11 end-point)
    )
  )
)

(defun day3:create-polyline (layer)
  ;; A closed LWPOLYLINE located beside the room, so it is easy to inspect.
  (entmakex
    (list
      '(0 . "LWPOLYLINE")
      '(100 . "AcDbEntity")
      (cons 8 layer)
      '(100 . "AcDbPolyline")
      '(90 . 4)
      '(70 . 1)
      '(10 7000.0 0.0)
      '(10 8000.0 0.0)
      '(10 8000.0 1000.0)
      '(10 7000.0 1000.0)
    )
  )
)

(defun day3:create-text (value insertion-point layer)
  ;; Create one single-line TEXT entity.
  (entmakex
    (list
      '(0 . "TEXT")
      '(100 . "AcDbEntity")
      (cons 8 layer)
      '(100 . "AcDbText")
      (cons 10 insertion-point)
      (cons 40 300.0)
      (cons 1 value)
      '(7 . "Standard")
      '(72 . 1)
      (cons 11 insertion-point)
      '(73 . 2)
    )
  )
)

(defun day3:create-circle (center radius layer)
  ;; Create a CIRCLE using a center point and radius.
  (entmakex
    (list
      '(0 . "CIRCLE")
      '(100 . "AcDbEntity")
      (cons 8 layer)
      '(100 . "AcDbCircle")
      (cons 10 center)
      (cons 40 radius)
    )
  )
)

(defun day3:point-string (point / z)
  (if point
    (progn
      (setq z (if (caddr point) (caddr point) 0.0))
      (strcat
        "(" (rtos (car point) 2 2)
        ", " (rtos (cadr point) 2 2)
        ", " (rtos z 2 2) ")"
      )
    )
    "n/a"
  )
)

(defun day3:count-type (selection-set entity-type / index count data)
  (setq index 0 count 0)
  (while (< index (sslength selection-set))
    (setq data (entget (ssname selection-set index)))
    (if (= (cdr (assoc 0 data)) entity-type)
      (setq count (1+ count))
    )
    (setq index (1+ index))
  )
  count
)

(defun day3:entity-summary (entity / data)
  ;; Entity database fields: 0=type, 8=layer, 5=handle, 10=main coordinate.
  (setq data (entget entity))
  (strcat
    "TYPE=" (cdr (assoc 0 data))
    " | LAYER=" (cdr (assoc 8 data))
    " | HANDLE=" (cdr (assoc 5 data))
    " | P10=" (day3:point-string (cdr (assoc 10 data)))
  )
)

(defun day3:query-entities (label file-mode / file selection-set index line-count circle-count text-count polyline-count)
  ;; Query the active drawing, log inventory counts, and list type/layer/handle/point.
  (setq file (open day3-log-path file-mode))
  (setq selection-set (ssget "_X"))
  (setq line-count (day3:count-type selection-set "LINE"))
  (setq circle-count (day3:count-type selection-set "CIRCLE"))
  (setq text-count (day3:count-type selection-set "TEXT"))
  (setq polyline-count (day3:count-type selection-set "LWPOLYLINE"))
  (write-line "" file)
  (write-line (strcat "=== " label " ===") file)
  (write-line (strcat "LINE x " (itoa line-count)) file)
  (write-line (strcat "CIRCLE x " (itoa circle-count)) file)
  (write-line (strcat "TEXT x " (itoa text-count)) file)
  (write-line (strcat "LWPOLYLINE x " (itoa polyline-count)) file)
  (write-line "-- Entity records --" file)
  (setq index 0)
  (while (< index (sslength selection-set))
    (write-line (day3:entity-summary (ssname selection-set index)) file)
    (setq index (1+ index))
  )
  (close file)
  (princ
    (strcat
      "\n" label
      " | LINE x " (itoa line-count)
      " | CIRCLE x " (itoa circle-count)
      " | TEXT x " (itoa text-count)
      " | LWPOLYLINE x " (itoa polyline-count)
    )
  )
)

(defun day3:move-entity (entity dx dy / data start end)
  ;; Move one LINE by replacing its start and end coordinate database fields.
  (setq data (entget entity))
  (setq start (cdr (assoc 10 data)))
  (setq end (cdr (assoc 11 data)))
  (setq data (subst (cons 10 (list (+ (car start) dx) (+ (cadr start) dy) (caddr start))) (assoc 10 data) data))
  (setq data (subst (cons 11 (list (+ (car end) dx) (+ (cadr end) dy) (caddr end))) (assoc 11 data) data))
  (entmod data)
  (entupd entity)
)

(defun day3:set-layer (entity layer / data)
  ;; Change the layer reference (DXF group 8) of one entity.
  (setq data (entget entity))
  (entmod (subst (cons 8 layer) (assoc 8 data) data))
  (entupd entity)
)

(defun day3:set-text (entity value / data)
  ;; Replace the TEXT string (DXF group 1).
  (setq data (entget entity))
  (entmod (subst (cons 1 value) (assoc 1 data) data))
  (entupd entity)
)

(defun day3:set-circle-radius (entity radius / data)
  ;; Replace the CIRCLE radius (DXF group 40).
  (setq data (entget entity))
  (entmod (subst (cons 40 radius) (assoc 40 data) data))
  (entupd entity)
)

(defun day3:delete-entity (entity)
  ;; Mark an entity as erased in the drawing database.
  (entdel entity)
)

(defun day3:save-drawing (path / document)
  ;; Save the active drawing as a real DWG file through AutoCAD's COM API.
  (setq document (vla-get-ActiveDocument (vlax-get-acad-object)))
  (vla-saveas document path)
)

(defun c:DAY3CREATE ()
  ;; Create the Day 3 data model entirely from code.
  (setvar "INSUNITS" 4)
  (day3:ensure-layer "DAY3-WALL" 7)
  (day3:ensure-layer "DAY3-MARKER" 2)
  (day3:ensure-layer "DAY3-TEXT" 3)
  (day3:ensure-layer "DAY3-POLY" 4)
  (day3:ensure-layer "DAY3-CHANGED" 6)
  (setq day3-line-1 (day3:create-line '(0.0 0.0 0.0) '(6000.0 0.0 0.0) "DAY3-WALL"))
  (setq day3-line-2 (day3:create-line '(6000.0 0.0 0.0) '(6000.0 4000.0 0.0) "DAY3-WALL"))
  (setq day3-line-3 (day3:create-line '(6000.0 4000.0 0.0) '(0.0 4000.0 0.0) "DAY3-WALL"))
  (setq day3-line-4 (day3:create-line '(0.0 4000.0 0.0) '(0.0 0.0 0.0) "DAY3-WALL"))
  (setq day3-circle (day3:create-circle '(3000.0 2000.0 0.0) 450.0 "DAY3-MARKER"))
  (setq day3-text (day3:create-text "DAY 3" '(3000.0 3000.0 0.0) "DAY3-TEXT"))
  (setq day3-polyline (day3:create-polyline "DAY3-POLY"))
  (day3:query-entities "AFTER CREATE" "w")
  (day3:save-drawing day3-created-path)
  (command "_.ZOOM" "_E")
  (princ "\nDAY3CREATE complete.")
  (princ)
)

(defun c:DAY3QUERY ()
  (day3:query-entities "MANUAL QUERY" "a")
  (princ)
)

(defun c:DAY3MODIFY ()
  ;; Modify geometry and properties without manual dragging.
  (day3:move-entity day3-line-1 0.0 300.0)
  (day3:set-layer day3-circle "DAY3-CHANGED")
  (day3:set-text day3-text "DAY 3 AUTOMATION")
  (day3:set-circle-radius day3-circle 650.0)
  (day3:query-entities "AFTER MODIFY" "a")
  (day3:save-drawing day3-modified-path)
  (command "_.ZOOM" "_E")
  (princ "\nDAY3MODIFY complete.")
  (princ)
)

(defun c:DAY3DELETE ()
  ;; Delete the circle after the modification has been logged and saved.
  (day3:delete-entity day3-circle)
  (day3:query-entities "AFTER DELETE" "a")
  (day3:save-drawing day3-modified-path)
  (princ "\nDAY3DELETE complete.")
  (princ)
)

(princ "\nDay 3 AutoLISP loaded. Commands: DAY3CREATE, DAY3QUERY, DAY3MODIFY, DAY3DELETE.")
(princ)
