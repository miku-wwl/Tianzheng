$ErrorActionPreference = 'Stop'

$lab = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$output = Join-Path $lab 'output'
$screenshots = Join-Path $lab 'screenshots'
$notes = Join-Path $lab 'notes'
$lineDxf = Join-Path $output 'day2_line_based.dxf'
$polyDxf = Join-Path $output 'day2_polyline_based.dxf'
$lineDwg = Join-Path $output 'day2_line_based.dwg'
$polyDwg = Join-Path $output 'day2_polyline_based.dwg'

function Get-InstalledAutodeskEntries {
    Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -match 'AutoCAD|Autodesk' } |
        Select-Object DisplayName, DisplayVersion, InstallLocation, Publisher
}

function Get-AcadDocumentByPath($app, [string]$path) {
    $full = [IO.Path]::GetFullPath($path)
    foreach ($doc in @($app.Documents)) {
        try {
            if ($doc.FullName -and ([IO.Path]::GetFullPath($doc.FullName) -ieq $full)) { return $doc }
        } catch { }
    }
    return $null
}

function Open-AcadDocument($app, [string]$path) {
    for ($attempt = 1; $attempt -le 8; $attempt++) {
        try {
            $doc = Get-AcadDocumentByPath $app $path
            if (-not $doc) { $doc = $app.Documents.Open($path, $false) }
            $doc.Activate()
            Start-Sleep -Seconds 3
            return $doc
        } catch {
            if ($attempt -eq 8) { throw }
            Start-Sleep -Seconds 3
        }
    }
}

function Get-EntityInventory($doc) {
    $typeCounts = @{}
    $layerCounts = @{}
    $details = [Collections.Generic.List[string]]::new()
    $index = 0
    foreach ($entity in $doc.ModelSpace) {
        $index++
        $type = [string]$entity.ObjectName
        $layer = [string]$entity.Layer
        if (-not $typeCounts.ContainsKey($type)) { $typeCounts[$type] = 0 }
        if (-not $layerCounts.ContainsKey($layer)) { $layerCounts[$layer] = 0 }
        $typeCounts[$type]++
        $layerCounts[$layer]++
        $details.Add(('Object {0:D3} | Type: {1} | Layer: {2}' -f $index, $type, $layer))
    }
    [pscustomobject]@{
        Name = $doc.Name
        FullName = $doc.FullName
        TypeCounts = $typeCounts
        LayerCounts = $layerCounts
        Details = $details
    }
}

function Save-AcadAsDwg($doc, [string]$path) {
    try {
        $doc.SaveAs($path)
        Start-Sleep -Seconds 2
        return [pscustomobject]@{ Path = $path; Exists = (Test-Path -LiteralPath $path); Error = $null }
    } catch {
        return [pscustomobject]@{ Path = $path; Exists = $false; Error = $_.Exception.Message }
    }
}

function Capture-AcadWindow([string]$path) {
    try {
        Add-Type -AssemblyName System.Drawing
        Add-Type @"
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class CadWindowCapture {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    public static void Capture(IntPtr hWnd, string path) {
        RECT rect;
        if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        int width = Math.Max(1, rect.Right - rect.Left);
        int height = Math.Max(1, rect.Bottom - rect.Top);
        using (Bitmap bitmap = new Bitmap(width, height))
        using (Graphics graphics = Graphics.FromImage(bitmap)) {
            graphics.CopyFromScreen(rect.Left, rect.Top, 0, 0, new Size(width, height));
            bitmap.Save(path, ImageFormat.Png);
        }
    }
}
"@
        $proc = Get-Process -Name acad | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
        if (-not $proc) { throw 'AutoCAD main window was not exposed by the process.' }
        [CadWindowCapture]::Capture($proc.MainWindowHandle, $path)
        return $true
    } catch {
        Set-Content -LiteralPath ($path + '.error.txt') -Value $_.Exception.Message -Encoding UTF8
        return $false
    }
}

if (-not (Test-Path -LiteralPath $lineDxf)) { throw "Missing $lineDxf" }
if (-not (Test-Path -LiteralPath $polyDxf)) { throw "Missing $polyDxf" }

$acad = New-Object -ComObject AutoCAD.Application.26
$acad.Visible = $true
Start-Sleep -Seconds 6

$resourceLines = [Collections.Generic.List[string]]::new()
$resourceLines.Add('AutoCAD resource inventory')
$resourceLines.Add('=========================')
$resourceLines.Add(('Collected: {0}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')))
$resourceLines.Add(('COM ProgID: AutoCAD.Application.26'))
$resourceLines.Add(('Version: {0}' -f $acad.Version))
$resourceLines.Add(('Executable: {0}' -f $acad.FullName))
$resourceLines.Add(('Visible after attach: {0}' -f $acad.Visible))
$resourceLines.Add('')
$resourceLines.Add('Installed Autodesk entries:')
foreach ($entry in Get-InstalledAutodeskEntries) {
    $resourceLines.Add(('{0} | {1} | {2}' -f $entry.DisplayName, $entry.DisplayVersion, $entry.InstallLocation))
}
$resourceLines.Add('')
$resourceLines.Add('Lab input files:')
$resourceLines.Add(('{0} | {1} bytes' -f $lineDxf, (Get-Item $lineDxf).Length))
$resourceLines.Add(('{0} | {1} bytes' -f $polyDxf, (Get-Item $polyDxf).Length))

$lineDoc = Open-AcadDocument $acad $lineDxf
$lineInventory = Get-EntityInventory $lineDoc
$lineDoc.SendCommand("_.ZOOM $([char]13)_E$([char]13)")
Start-Sleep -Seconds 2
$lineShot = Join-Path $screenshots '04_autocad_line_overview.png'
$lineShotOk = Capture-AcadWindow $lineShot
$lineDwgResult = Save-AcadAsDwg $lineDoc $lineDwg

$polyDoc = Open-AcadDocument $acad $polyDxf
$polyInventory = Get-EntityInventory $polyDoc
$polyDoc.SendCommand("_.ZOOM $([char]13)_E$([char]13)")
Start-Sleep -Seconds 2
$polyShot = Join-Path $screenshots '05_autocad_polyline_overview.png'
$polyShotOk = Capture-AcadWindow $polyShot
$polyDwgResult = Save-AcadAsDwg $polyDoc $polyDwg

$lineDwgDoc = $null
$polyDwgDoc = $null
$reopenResults = [Collections.Generic.List[object]]::new()
foreach ($dwg in @($lineDwg, $polyDwg)) {
    if (Test-Path -LiteralPath $dwg) {
        try {
            $opened = Open-AcadDocument $acad $dwg
            $inv = Get-EntityInventory $opened
            $reopenResults.Add([pscustomobject]@{ Path = $dwg; Opened = $true; EntityCount = $inv.Details.Count; Error = $null })
            if ($dwg -eq $lineDwg) { $lineDwgDoc = $opened } else { $polyDwgDoc = $opened }
        } catch {
            $reopenResults.Add([pscustomobject]@{ Path = $dwg; Opened = $false; EntityCount = 0; Error = $_.Exception.Message })
        }
    } else {
        $reopenResults.Add([pscustomobject]@{ Path = $dwg; Opened = $false; EntityCount = 0; Error = 'DWG file was not created' })
    }
}

$resourceLines.Add('')
$resourceLines.Add('Experiment A AutoCAD COM inventory:')
$resourceLines.Add(('Document: {0}' -f $lineInventory.FullName))
$resourceLines.Add(('Types: {0}' -f (($lineInventory.TypeCounts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name) x $($_.Value)" }) -join ', ')))
$resourceLines.Add(('Layers: {0}' -f (($lineInventory.LayerCounts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name) x $($_.Value)" }) -join ', ')))
$resourceLines.Add('')
$resourceLines.Add('Experiment B AutoCAD COM inventory:')
$resourceLines.Add(('Document: {0}' -f $polyInventory.FullName))
$resourceLines.Add(('Types: {0}' -f (($polyInventory.TypeCounts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name) x $($_.Value)" }) -join ', ')))
$resourceLines.Add(('Layers: {0}' -f (($polyInventory.LayerCounts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name) x $($_.Value)" }) -join ', ')))
$resourceLines.Add('')
$resourceLines.Add(('A-WALL Experiment A: {0}' -f (($lineInventory.Details | Where-Object { $_ -match 'Layer: A-WALL' }) -join '; ')))
$resourceLines.Add(('A-WALL Experiment B: {0}' -f (($polyInventory.Details | Where-Object { $_ -match 'Layer: A-WALL' }) -join '; ')))
$resourceLines.Add('')
$resourceLines.Add(('DWG A: Exists={0}; Error={1}' -f $lineDwgResult.Exists, $lineDwgResult.Error))
$resourceLines.Add(('DWG B: Exists={0}; Error={1}' -f $polyDwgResult.Exists, $polyDwgResult.Error))
$resourceLines.Add(('Reopen results: {0}' -f (($reopenResults | ForEach-Object { "$($_.Path) | Opened=$($_.Opened) | EntityCount=$($_.EntityCount) | Error=$($_.Error)" }) -join '; ')))
$resourceLines.Add(('AutoCAD overview screenshot A: {0}' -f $lineShotOk))
$resourceLines.Add(('AutoCAD overview screenshot B: {0}' -f $polyShotOk))
$resourceLines.Add('')
$resourceLines.Add('Limitations: this run used AutoCAD COM automation. Native GUI Properties palette, Layers palette, and Paper Space tab were not clicked because native window-control APIs were unavailable in this session.')

$resourceLines | Set-Content -LiteralPath (Join-Path $notes 'autocad_resource_inventory.txt') -Encoding UTF8
Write-Output ($resourceLines -join [Environment]::NewLine)
