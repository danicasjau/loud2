# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.

import sys
import os
import getpass

try:
    from PySide6.QtCore import *   
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *

    from PySide6.QtCore import QThread, Signal

except:
    from qtpy.QtCore import *   
    from qtpy.QtGui import *
    from qtpy.QtWidgets import *

    from qtpy.QtCore import QThread, Signal


from PrismUtils.Decorators import err_catcher_plugin as err_catcher # pyright: ignore[reportMissingImports]

from loud2_viewer import WebViewer

from usdAsset_dialog import CreateAssetCustomDlg
from usdShot_dialog import CreateShotCustomDlg

from PrismUtils import PrismWidgets # pyright: ignore[reportMissingImports]

from manager.userWindow import ConfigDrivenWindow
from BackUpManeger.backup import SafeCopyApp

import os
import shutil
import json

ASSET_INFO_PATH = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Assetinfo\assetInfo.json"


class Prism_laud2_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.setStyle = False

        print("loud2 registering callbacks for loud2 style")

        self.core.registerCallback("postInitialize", self.postInitialize, plugin=self)
        self.core.registerCallback("onProjectBrowserStartup", self.setNamings, plugin=self)
        self.core.registerCallback("onProjectBrowserStartup", self.onProjectBrowserStartup, plugin=self)
        self.core.registerCallback("onProjectBrowserStartup", self.setUser, plugin=self)
        #self.core.registerCallback("onProjectBrowserStartup", self.showUsdPanel, plugin=self) # afageix layout usd viewer 

        # ============== ASSET CREATION FALLBACK =========================
        self.core.registerCallback(
            "openPBAssetContextMenu", self.assetAction, plugin=self
        )
        self.core.registerCallback(
            "openPBShotContextMenu", self.shotAction, plugin=self
        )
        self.core.registerCallback(
            "onCreateAssetDlgOpen", self.customAssetCreation, plugin=self
        )

        self.usdviewer = None

    def setUser(self, origin):
        print("set user")
        """
        Returns a tuple: (name, abbreviation, role)
        - If the PC username exists in users.json, return that user's info.
        - Otherwise, return a Guest user with generated name and abbreviation.
        """

        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manager", "users.json")
        
        pc_username = getpass.getuser().lower()

        username, abrev = "guest", "guest"  # default values

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                users = json.load(f)

            # Look for exact username or in knownNames
            for user in users:
                user_username = user["username"].lower()
                known_names = [k.lower() for k in user.get("knownNames", [])]

                # Check exact username match
                if pc_username == user_username:
                    username, abrev, role = user["username"], user["abreviation"], user["role"]
                    break

                # Check knownNames
                if pc_username in known_names:
                    username, abrev, role = user["username"], user["abreviation"], user["role"]
                    break

        os.environ["PRISM_USER"] = username
        os.environ["PRISM_USER_ABREVIATION"] = abrev

        self.core.users.setUser(username, True, abrev, True)
        self.core.username = username
        #self.core.users.setUserAbbeviation(abrev, True)



    @err_catcher(name=__name__)
    def isActive(self):
        return True

    def dump_object(self, obj):
        print(f"\n=== {type(obj)} ===")

        # Attributes & methods
        for name in dir(obj):
            if name.startswith("__"):
                continue
            try:
                value = getattr(obj, name)
                print(f"{name}: {value}")
            except Exception as e:
                print(f"{name}: <error: {e}>")


    def setDeacentStyle(self):
        print("Setting deacent style")
        try:
            self.core.pb.tbw_project.setStyleSheet("""
            QTabBar::tab {
                padding: 5px 10px;      /* height & width padding */
                min-height: 16px;        /* force taller tabs */
                border-radius: 4px;      /* no rounded corners */
                margin: 5px 5px;
            }

            QTabBar::tab:selected {
                background: ##7ba3e3;
            }

            QTabBar::tab:!selected {
                background: #2d2d2d;
            }

            QTabWidget::pane {
                border: 1px solid #333; /* optional */
            }
            """)
        except:
            print("Unable to load gui prism modifications")

    def setNamings(self, origin):
        origin.setWindowTitle("2LOUD PRISM - Pipline organization")

    def onProjectBrowserStartup(self, origin):
        for act in list(origin.menubar.actions()):
            menu = act.menu()
            title = menu.title() if menu else act.text()
            if title in ("Send feedback..."):
                if menu:
                    menu.clear()
                else:
                    origin.menubar.removeAction(act)

        origin.documentationMenu = QMenu("📄Docs l2")
        origin.documentationMenu.addAction("Organization Excel", lambda: self.showWebWindow("exc"))
        origin.documentationMenu.addAction("All Documentation", lambda: self.showWebWindow("other"))
        origin.documentationMenu.addAction("Discord", lambda: self.showWebWindow("dis"))
        origin.documentationMenu.addAction("Super Canva", lambda: self.showWebWindow("can"))
        origin.menubar.addMenu(origin.documentationMenu)


        origin.agentMenu = QMenu("📢2LOUD")
        origin.agentMenu.addAction("Configuration", lambda: self.showConfiguration())
        origin.agentMenu.addAction("Show usd", lambda: self.showUsdPanel())
        origin.menubar.addMenu(origin.agentMenu)

        origin.backupMenu = QMenu("💽Backup")
        origin.backupMenu.addAction("Backup Manager", lambda: self.openBackupManager())
        origin.backupMenu.addAction("Fast Backup", lambda: self.openBackupManager())
        origin.backupMenu.addAction("Start full Backup", lambda: self.openBackupManager())
        origin.menubar.addMenu(origin.backupMenu)

    def postInitialize(self):
        if self.setStyle:
            self.core.registerStyleSheet(path=r"P:\VFX_Project_30\r&d\tloud\00_Pipeline\Styles\loudStyle")
            self.core.setActiveStyleSheet("loudStyle")
        
        #self.setDeacentStyle()

    def showWebWindow(self, oType="dis"):
        print("Show web window")
        self.webWindow = WebViewer(windowType=oType)
        self.webWindow.show()

    def showConfiguration(self):
        print("Show configuration window")
        self.configWindow = ConfigDrivenWindow()
        self.configWindow.show()

    def confirmDelete(self, path):
        title = "⚠️⚠️  ASSET DELATION - EXTREME WARNING  ⚠️⚠️"
        msg = (
            f"YOU ARE ABOUT TO DELETE THE {os.path.basename(path)} ASSET.\n\n"
            "This action is **IRREVERSIBLE** and **DANGEROUS**. "
            "There is NO undo.\n"
            "The asset will be COMPLETELY REMOVED from the project. "
            "ALL references will BREAK. "
            "ALL dependent paths will FAIL. "
            "This MAY corrupt scenes, tools, or pipelines. \n"
            "Proceed ONLY if you know what you are doing. "
            "If you are unsure — CANCEL. \n\n"
            f"DELETION ASSET: {os.path.basename(path)} \n"
            "Do you REALLY want to continue?"
        )
        result = self.core.popupQuestion(msg, title=title, icon=QMessageBox.Critical)
        if result == "Yes":
            result2 = self.core.popupQuestion("THE ASSET WILL BE REMOVED. Confirm: Action ireversible")
            if result2 == "Yes":
                self.deleteAsset(path)
                self.core.pb.refreshUI()
                print("Entity deleted")


    def openBackupManager(self):
        ex = SafeCopyApp()
        ex.show()

    # ======================================
    # ASSET CREATION USD ABLE
    # ======================================
    def customAssetCreation(self):
        print("Args shot custom")
        print(f"ARGS:")

    def openCreateAssetDlg(self, parent, path):
        print(parent)
        dlg = CreateAssetCustomDlg(self.core, parent=parent, path=path)
        dlg.show()

    def deleteAssetJsonPath(self, assetPath):
        print("Delate Asset Json Path")

    # Extract asset name from filesystem path
        asset_name = os.path.basename(os.path.normpath(assetPath))

        # Read JSON file
        with open(ASSET_INFO_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        assets = data.get("assets", {})

        if asset_name not in assets:
            return False

        # Remove asset
        del assets[asset_name]

        # Write back to file
        with open(ASSET_INFO_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return True

    def deleteAsset(self, assetPath):
        while True:
            try:
                if os.path.exists(assetPath):
                    shutil.rmtree(assetPath)
                    if not self.deleteAssetJsonPath(assetPath):
                        print("Unable to remove from json path")
                if self.core.useLocalFiles:
                    lShotPath = assetPath.replace(
                        self.core.projectPath, self.core.localProjectPath
                    )
                    if os.path.exists(lShotPath):
                        shutil.rmtree(lShotPath)
                        self.deleteAssetJsonPath(assetPath)
                break
            except Exception as e:
                msg = (
                    'Permission denied.\nAnother programm uses files in the shotfolder.\n\nThe shot "%s" could not be deleted completly.\n\n%s'
                    % (assetPath, str(e)),
                )
                result = self.core.popupQuestion(msg, buttons=["Retry", "Cancel"])
                if result == "Cancel":
                    self.core.popup("Deleting shot canceled.")
                    break


    def assetAction(self, origin, menu, index):
        cItem = origin.tw_tree.itemFromIndex(index)
        if cItem is None:
            path = self.core.assetPath
        else:
            path = cItem.data(0, Qt.UserRole)["paths"][0]

        print(f"INFO asset sending path: {path}")
        action = QAction("Create Asset l2", origin)
        action.triggered.connect(lambda: self.openCreateAssetDlg(origin, path))

        btn = QPushButton("Delete Asset")
        btn.setStyleSheet("""QPushButton { background-color: rgba(255, 0, 0, 0.2);}
        QPushButton:hover {background-color: rgba(255, 0, 0, 0.4);}""")
        btn.clicked.connect(lambda: self.confirmDelete(f"{path}"))


        #deleteAction = QAction("Delete Asset", origin)
        deleteAction = QWidgetAction(origin)
        deleteAction.setDefaultWidget(btn)

        hasId = False
        for act in menu.actions():
            if act.text() == "Omit Asset":
                hasId = True
                break


        btnView = QPushButton("View Asset")
        btnView.setStyleSheet("""QPushButton { background-color: rgba(0, 255, 0, 0.2);}
        QPushButton:hover {background-color: rgba(0, 255, 0, 0.4);}""")
        btnView.clicked.connect(lambda: self.updateUsdViewer(f"{path}"))

        #deleteAction = QAction("Delete Asset", origin)
        setOnViewer = QWidgetAction(origin)
        setOnViewer.setDefaultWidget(btnView)

        if menu.actions():
            menu.insertAction(menu.actions()[0], action)
            if hasId:
                menu.addAction(deleteAction) 
                menu.addAction(setOnViewer)
        else:
            menu.addAction(action)
            if hasId: 
                menu.addAction(deleteAction)
                menu.addAction(setOnViewer)

    
    # ======================================
    # SHOT CREATION USD ABLE
    # ======================================
    def openCreateShotDlg(self, parent):
        dlg = CreateShotCustomDlg(self.core, parent=parent)
        dlg.show()

    def shotAction(self, origin, menu, index):
        action = QAction("Create Shot l2", origin)
        action.triggered.connect(lambda: self.openCreateShotDlg(origin))

        btn = QPushButton("Delete Shot")
        btn.setStyleSheet("""QPushButton { background-color: rgba(255, 0, 0, 0.2);}
        QPushButton:hover {background-color: rgba(255, 0, 0, 0.4);}""")
        btn.clicked.connect(lambda: self.confirmDelete("Are you sure you want to delete this shot?"))

        #deleteAction = QAction("Delete Asset", origin)
        deleteAction = QWidgetAction(origin)
        deleteAction.setDefaultWidget(btn)

        hasId = False
        for act in menu.actions():
            if act.text() == "Omit Shot":
                hasId = True
                break

        if menu.actions():
            menu.insertAction(menu.actions()[0], action)
            if hasId:
                menu.addAction(deleteAction) 
        else:
            menu.addAction(action)
            if hasId: menu.addAction(deleteAction)
    
    def updateUsdViewer(self, path=None):
        if path:
            # context = args.getCurrentProduct()
            # p:\VFX_Project_30\2LOUD\Spotlight\03_Production\Assets\ASSETS\SOUNDSTAGE\PROPS\chroma
            if self.usdviewer:
                assetName = os.path.basename(path)
                self.usdviewer.reopenStage(os.path.join(path, "Export", "asset", "master", f"{assetName}_asset_master.usda"))


    def showUsdPanel(self):
        usdPath = r"P:\VFX_Project_30\2LOUD\Spotlight\03_Production\Assets\ASSETS\EXT\BUILDINGASSETS\fenceBuilding\Export\asset\master\fenceBuilding_asset_master.usda"
        print("Showing panel")
        from loudUsdViewer import tviewer #TViewer
        from loudUsdViewer import setScene #getUsdScene

        if self.usdviewer:
            return

        item_widget = QWidget()
        item_widget.setObjectName("usdViewerItem")
        item_widget.setLayoutDirection(Qt.LeftToRight)

        # --- Top label ---
        usd_versionRight = QLabel("USD VIEWER")
        usd_versionRight.setObjectName("usd_versionLabel")
        usd_versionRight.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- USD Viewer ---

        
        self.usdviewer = tviewer.TViewer(stage=setScene.getUsdScene(usdPath))
        self.usdviewer.setBaseSize(400, 400)   # use this instead of resize()

        self.usdviewer.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.usdviewer.view.updateView(resetCam=False, forceComputeBBox=True)

        # --- Vertical layout ---
        layout = QVBoxLayout(item_widget)
        layout.addWidget(usd_versionRight, alignment=Qt.AlignRight)
        layout.addWidget(self.usdviewer)   # ✅ viewer is INSIDE item_widget
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        item_widget.setLayout(layout)

        # --- Insert into productBrowser (first position if needed) ---
        #self.core.pb.productBrowser.horizontalLayout.insertWidget(0, item_widget)

        self.core.pb.productBrowser.verticalLayout_2.addWidget(self.usdviewer)

        # Add to parent layout
        # self.core.pb.productBrowser.horizontalLayout.addWidget(item_widget)
        # self.core.pb.productBrowser.addWidget(item_widget)
