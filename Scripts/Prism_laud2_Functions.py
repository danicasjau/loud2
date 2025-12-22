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
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.


from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

from loud2_viewer import WebViewer

from usdAsset_dialog import CreateAssetCustomDlg
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
            "openPBAssetContextMenu", self.productCheck, plugin=self
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


    # ======================================
    # ASSET CREATION USD ABLE
    # ======================================
    def openCreateAssetDlg(self, parent):
        dlg = CreateAssetCustomDlg(self.core, parent=parent)
        dlg.show()

    def productCheck(self, origin, menu, index):
        action = QAction("Loud ASSET", origin)
        action.triggered.connect(lambda: self.openCreateAssetDlg(origin))
        menu.addAction(action)
