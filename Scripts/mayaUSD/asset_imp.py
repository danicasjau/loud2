import maya.cmds as cmds
import os

def export_selected_geometry_usdc(export_path):
    """
    Export only selected geometry from Maya to a binary USD (.usdc) file.
    
    :param export_path: Full path to save the USD file (.usdc)
    """
    if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
        cmds.loadPlugin("mayaUsdPlugin")

    # Get selected geometry
    selection = cmds.ls(selection=True, long=True, geometry=True)
    if not selection:
        raise RuntimeError("No geometry selected for export.")

    # Ensure the folder exists
    folder = os.path.dirname(export_path)
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Maya USD export options for geometry only
    # reference: https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-CF1E34A3-B062-4E9C-901F-4DAAA90F2E39
    cmds.mayaUsdExport(
        file=export_path,
        selection=True,                # only selected nodes
        defaultMeshScheme="none",      # export raw geometry
        exportDisplayColor=False,      # no vertex colors
        exportColorSets=False,         # no color sets
        exportUVs=True,                # keep UVs
        mergeTransformAndShape=True,   # combine transform+shape
        shadingMode="none",            # ignore materials
        fileFormat="usdc",             # binary USD
        exportInstances=False           # optional: flatten instances
    )

    print(f"Exported {len(selection)} geometries to {export_path}")
