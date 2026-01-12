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


from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

from loud2_viewer import WebViewer

from usdAsset_dialog import CreateAssetCustomDlg
from usdShot_dialog import CreateShotCustomDlg

from PrismUtils import PrismWidgets

from manager.userWindow import ConfigDrivenWindow

class Prism_laud2_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.setStyle = False

        print("loud2 registering callbacks for loud2 style")

        self.core.registerCallback("postInitialize", self.postInitialize, plugin=self)
        self.core.registerCallback("onProjectBrowserStartup", self.setNamings, plugin=self)
        self.core.registerCallback("onProjectBrowserStartup", self.onProjectBrowserStartup, plugin=self)

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


    @err_catcher(name=__name__)
    def isActive(self):
        return True


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

        origin.documentationMenu = QMenu("Docs l2")
        origin.documentationMenu.addAction("Organization Excel", lambda: self.showWebWindow("exc"))
        origin.documentationMenu.addAction("All Documentation", lambda: self.showWebWindow("other"))
        origin.documentationMenu.addAction("Discord", lambda: self.showWebWindow("dis"))
        origin.documentationMenu.addAction("Super Canva", lambda: self.showWebWindow("can"))
        origin.menubar.addMenu(origin.documentationMenu)


        origin.agentMenu = QMenu("2LOUD")
        origin.agentMenu.addAction("Configuration", lambda: self.showConfiguration())
        origin.menubar.addMenu(origin.agentMenu)

    def postInitialize(self):
        self.core.registerStyleSheet(path=r"P:\VFX_Project_30\r&d\tloud\00_Pipeline\Styles\loudStyle")

        if self.setStyle:
            self.core.setActiveStyleSheet("loudStyle")

    
    def showWebWindow(self, oType="dis"):
        print("Show web window")
        self.webWindow = WebViewer(windowType=oType)
        self.webWindow.show()

    def showConfiguration(self):
        print("Show configuration window")
        self.configWindow = ConfigDrivenWindow()
        self.configWindow.show()


    def confirmDeleteShot(self, msg):
        result = self.popup(msg)
        if result == "Yes":
            print("Entity deleted")

    # ======================================
    # ASSET CREATION USD ABLE
    # ======================================
    def customAssetCreation(self):
        print("Args shot custom")
        print(f"ARGS:")

    def openCreateAssetDlg(self, parent):
        print(parent)
        dlg = CreateAssetCustomDlg(self.core, parent=parent)
        dlg.show()
        entity = self.core.entities.getAsset(assetName="ss")
        print(entity)
        meta = self.core.entities.getMetaData(entity)
        print(meta)
        #self.core.entities.createAsset(self, entity, description=None, preview=None, metaData=None, dialog=None)
        #self.core.entities.createAsset()
        
    
    def assetAction(self, origin, menu, index):
        action = QAction("Create Asset l2", origin)
        action.triggered.connect(lambda: self.openCreateAssetDlg(origin))

        btn = QPushButton("Delete Asset")
        btn.setStyleSheet("""QPushButton { background-color: rgba(255, 0, 0, 0.2);}
        QPushButton:hover {background-color: rgba(255, 0, 0, 0.4);}""")
        btn.clicked.connect(lambda: self.confirmDeleteShot("Are you sure you want to delete this asset?"))


        #deleteAction = QAction("Delete Asset", origin)
        deleteAction = QWidgetAction(origin)
        deleteAction.setDefaultWidget(btn)

        hasId = False
        for act in menu.actions():
            if act.text() == "Omit Asset":
                hasId = True
                break

        if menu.actions():
            menu.insertAction(menu.actions()[0], action)
            if hasId:
                menu.addAction(deleteAction) 
        else:
            menu.addAction(action)
            if hasId: menu.addAction(deleteAction)
    
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
        btn.clicked.connect(lambda: self.confirmDeleteShot("Are you sure you want to delete this shot?"))

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
    
