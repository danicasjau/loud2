import sys
import os
import re

import json
import shutil
from pathlib import Path

sys.path.append(r"C:\Program Files\Prism2\PythonLibs\Python3\PySide")

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtWidgets import QApplication
    import maya.cmds as cmds
except:
    #from PySide2 import QtWidgets, QtCore, QtGui
    print("Error not pyside or maya")

# global vars
ASSET_INFO_PATH = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Assetinfo"
ASSET_INFO_JSON = ASSET_INFO_PATH + r"\assetInfo.json"
PROJECT_PATH = r"P:\VFX_Project_30\2LOUD\Spotlight\03_Production\Assets"

def getAssets():
    with open(ASSET_INFO_JSON, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["assets"]

def findImageByName(name):
    atm1 = f"{ASSET_INFO_PATH}\{name}_preview.jpg"
    print(atm1)
    if os.path.exists(atm1): return atm1
    else: return f"{ASSET_INFO_PATH[:1]}\fallbacks\noFileBig.jpg"

def findAssetWalk(assetName):
    target_file = f"{assetName}_asset_master.usda"

    for root, dirs, files in os.walk(PROJECT_PATH):
        if target_file in files:
            return os.path.join(root, target_file)

    return None
     

class AssetPickerWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("2LOUD - ASSET IMPORT") # Title
        self.resize(600, 450)

        self.selected_assets = []
        self.buttons = []

        self.columns = 5 


        self.main_layout = QtWidgets.QVBoxLayout(self) # Main layout Vertixal    
        self.title_layout = QtWidgets.QHBoxLayout()

        # Title
        self.title = QtWidgets.QLabel("2loud Select Import")
        self.title.setStyleSheet("font-size: 25px; font-weight: bold;")
        self.title_layout.addWidget(self.title)
        self.main_layout.addLayout(self.title_layout)

        # Scroll area
        self.scroll = QtWidgets.QScrollArea() # Create Scrolalble widget
        self.scroll.setWidgetResizable(True) # Riziseable as window
        self.main_layout.addWidget(self.scroll)

        content = QtWidgets.QWidget()
        self.scroll.setWidget(content)

        grid = QtWidgets.QGridLayout(content) 
        grid.setSpacing(5) 

        i = 0
        assets = getAssets()
        for asset_name, asset_data in assets.items():
            fileName = asset_name
            assetWidget = AssetImageIcon(findImageByName(asset_name), asset_name) 
            # button
            btn = assetWidget.button
            btn.clicked.connect(self._make_callback(assetWidget))
            self.buttons.append(btn)

            grid.addWidget(assetWidget, i // self.columns, i % self.columns) # put onto grid 
            i+=1

            name = fileName.split("_preview.jpg")[0] 

            btn.setToolTip(f"""
            Name: {name}
            <br>
            Asset ID: ID
            <br>
            """)#{asset_data.id}


        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()

        accept_btn = QtWidgets.QPushButton("Accept")
        cancel_btn = QtWidgets.QPushButton("Cancel")

        accept_btn.clicked.connect(self._accept)
        cancel_btn.clicked.connect(self._reject)

        buttons_layout.addWidget(accept_btn)
        buttons_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(buttons_layout)

    def _make_callback(self, astImg):
        def callback():
            btn = astImg.button
            astImg.selected = not astImg.selected
            btn.setChecked(astImg.selected)
            self.selected_assets.append(astImg)

        return callback

    def _accept(self):
        print("accept")
        for asset in self.selected_assets:
            try:
                pth = findAssetWalk(asset.name)
                load_usd_asset_with_layer_editor(pth)
            except Exception as e:
                print(f"{e} Couldn't find asset : {asset.name}")
            print(asset)
        self.selected_assets = []
        super().accept()   # closes dialog with Accepted result

    def _reject(self):
        print("reject")
        super().reject()   # closes dialog with Rejected result


# Create Buttons with images and extra data
class AssetImageIcon(QtWidgets.QWidget):
    def __init__(self, image_path, name):
        super().__init__()

        self.image_size = 96
        self.selected = False
        self.name = name

        # Layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(2)

        # Button Creation
        self.image_path = image_path
        self.image_name = os.path.splitext(os.path.basename(image_path))[0]

        self.button = QtWidgets.QPushButton()
        self.button.setCheckable(True)
        self.button.setFixedSize(self.image_size, self.image_size)

        pixmap = QtGui.QPixmap(image_path)
        icon = QtGui.QIcon(pixmap)

        self.button.setIcon(icon) # Set the icon
        self.button.setIconSize(QtCore.QSize(self.image_size - 8, self.image_size - 8))

        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #333;
                background-color: #222;
                border-radius: 20px;
            }
            QPushButton:checked {
                border: 2px solid #42f5b6;
                background-color: #333;
            }
        """) 

        # Text Creation
        fileName = image_path.split("\\")[-1] # Strip image file name
        name = fileName.split("_preview.jpg")[0] # strip image name
        self.label = QtWidgets.QLabel(f"{name}") # Set Label

        self.label.setFixedHeight(20)
        self.label.setAlignment(QtCore.Qt.AlignCenter) # Align
        self.label.setStyleSheet("color: #ccc; font-size: 10pt;") # Set text style

        # Layout
        self.layout.addWidget(self.button, alignment=QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.button.image_name = name # Store the name on the button


import maya.cmds as cmds

def load_usd_asset_with_layer_editor(usd_path, proxy_name="usdAssetProxy"):
    """
    Load a USD asset fully into Maya using mayaUsdLayerEditor.
    Ensures geometry and UsdPreviewSurface materials are loaded.
    
    Returns the proxy shape node.
    """
    if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
        cmds.loadPlugin("mayaUsdPlugin")

    # Create a transform for the proxy shape
    transform = cmds.createNode("transform", name=proxy_name + "_TRANS")
    proxy_shape = cmds.createNode("mayaUsdProxyShape", name=proxy_name, parent=transform)

    # Load the USD stage
    # Set the file on the proxy shape
    cmds.setAttr(f"{proxy_shape}.filePath", usd_path, type="string")

    # Force the layer editor to refresh and load geometry + shading
    cmds.mayaUsdLayerEditor(proxy_shape, edit=True, refreshSystemLock=True)

    # Optional: ensure display materials are used
    # 'materialMode' attribute controls shading:
    # 0 = Display Color, 1 = Use Registry (UsdPreviewSurface), 2 = None
    cmds.setAttr(f"{proxy_shape}.materialMode", 1)

    # Optional: turn on visibility of root prim
    cmds.setAttr(f"{proxy_shape}.drawRenderPurpose", 1)

    return proxy_shape


def load_asset(path, reference=False):
    """
    Load a USD or FBX file into Maya, importing materials as well.
    """

    if not os.path.exists(path):
        raise RuntimeError(f"File does not exist: {path}")

    ext = os.path.splitext(path)[1].lower()

    # ---------- USD ----------
    if ext in (".usd", ".usda", ".usdc", ".usdz"):
        if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
            cmds.loadPlugin("mayaUsdPlugin")

        # Maya USD Import flags (from File > Import > Options)
        usd_flags = {
            "file": path,
            "type": "USD Import",
            "ignoreVersion": True,
            "mergeNamespacesOnClash": False,
            "namespace": "usdAsset",
            # These flags control materials/shading
            "shadingMode": "useRegistry",  # converts USD materials into Maya shaders
            "importAnimation": True,
            "primPath": "|",                # root prim
            "readAnimData": True,
            "readColorSets": True            # imports vertex colors
        }

        if reference:
            usd_flags["reference"] = True
        else:
            usd_flags["i"] = True  # import

        cmds.file(**usd_flags)

    # ---------- FBX ----------
    elif ext == ".fbx":
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya")

        if reference:
            cmds.file(
                path,
                reference=True,
                type="FBX",
                ignoreVersion=True,
                mergeNamespacesOnClash=False,
                namespace="fbxAsset"
            )
        else:
            cmds.file(
                path,
                i=True,
                type="FBX",
                ignoreVersion=True,
                mergeNamespacesOnClash=False
            )

    else:
        raise RuntimeError(f"Unsupported file type: {ext}")



def load_assetOLD(path, reference=False):
    if not os.path.exists(path):
        raise RuntimeError("File does not exist: {}".format(path))

    ext = os.path.splitext(path)[1].lower()

    # ---------- USD ----------
    if ext in (".usd", ".usda", ".usdc", ".usdz"):
        if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
            cmds.loadPlugin("mayaUsdPlugin")

        if reference:
            cmds.file(
                path,
                reference=True,
                type="USD Import",
                ignoreVersion=True,
                mergeNamespacesOnClash=False,
                namespace="usdAsset"
            )
        else:
            cmds.file(
                path,
                i=True,
                type="USD Import",
                ignoreVersion=True,
                mergeNamespacesOnClash=False
            )

    # ---------- FBX ----------
    elif ext == ".fbx":
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya")

        if reference:
            cmds.file(
                path,
                reference=True,
                type="FBX",
                ignoreVersion=True,
                mergeNamespacesOnClash=False,
                namespace="fbxAsset"
            )
        else:
            cmds.file(
                path,
                i=True,
                type="FBX",
                ignoreVersion=True,
                mergeNamespacesOnClash=False
            )
    else:
        raise RuntimeError("Unsupported file type: {}".format(ext))


win = AssetPickerWindow()
win.show()
"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AssetPickerWindow()
    win.show()
    sys.exit(app.exec())"""