# usdShot_dialogGui.py
# 
# Codi per a la creacio de custom shots loud2
# 


from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from PrismUtils import PrismWidgets


DEPARTMENTS = ["Default", "All"]
USD_PRODUCTS = ["Default", "All"]


class CreateShotCustomDlg(PrismWidgets.CreateItem):
    def __init__(self, core, parent=None, startText=None):
        self.startText = ""
        super(CreateShotCustomDlg, self).__init__(startText=self.startText.lstrip("/"), core=core, mode="assetHierarchy", allowChars=["/"])
        self.parentDlg = parent
        self.core = core
        self.thumbXres = 250
        self.thumbYres = 141
        self.setupUi_()

    def setupUi_(self):
        self.setWindowTitle("Create 2Loud Shot...")
        self.resize(450, 750)

        # Main Layout
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        super_layout = self.layout()
        if not super_layout:
            return

        # Remove all layout items except the last one (usually the Prism buttons)
        for i in reversed(range(super_layout.count() - 1)):
            item = super_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._deleteLayout(item.layout())

        # Insert custom container at the top, pushing buttons to the bottom
        super_layout.insertWidget(0, container)
                

    def update_dynamic_ui(self, preset_name):
        # Switch stack page
        if preset_name == "Asset":
            self.stack.setCurrentWidget(self.page_asset)
        elif preset_name == "Character":
            self.stack.setCurrentWidget(self.page_char)
        elif preset_name == "Environment":
            self.stack.setCurrentWidget(self.page_env)

    def accept(self):
        """
        Aqui va la logic per crear el asset i tot el systema de usd en les carpetes corresponents. 
    
        ara nomes fem un print de confirmacio
        """
        print("... Generating .usd files ...")
        print("... Success!")
        print("=" * 40)
        super().accept()


    def _deleteLayout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self._deleteLayout(item.layout())
        layout.setParent(None)