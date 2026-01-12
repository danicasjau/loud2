from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from PrismUtils import PrismWidgets


DEPARTMENTS = ["Default", "All"]
USD_PRODUCTS = ["Default", "All"]
ASSET_PRESSETS = ["Asset Static", "Asset Dynamic", "Character", "Environment"]

PRODUCTS_ALL = [
    "Asset",
    "Geometria",
    "Material",
    "Textures",
    "Highpoly",
    "Rig",
    "Groom"
]

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
        self.setWindowTitle("Create 2Loud Asset...")
        self.resize(450, 750)

        # Main Layout
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)


        super_layout = self.layout()   # Prism base layout

        count = super_layout.count()

        # Remove all layout items except the last one
        for i in reversed(range(count - 1)):
            item = super_layout.takeAt(i)

            if item.widget():
                item.widget().setParent(None)

            elif item.layout():
                self._deleteLayout(item.layout())

        last_index = super_layout.count() - 1
        if last_index < 0:
            last_index = 0   # safety

        super_layout.insertWidget(last_index, container)
                
        # --- TOP SECTION ---
        
        # Task Preset (Moved to Top)
        self.lo_preset = QHBoxLayout()
        self.lo_preset.addWidget(QLabel("Task Preset:"))
        self.cb_taskPreset = QComboBox()
        self.cb_taskPreset.addItems(ASSET_PRESSETS) 
        self.lo_preset.addWidget(self.cb_taskPreset)
        self.lo_preset.addStretch()
        self.main_layout.addLayout(self.lo_preset)
        
        self.cb_taskPreset.currentTextChanged.connect(self.update_dynamic_ui)

        # Asset Name Area
        self.header_layout = QHBoxLayout()
        self.l_assetIcon = QLabel("ICON") 
        self.l_assetIcon.setFixedSize(25, 25)
        self.l_assetIcon.setStyleSheet("background-color: #555; border-radius: 5px;")
        self.l_assetIcon.setAlignment(Qt.AlignCenter)
        self.header_layout.addWidget(self.l_assetIcon)
        
        self.l_item = QLabel("Asset Name:")
        self.header_layout.addWidget(self.l_item)
        self.main_layout.addLayout(self.header_layout)

        # Asset Name Input
        self.e_item = QLineEdit(self.startText)
        self.e_item.setPlaceholderText("Enter asset name...")
        self.main_layout.addWidget(self.e_item)
        self.e_item.setFocus()
        
        # --- DYNAMIC MIDDLE SECTION ---
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # 1. Asset Page
        self.page_asset = QWidget()
        page_asset_layout = QVBoxLayout(self.page_asset)
        page_asset_layout.setContentsMargins(0, 10, 0, 10)
        
        # Asset: Subdiv
        l_subdiv = QHBoxLayout()
        l_subdiv.addWidget(QLabel("Subdivision Level:"))
        self.sb_subdiv = QSpinBox()
        self.sb_subdiv.setRange(0, 5)
        l_subdiv.addWidget(self.sb_subdiv)
        page_asset_layout.addLayout(l_subdiv)
        
        # Asset: Def Level
        l_def = QHBoxLayout()
        l_def.addWidget(QLabel("Definition Level:"))
        self.cb_def = QComboBox()
        self.cb_def.addItems(["Low", "Medium", "High", "Ultra"])
        l_def.addWidget(self.cb_def)
        page_asset_layout.addLayout(l_def)
        
        # Asset: Texture Size
        l_tex = QHBoxLayout()
        l_tex.addWidget(QLabel("Texture Size:"))
        self.cb_tex = QComboBox()
        self.cb_tex.addItems(["512", "1k", "2k", "4k", "8k"])
        l_tex.addWidget(self.cb_tex)
        page_asset_layout.addLayout(l_tex)
        
        # Asset: ID
        l_id_asset = QHBoxLayout()
        l_id_asset.addWidget(QLabel("Generate ID:"))
        self.chb_id_asset = QCheckBox()
        self.chb_id_asset.setChecked(True)
        l_id_asset.addWidget(self.chb_id_asset)
        page_asset_layout.addLayout(l_id_asset)
        
        self.stack.addWidget(self.page_asset)
        
        # 2. Character Page
        self.page_char = QWidget()
        page_char_layout = QVBoxLayout(self.page_char)
        page_char_layout.setContentsMargins(0, 10, 0, 10)
        
        # Char: ID
        l_id_char = QHBoxLayout()
        l_id_char.addWidget(QLabel("Generate ID:"))
        self.chb_id_char = QCheckBox()
        self.chb_id_char.setChecked(True)
        l_id_char.addWidget(self.chb_id_char)
        page_char_layout.addLayout(l_id_char)
        
        # Char: Importance
        l_imp = QHBoxLayout()
        l_imp.addWidget(QLabel("Importance ID:"))
        self.sb_imp = QSpinBox()
        l_imp.addWidget(self.sb_imp)
        page_char_layout.addLayout(l_imp)
        
        # Char: Versions
        l_ver = QHBoxLayout()
        l_ver.addWidget(QLabel("Versions Int:"))
        self.sb_ver = QSpinBox()
        l_ver.addWidget(self.sb_ver)
        page_char_layout.addLayout(l_ver)
        
        self.stack.addWidget(self.page_char)
        
        # 3. Environment Page
        self.page_env = QWidget()
        page_env_layout = QVBoxLayout(self.page_env)
        page_env_layout.setContentsMargins(0, 10, 0, 10)
        
        # Env: ID
        l_id_env = QHBoxLayout()
        l_id_env.addWidget(QLabel("Generate ID:"))
        self.chb_id_env = QCheckBox()
        self.chb_id_env.setChecked(True)
        l_id_env.addWidget(self.chb_id_env)
        page_env_layout.addLayout(l_id_env)
        
        self.stack.addWidget(self.page_env)
        
        # --- COMMON BOTTOM SECTION (Visible for ALL) ---
        
        # Description (Universal)
        self.l_info = QLabel("Description:")
        self.main_layout.addWidget(self.l_info)
        self.te_description = QTextEdit()
        self.te_description.setMaximumHeight(80)
        self.main_layout.addWidget(self.te_description)

        # Thumbnail (Universal)
        self.w_thumbnail = QWidget()
        self.lo_thumbnail = QHBoxLayout(self.w_thumbnail)
        self.lo_thumbnail.setContentsMargins(0, 0, 0, 0)
        self.l_thumbnailStr = QLabel("Thumbnail:")
        self.l_thumbnail = QLabel()
        self.l_thumbnail.setFixedSize(100, 60)
        self.l_thumbnail.setStyleSheet("border: 1px dashed gray; background-color: #333;")
        self.l_thumbnail.setAlignment(Qt.AlignCenter)
        self.l_thumbnail.setText("No Image")
        
        self.lo_thumbnail.addWidget(self.l_thumbnailStr)
        self.lo_thumbnail.addWidget(self.l_thumbnail)
        self.lo_thumbnail.addStretch()
        self.main_layout.addWidget(self.w_thumbnail)

        # Spacer to push bottom configs down
        self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addItem(self.spacer)

        # --- BOTTOM CONFIGS (Departments & USD Products) ---
        
        bottom_configs = QWidget()
        bc_layout = QVBoxLayout(bottom_configs)
        bc_layout.setContentsMargins(0, 0, 0, 0)

        # Departments
        self.lo_dept = QHBoxLayout()
        self.lo_dept.addWidget(QLabel("Departments:"))
        self.cb_dept = QComboBox()
        self.cb_dept.addItems(DEPARTMENTS)
        self.lo_dept.addWidget(self.cb_dept)
        self.lo_dept.addStretch()
        bc_layout.addLayout(self.lo_dept)

        # USD Products
        self.lo_usd = QHBoxLayout()
        self.lo_usd.addWidget(QLabel("USD Products:"))
        self.cb_usd = QComboBox()
        self.cb_usd.addItems(USD_PRODUCTS)
        self.lo_usd.addWidget(self.cb_usd)
        self.lo_usd.addStretch()
        bc_layout.addLayout(self.lo_usd)
        
        self.main_layout.addWidget(bottom_configs)

        # Buttons (Create / Cancel)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept) 
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.buttons()[0].setText("Create")
        self.main_layout.addWidget(self.buttonBox)
        
        # Initial Trigger
        self.update_dynamic_ui(self.cb_taskPreset.currentText())

    def update_dynamic_ui(self, preset_name):
        # Switch stack page
        if preset_name == "Asset Dynamic" or preset_name == "Asset Static":
            self.stack.setCurrentWidget(self.page_asset)
        elif preset_name == "Character":
            self.stack.setCurrentWidget(self.page_char)
        elif preset_name == "Environment":
            self.stack.setCurrentWidget(self.page_env)

    def accept(self):
        """Mock USD Asset Creation Logic"""
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