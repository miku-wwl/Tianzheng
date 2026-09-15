// Educational only: this is a compact AutoCAD .NET API pattern, not a compiled plugin.
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using Autodesk.AutoCAD.Runtime;

public sealed class Day3DotNetExample
{
    [CommandMethod("DAY3DOTNETEXAMPLE")]
    public void CreateLineInModelSpace()
    {
        Document document = Application.DocumentManager.MdiActiveDocument;
        Database database = document.Database;

        // Transaction = database transaction: work is committed only at the end.
        using (Transaction transaction = database.TransactionManager.StartTransaction())
        {
            BlockTable blockTable = (BlockTable)transaction.GetObject(
                database.BlockTableId, OpenMode.ForRead);
            BlockTableRecord modelSpace = (BlockTableRecord)transaction.GetObject(
                blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

            Entity line = new Line(new Point3d(0, 0, 0), new Point3d(6000, 0, 0));
            ObjectId lineId = modelSpace.AppendEntity(line);
            transaction.AddNewlyCreatedDBObject(line, true);

            document.Editor.WriteMessage($"\nCreated LINE ObjectId: {lineId}");
            transaction.Commit();
        }
    }
}
