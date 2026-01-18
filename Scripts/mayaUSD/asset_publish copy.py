import os
from maya import cmds, mel
import re
import uuid
try:
    from PySide6 import QtWidgets, QtCore, QtGui
except:
    from PySide2 import QtWidgets, QtCore, QtGui

from shiboken6 import wrapInstance
import maya.OpenMayaUI as omui
import subprocess
import threading
import sys

try: 
    PROJECT_PATH = pcore.projectPath
except:
    PROJECT_PATH = r"P:\VFX_Project_30\2LOUD\Spotlight"

# ------------------------------
# Maya Main Window
# ------------------------------
def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class pathManager:
    def __init__(self):
        self.assetName = ""
        self.assetPath = ""
        self.assetPublishPath = ""
        self.version = "v0001"

    # -------------------------
    # Asset Name from Maya file
    # -------------------------
    def getOwnAssetName(self):
        scene_path = cmds.file(query=True, sceneName=True)
        if not scene_path:
            return None  # scene not saved

        maya_file_name = os.path.basename(scene_path)
        return maya_file_name.split("_")[0]

    # -------------------------
    # Find Asset Root Folder
    # -------------------------
    def findAssetWalk(self):
        if not self.assetName:
            return None

        for root, dirs, files in os.walk(
            os.path.join(PROJECT_PATH, "03_Production", "Assets")
        ):
            if self.assetName in dirs:
                return os.path.join(root, self.assetName)

        return None

    # -------------------------
    # Get Next Version (v0001 → v0002)
    # -------------------------
    def getAssetVersion(self):
        mesh_export_path = os.path.join(self.assetPath, "Export", "mesh")

        if not os.path.exists(mesh_export_path):
            return "v0001"

        versions = []
        for name in os.listdir(mesh_export_path):
            if re.match(r"v\d{4}", name):
                versions.append(int(name[1:]))

        if not versions:
            return "v0001"

        next_version = max(versions) + 1
        return f"v{next_version:04d}"

    # -------------------------
    # Publish Path
    # -------------------------
    def getAssetPublishPath(self, method="mesh"):
        if method.lower() == "mesh":
            return os.path.join(
                self.assetPath,
                "Export",
                "Mesh"
            )
        return None

    # -------------------------
    # Setup All Paths
    # -------------------------
    def setPaths(self):
        self.assetName = self.getOwnAssetName()
        if not self.assetName:
            cmds.warning("Scene not saved. Cannot resolve asset.")
            return

        self.assetPath = self.findAssetWalk()
        if not self.assetPath:
            cmds.warning(f"Asset '{self.assetName}' not found.")
            return

        self.version = self.getAssetVersion()
        self.assetPublishPath = self.getAssetPublishPath()


def deleteFileFromPath(file_path):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        print("File not found:", file_path)
    except PermissionError:
        print("No permission to delete:", file_path)


# ------------------------------
# Main UI Class
# ------------------------------
class TwoLoudAssetExport(QtWidgets.QDialog):
    WINDOW_NAME = "2LOUD_asset_export"

    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)

        self.setWindowTitle("2LOUD Asset Export")
        self.setMinimumWidth(480)
        self.setObjectName(self.WINDOW_NAME)

        self.paths = pathManager()
        self.paths.setPaths()

        self.build_ui()
        self.create_connections()
        self.refresh_selection()

    # --------------------------
    # UI
    # --------------------------
    def build_ui(self):
        main = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel("2LOUD Asset Export \n")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:22px;font-weight:bold;")
        main.addWidget(title)

        subtitle = QtWidgets.QLabel("Asset: EL MARTELL")
        subtitle.setAlignment(QtCore.Qt.AlignLeft)
        subtitle.setStyleSheet("font-size:16px;font-weight:bold;")
        main.addWidget(subtitle)

        # Export Method
        method = QtWidgets.QHBoxLayout()
        method.addWidget(QtWidgets.QLabel("Export Method:"))
        self.export_method = QtWidgets.QComboBox()
        self.export_method.addItems(["Asset", "Geometry", "Mesh"])
        self.export_method.setCurrentText("Mesh")
        method.addWidget(self.export_method)
        main.addLayout(method)

        # Geometry List
        geo_group = QtWidgets.QGroupBox("Selected Geometry")
        geo_layout = QtWidgets.QVBoxLayout(geo_group)

        self.geo_list = QtWidgets.QListWidget()
        geo_layout.addWidget(self.geo_list)

        self.origin_btn = QtWidgets.QPushButton("Set Selected to World Origin")
        self.recheck_btn = QtWidgets.QPushButton("ReCheck (Ngons)")
        geo_layout.addWidget(self.origin_btn)
        geo_layout.addWidget(self.recheck_btn)

        main.addWidget(geo_group)

        # Publish Info
        info = QtWidgets.QGroupBox("Publish Information")
        info_layout = QtWidgets.QFormLayout(info)

        self.publish_path = QtWidgets.QLabel(f"{self.paths.assetPath}")
        self.asset_name = QtWidgets.QLabel(f"{self.paths.assetName}")
        self.next_version = QtWidgets.QLabel(f"{self.paths.version}")

        self.geo_count = QtWidgets.QLabel("0")
        self.points_count = QtWidgets.QLabel("0")
        self.faces_count = QtWidgets.QLabel("0")
        self.verts_count = QtWidgets.QLabel("0")

        info_layout.addRow("Publish Path:", self.publish_path)
        info_layout.addRow("Asset Name:", self.asset_name)
        info_layout.addRow("Next Version:", self.next_version)
        info_layout.addRow("Geometries:", self.geo_count)
        info_layout.addRow("Points:", self.points_count)
        info_layout.addRow("Faces:", self.faces_count)
        info_layout.addRow("Vertices:", self.verts_count)

        main.addWidget(info)

        # Advanced Options (Collapsible)
        self.advanced_toggle = QtWidgets.QToolButton()
        self.advanced_toggle.setText("Advanced Options")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        self.advanced_toggle.setArrowType(QtCore.Qt.RightArrow)
        main.addWidget(self.advanced_toggle)

        self.advanced_widget = QtWidgets.QWidget()
        adv_layout = QtWidgets.QVBoxLayout(self.advanced_widget)

        self.new_asset_btn = QtWidgets.QPushButton("Create New Asset")
        self.select_asset_btn = QtWidgets.QPushButton("Select Existing Asset")

        self.save_houdini_chk = QtWidgets.QCheckBox("Save Houdini File")
        self.save_houdini_chk.setChecked(True)

        self.run_usd_chk = QtWidgets.QCheckBox("Run USD after Publish")
        self.create_textures_chk = QtWidgets.QCheckBox("Create Textures")
        self.create_textures_chk.setChecked(True)

        adv_layout.addWidget(self.new_asset_btn)
        adv_layout.addWidget(self.select_asset_btn)
        adv_layout.addWidget(self.save_houdini_chk)
        adv_layout.addWidget(self.run_usd_chk)
        adv_layout.addWidget(self.create_textures_chk)

        self.advanced_widget.setVisible(False)
        main.addWidget(self.advanced_widget)

        # Publish Button
        self.publish_btn = QtWidgets.QPushButton("PUBLISH")
        self.publish_btn.setMinimumHeight(44)
        main.addWidget(self.publish_btn)

    # --------------------------
    # Connections
    # --------------------------
    def create_connections(self):
        self.origin_btn.clicked.connect(self.move_to_origin)
        self.recheck_btn.clicked.connect(self.check_ngons)
        self.publish_btn.clicked.connect(self.publish)

        self.advanced_toggle.toggled.connect(self.toggle_advanced)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_selection)
        self.timer.start(600)

    def toggle_advanced(self, state):
        self.advanced_widget.setVisible(state)
        self.advanced_toggle.setArrowType(
            QtCore.Qt.DownArrow if state else QtCore.Qt.RightArrow
        )

    # --------------------------
    # Selection / Ngons
    # --------------------------
    def refresh_selection(self):
        self.geo_list.clear()
        self.meshes = []

        selection = cmds.ls(selection=True, long=True) or []
        for node in selection:
            self.collect_meshes(node)

        self.meshes = sorted(set(self.meshes))
        self.populate_list()
        self.update_stats()
        self.check_ngons()

    def collect_meshes(self, node):
        if cmds.nodeType(node) == "transform":
            shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
            if any(cmds.nodeType(s) == "mesh" for s in shapes):
                self.meshes.append(node)

        for child in cmds.listRelatives(node, children=True, fullPath=True) or []:
            self.collect_meshes(child)

    def populate_list(self, ngon_data=None):
        self.geo_list.clear()
        for mesh in self.meshes:
            item = QtWidgets.QListWidgetItem(mesh)
            if ngon_data and mesh in ngon_data:
                item.setForeground(QtGui.QColor("red"))
                item.setText(f"{mesh}  ⚠ Ngons ({ngon_data[mesh]})")
            self.geo_list.addItem(item)

    def check_ngons(self):
        """
        Detect ngons using polyInfo (correct Maya method)
        """
        ngon_data = {}

        for mesh in self.meshes:
            shapes = cmds.listRelatives(mesh, shapes=True, fullPath=True) or []
            mesh_shape = next((s for s in shapes if cmds.nodeType(s) == "mesh"), None)
            if not mesh_shape:
                continue

            faces = cmds.polyEvaluate(mesh_shape, face=True)
            ngon_count = 0

            for i in range(faces):
                info = cmds.polyInfo(f"{mesh_shape}.f[{i}]", faceToVertex=True)
                if not info:
                    continue

                # Example: "FACE 0: 1 2 3 4 5"
                verts = info[0].split(":")[-1].split()
                if len(verts) > 4:
                    ngon_count += 1

            if ngon_count > 0:
                ngon_data[mesh] = ngon_count

        self.populate_list(ngon_data)

    # --------------------------
    # Stats
    # --------------------------
    def update_stats(self):
        geo = len(self.meshes)
        points = faces = verts = 0

        for mesh in self.meshes:
            points += cmds.polyEvaluate(mesh, vertex=True)
            faces += cmds.polyEvaluate(mesh, face=True)
            verts += cmds.polyEvaluate(mesh, vertex=True)

        self.geo_count.setText(str(geo))
        self.points_count.setText(str(points))
        self.faces_count.setText(str(faces))
        self.verts_count.setText(str(verts))


    # --------------------------
    # Utility
    # --------------------------
    def move_to_origin(self):
        for mesh in self.meshes:
            cmds.xform(mesh, ws=True, t=(0, 0, 0))


    # --------------------------
    # Export
    # --------------------------
    def publish(self):
        if not self.meshes:
            cmds.warning("No meshes selected for publishing.")
            return

        if not self.paths or not self.paths.assetPath:
            cmds.warning("Asset paths are not set.")
            return

        self.tempPath = "P:/VFX_Project_30/2LOUD/Spotlight/00_Pipeline/temp"
        os.makedirs(self.tempPath, exist_ok=True)

        entity = {
            'type': 'asset',
            'asset_path': self.paths.assetName
        }

        product = "mesh"
        filesToDelete = []

        astName = f"{self.paths.assetName}_{product}_temp"

        file_path = self.export_fbx(self.meshes, astName, self.tempPath)
        productInfo = pcore.products.ingestProductVersion([file_path], entity, product)
        self.masterPath = pcore.products.updateMasterVersion(str(productInfo["createdFiles"][0]))
        filesToDelete.append(file_path)

        for f in filesToDelete:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                cmds.warning(f"Failed to delete temp file {f}: {e}")

        self.generateUsd()


    # --------------------------
    # Robust FBX export
    # --------------------------
    
    def export_fbx(self, objects, namein, path):
        # Filter valid mesh transforms
        valid_meshes = []
        for obj in objects:
            if cmds.objExists(obj):
                shapes = cmds.listRelatives(obj, shapes=True, type="mesh") or []
                if shapes:
                    valid_meshes.append(obj)

        if not valid_meshes:
            cmds.warning("No valid meshes found for FBX export.")
            return None

        os.makedirs(path, exist_ok=True)
        file_path = path + f"/{namein}.fbx"

        # Load FBX plugin safely
        if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
            try:
                cmds.loadPlugin("fbxmaya")
            except Exception as e:
                cmds.warning(f"Failed to load FBX plugin: {e}")
                return None
            if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
                cmds.warning("FBX plugin could not be loaded properly.")
                return None

        # Select valid meshes
        cmds.select(valid_meshes, r=True)

        try:
            mel.eval(f'file -force -options "v=0;" -typ "FBX export" -pr -es "{file_path}";')
            print(f"FBX export succeeded: {file_path}")
            return file_path
        except RuntimeError as e:
            cmds.warning(f"FBX export failed: {e}")
            return None
        
    def generateUniqueIdentifier(self):
        self.identifier = str(uuid.uuid4())
        return self.identifier
    

    def generateUsd(self):
            print("Sending data to Houdini")
            
            if not self.save_houdini_chk.isChecked():
                print("Houdini assets are NOT checked.")
                return

            python_exe = r"C:\Program Files\Side Effects Software\Houdini 21.0.440\bin\hython.exe"
            script_path = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Plugins\Custom\laud2\Scripts\mayaUSD\variants.py"

            # Generate unique identifier
            self.generateUniqueIdentifier()
            args = [self.paths.assetName, self.masterPath, self.identifier]
            cmd = [python_exe, script_path] + args

            # Create and start the Houdini process thread
            houdini_thread = HoudiniProcessThread(cmd)
            houdini_thread.finished.connect(self.on_houdini_finished)  # Connect signal to callback
            houdini_thread.start()  # Start the thread

    def on_houdini_finished(self, stdout, stderr):
        """Callback function when Houdini process finishes successfully or with errors."""
        if stderr:
            # Handle error
            print("Houdini process failed:")
            print("Error:", stderr)
        else:
            # Handle success
            print("Houdini process finished successfully.")
            print("Output:", stdout)
            self.convertUsdToVersion()
            # Update UI with success message, enable buttons, etc.

    def convertUsdToVersion(self):
        entity = {
            'type': 'asset',
            'asset_path': self.paths.assetName
        }

        product = "geometry"
        filesToDelete = []

        file_path2 = fr"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\temp\out_{self.identifier}_temp.usdc"

        try:
            productInfo = pcore.products.ingestProductVersion([file_path2], entity, product)
            pcore.products.updateMasterVersion(str(productInfo["createdFiles"][0]))
        except:
            print("Unable to set usd master")

        filesToDelete.append(file_path2)
        for f in filesToDelete:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                cmds.warning(f"Failed to delete temp file {f}: {e}")
        print("DONE")


class HoudiniProcessThread(QtCore.QThread):
    finished = QtCore.Signal(str, str)  # Signal to emit the output and error

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            # Run Houdini in the background using subprocess
            process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,  # Hide terminal window
                text=True
            )

            # Wait for the process to complete and capture output
            stdout, stderr = process.communicate()

            # Emit signal with stdout and stderr to main thread
            if process.returncode == 0:
                self.finished.emit(stdout, stderr)  # Signal success
            else:
                self.finished.emit("", stderr)  # Signal error

        except Exception as e:
            # In case of any exception, emit the error message
            self.finished.emit("", str(e))  # Signal error

# ------------------------------
# Launch
# ------------------------------
def show():
    if cmds.window(TwoLoudAssetExport.WINDOW_NAME, exists=True):
        cmds.deleteUI(TwoLoudAssetExport.WINDOW_NAME)
    TwoLoudAssetExport().show()

show()
