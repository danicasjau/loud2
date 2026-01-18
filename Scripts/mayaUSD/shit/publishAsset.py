import maya.cmds as cmds
import os

def loud2_publisher():
    # --- Configuration ---
    default_base_path = "C:/Project/USD/Publish"
    file_name = "asset_v001"
    departments = ["Modeling", "Texturing", "BaseMesh"]
    window_id = "Loud2PublishWin"

    if cmds.window(window_id, exists=True):
        cmds.deleteUI(window_id)

    # 1. UI Setup
    window = cmds.window(window_id, title="Loud2 USD Publisher", widthHeight=(400, 500))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnOffset=['both', 15])
    
    cmds.separator(height=10, style='none')
    cmds.text(label="LOUD2 PUBLISH TERMINAL", font="boldLabelFont", height=30)
    
    path_field = cmds.textFieldGrp(label="Destination:", text=default_base_path)
    name_field = cmds.textFieldGrp(label="File Name:", text=file_name)
    
    dept_menu = cmds.optionMenu(label="Department: ")
    for dept in departments: cmds.menuItem(label=dept)

    format_menu = cmds.optionMenu(label="USD Format: ")
    for fmt in ["usdc", "usda", "usd"]: cmds.menuItem(label=fmt)

    cmds.frameLayout(label="Export Settings", collapsable=True, marginWidth=10)
    cmds.columnLayout(adjustableColumn=True)
    master_chk = cmds.checkBox(label="Set as Master Layer (Empty Init)", value=True)
    export_type = cmds.radioButtonGrp(label='Content:', labelArray2=['Only Geo', 'Only Lights'], numberOfRadioButtons=2, select=1)
    anim_chk = cmds.checkBox(label="Include Animation", value=False)
    uv_chk = cmds.checkBox(label="Export UVs", value=True)
    cmds.setParent('..'); cmds.setParent('..')

    cmds.text(label="Publish Notes:", align="left")
    notes_field = cmds.scrollField(height=60, wordWrap=True)

    # 2. Functional Logic
    def execute_publish(*args):
        base = cmds.textFieldGrp(path_field, q=True, text=True)
        fname = cmds.textFieldGrp(name_field, q=True, text=True)
        dept = cmds.optionMenu(dept_menu, q=True, value=True)
        ext = cmds.optionMenu(format_menu, q=True, value=True)
        
        final_dir = os.path.join(base, dept).replace("\\", "/")
        if not os.path.exists(final_dir): os.makedirs(final_dir)
        full_path = f"{final_dir}/{fname}.{ext}"

        if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
            cmds.loadPlugin("mayaUsdPlugin")

        # Flag Workaround: Check which animation flag exists
        # Some versions use 'exportAnimation', others use 'animation'
        anim_val = cmds.checkBox(anim_chk, q=True, v=True)
        export_args = {
            "file": full_path,
            "selection": True,
            "mergeTransformAndShape": True,
            "defaultUSDFormat": ext,
            "exportUVs": cmds.checkBox(uv_chk, q=True, v=True)
        }
        
        # This solves your specific error by trying both common flag names
        try:
            # Check for 'animation' flag first
            cmds.mayaUSDExport(query=True, animation=True)
            export_args["animation"] = anim_val
        except:
            export_args["exportAnimation"] = anim_val

        try:
            # Step A: Initialize Empty File (Master Logic)
            if cmds.checkBox(master_chk, q=True, v=True):
                cmds.select(clear=True)
                cmds.mayaUSDExport(file=full_path, selection=True, defaultUSDFormat=ext)

            # Step B: Select Content
            mode = cmds.radioButtonGrp(export_type, q=True, select=True)
            if mode == 1: # Geo
                targets = cmds.listRelatives(cmds.ls(type='mesh'), p=True, f=True)
            else: # Lights
                targets = cmds.listRelatives(cmds.ls(lights=True), p=True, f=True)
            
            if targets: cmds.select(targets)
            else: cmds.select(clear=True)

            # Step C: Final Export
            cmds.mayaUSDExport(**export_args)
            
            cmds.confirmDialog(title="Success", message=f"Published to: {full_path}")
            print(f"Notes: {cmds.scrollField(notes_field, q=True, text=True)}")
            
        except Exception as e:
            cmds.error(f"Publish Failed: {str(e)}")

    # 3. Buttons
    cmds.separator(height=20)
    cmds.rowLayout(numberOfColumns=2, ad2=2, columnWidth2=[185, 185])
    cmds.button(label="PUBLISH", bgc=[0.3, 0.5, 0.3], height=40, command=execute_publish)
    cmds.button(label="CANCEL", bgc=[0.4, 0.2, 0.2], height=40, command=lambda x: cmds.deleteUI(window_id))

    cmds.showWindow(window)

loud2_publisher()