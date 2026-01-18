from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from PrismUtils import PrismWidgets

from PrismUtils.Decorators import err_catcher
import os


DEPRATMENT_TASKS = [
    ["Concept", ["Concept"]], 
    ["Modeling", ["Variants", "Modeling", "Sculping", "FineDetail"]], 
    ["Texturing", ["Texturing"]], 
    ["LookDev", ["LookDev"]]
]

DEPARTMENTS = ["Default", "All"]
USD_PRODUCTS = ["Default", "All"]
ASSET_TYPES = ["Static Asset", "Dynamic Asset", "Character", "Environment"]

CUSTOM_ASSET_BASIC_USD = """#usda 1.0
(
    endTimeCode = 1
    framesPerSecond = 24
    metersPerUnit = 1
    startTimeCode = 1
    timeCodesPerSecond = 24
    upAxis = "Y"
)

def Xform "[ASSETNAME]" (
    kind = "component"
    prepend references = [
        @../../binding/master/[ASSETNAME]_binding_master.usda@</[ASSETNAME]>,
        @../../geometry/master/[ASSETNAME]_geometry_master.usdc@</[ASSETNAME]>
    ]
)
{
    def Xform "geo"
    {
    }

    def Scope "mtl" (
        prepend references = @../../materials/master/[ASSETNAME]_materials_master.usdc@</materials>
    )
    {
    }
}
"""


CUSTOM_BINDING_BASIC_USD = """#usda 1.0
(
    endTimeCode = 1
    framesPerSecond = 24
    metersPerUnit = 1
    startTimeCode = 1
    timeCodesPerSecond = 24
    upAxis = "Y"
)

def Scope "[ASSETNAME]" (
    kind = "component"
)
{
    def Xform "geo" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {
        rel material:binding = </[ASSETNAME]/mtl/[ASSETNAME]_MTL>
    }

    def Scope "mtl" (
        prepend references = @../../materials/master/[ASSETNAME]_materials_master.usdc@</materials>
    )
    {
    }
}
"""


class CreateAssetCustomDlg2(PrismWidgets.CreateItem):
    def __init__(self, core, parent=None, startText=None):
        self.startText = ""
        super(CreateAssetCustomDlg, self).__init__(startText=self.startText.lstrip("/"), core=core, mode="assetHierarchy", allowChars=["/"])

        self.parentDlg = parent
        self.core = core
        self.thumbXres = 250
        self.thumbYres = 141
        self.setupUi_()

    def setupUi_(self):
        self.setWindowTitle("Create 2Loud Asset...")
        self.resize(450, 750)
        layout = self.layout()

        print("Current asset creation")

    def accept(self):
        print("Custom asset creation generation")
        super().accept()

class CreateAssetCustomDlg(PrismWidgets.CreateItem):
    def __init__(self, core, parent=None, startText=None, path=None):
        startText = startText or ""
        super(CreateAssetCustomDlg, self).__init__(startText=startText.lstrip("/"), core=core, mode="assetHierarchy", allowChars=["/"])
        self.parentDlg = parent
        self.core = core
        self.thumbXres = 250
        self.thumbYres = 141
        self.imgPath = ""
        self.pmap = None

        self.path = path

        self.loudCreateAssetImagePath = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Icons\2Loud_tool.png"
        self.assetPath = r"P:\VFX_Project_30\2LOUD\Spotlight\03_Production\Assets"

        self.setupUi_()

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create 2loud custom Asset...")
        self.core.parentWindow(self, parent=self.parentDlg)

        # Setup button icons
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "create.png"
        )
        iconC = self.core.media.getColoredIcon(iconPath)
        self.buttonBox.buttons()[0].setIcon(iconC)
        self.buttonBox.buttons()[0].hide()

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.buttonBox.buttons()[2].setIcon(icon)

        # Configure item input
        self.w_item.setContentsMargins(0, 0, 0, 0)
        self.e_item.setToolTip("Asset name or comma separated list of asset names.\nParent folders can be included using slashes.")
        self.l_item.setText("Asset(s):")
        
        if (len(self.removePath()) <= 0): 
            pathAddText = ""
        else: 
            pathAddText = self.removePath() + "/"
        self.e_item.setText(pathAddText)

        # Layout margins
        self.layout().setContentsMargins(20, 20, 20, 20)

        # =======================================
        # Logo and Title Section
        # =======================================
        self.logoLabel = QLabel(self)
        self.logoLabel.setFixedSize(50, 50)
        self.logoLabel.setScaledContents(True)

        if os.path.exists(self.loudCreateAssetImagePath):
            pixmap = QPixmap(self.loudCreateAssetImagePath)
            self.logoLabel.setPixmap(pixmap)

        self.w_logoContainer = QWidget()
        lo_logo = QHBoxLayout(self.w_logoContainer)
        lo_logo.setContentsMargins(10, 10, 10, 10)
        lo_logo.addWidget(self.logoLabel, alignment=Qt.AlignCenter)

        self.layout().insertWidget(0, self.w_logoContainer, alignment=Qt.AlignHCenter)

        self.titleLabel = QLabel("2Loud Asset Creator", self)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: white;
            }
        """)
        self.layout().insertWidget(0, self.titleLabel, alignment=Qt.AlignHCenter)

        # =======================================
        # Thumbnail Section (between Asset and Description)
        # =======================================
        self.w_thumbnail = QWidget()
        self.lo_thumbnail = QHBoxLayout(self.w_thumbnail)
        self.lo_thumbnail.setContentsMargins(0, 0, 0, 0)
        self.l_thumbnailStr = QLabel("Thumbnail:")
        self.l_thumbnail = QLabel()
        self.lo_thumbnail.addWidget(self.l_thumbnailStr)
        self.lo_thumbnail.addWidget(self.l_thumbnail)
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.w_thumbnail)

        # =======================================
        # Asset Settings Section
        # =======================================
        self.w_settings = QWidget()
        self.assetSettings_Layout = QVBoxLayout(self.w_settings)
        self.assetSettings_Layout.setContentsMargins(0, 0, 0, 0)

        # Title with line separator
        self.w_assetSettings_header = QWidget()
        self.lo_assetSettings_header = QHBoxLayout(self.w_assetSettings_header)
        self.lo_assetSettings_header.setContentsMargins(0, 0, 0, 0)
        
        self.assetSettings_title = QLabel("Asset Settings")
        self.assetSettings_title.setStyleSheet("font-weight: bold;")
        
        self.assetSettings_line = QFrame()
        self.assetSettings_line.setFrameShape(QFrame.HLine)
        self.assetSettings_line.setFrameShadow(QFrame.Sunken)
        
        self.lo_assetSettings_header.addWidget(self.assetSettings_title)
        self.lo_assetSettings_header.addWidget(self.assetSettings_line)
        
        self.assetSettings_Layout.addWidget(self.w_assetSettings_header)

        # Asset Info Section
        self.assetInf_title = QLabel("Asset Info")
        self.assetSettings_Layout.addWidget(self.assetInf_title)

        # First line: ID Field
        self.assetInf_widget1 = QWidget()
        self.assetInf_layout1 = QHBoxLayout(self.assetInf_widget1)
        self.assetInf_layout1.setContentsMargins(0, 0, 0, 0)
        self.assetInf_layout1.addSpacing(10)

        self.ID_label = QLabel("ID:")
        self.ID_field = QLineEdit()
        self.ID_field.setReadOnly(True)
        self.ID_field.setStyleSheet("QLineEdit { color: grey;}")
        self.ID_field.setText("feature in process")
        self.ID_field.setFixedWidth(150)

        self.assetInf_layout1.addWidget(self.ID_label)
        self.assetInf_layout1.addWidget(self.ID_field)
        self.assetInf_layout1.addStretch()

        self.assetSettings_Layout.addWidget(self.assetInf_widget1)

        # Second line: Ch Dependant and Task Preset
        self.assetInf_widget2 = QWidget()
        self.assetInf_layout2 = QHBoxLayout(self.assetInf_widget2)
        self.assetInf_layout2.setContentsMargins(0, 0, 0, 0)
        self.assetInf_layout2.addSpacing(10)

        # Ch Dependant Checkbox (label in front)
        self.ChDependant_label = QLabel("Ch Dependant:")
        self.ChDependant_check = QCheckBox()
        self.ChDependant_check.setChecked(False)
        self.assetInf_layout2.addWidget(self.ChDependant_label)
        self.assetInf_layout2.addWidget(self.ChDependant_check)
        self.assetInf_layout2.addStretch()

        # Task Preset Section
        self.taskPreset_label = QLabel("Task Preset:")
        self.taskPreset_combobox = QComboBox()
        self.taskPreset_combobox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.assetInf_layout2.addWidget(self.taskPreset_label)
        self.assetInf_layout2.addWidget(self.taskPreset_combobox)

        self.assetSettings_Layout.addWidget(self.assetInf_widget2)

        # Load presets
        presets = self.core.projects.getAssetTaskPresets()
        if presets:
            for preset in presets:
                self.taskPreset_combobox.addItem(preset.get("name", ""), preset)

        # =======================================
        # Additional Settings (Subdivision, LoD, TX Size)
        # =======================================
        self.w_additionalSettings = QWidget()
        self.lo_additionalSettings = QHBoxLayout(self.w_additionalSettings)
        self.lo_additionalSettings.setContentsMargins(0, 0, 0, 0)

        # Subdivision
        self.l_subdivision = QLabel("Subdivision:")
        self.sb_subdivision = QSpinBox()
        self.sb_subdivision.setRange(1, 10)
        self.sb_subdivision.setValue(2)

        # LoD
        self.l_tx = QLabel("LoD:")
        self.sb_tx = QSpinBox()
        self.sb_tx.setRange(1, 16)
        self.sb_tx.setValue(2)

        # TX Size
        self.l_txSize = QLabel("TX Size:")
        self.cb_txSize = QComboBox()
        self.cb_txSize.addItems(["512", "1024", "2048", "4096", "8192", "16384"])
        self.cb_txSize.setCurrentText("1024")

        self.lo_additionalSettings.addWidget(self.l_subdivision)
        self.lo_additionalSettings.addWidget(self.sb_subdivision)
        self.lo_additionalSettings.addWidget(self.l_tx)
        self.lo_additionalSettings.addWidget(self.sb_tx)
        self.lo_additionalSettings.addWidget(self.l_txSize)
        self.lo_additionalSettings.addWidget(self.cb_txSize)

        self.assetSettings_Layout.addWidget(self.w_additionalSettings)
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.w_settings)

        # =======================================
        # Description Section
        # =======================================
        self.l_info = QLabel("Description:")
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.l_info)
        self.te_text = QTextEdit()
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.te_text)

        # =======================================
        # Metadata Widget
        # =======================================
        import MetaDataWidget
        self.w_meta = MetaDataWidget.MetaDataWidget(self.core)
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.w_meta)

        # =======================================
        # Create Button (before buttonBox)
        # =======================================
        self.createBtn = QPushButton("Create 2Loud Asset", self)
        self.createBtn.setIcon(iconC)
        self.createBtn.setToolTip("Create asset using 2Loud pipeline")
        self.createBtn.clicked.connect(self.onLoud2CreateButtonClicked)
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox), self.createBtn)

        # =======================================
        # Thumbnail Setup
        # =======================================
        imgFile = os.path.join(self.core.projects.getFallbackFolder(), "noFileSmall.jpg")
        pmap = self.core.media.getPixmapFromPath(imgFile)
        if pmap:
            self.l_thumbnail.setMinimumSize(pmap.width(), pmap.height())
            self.l_thumbnail.setPixmap(pmap)

        self.l_thumbnail.setContextMenuPolicy(Qt.CustomContextMenu)

        self.l_thumbnail.mouseReleaseEvent = self.previewMouseReleaseEvent
        self.l_thumbnail.customContextMenuRequested.connect(self.rclThumbnail)
        
        self.resize(450, 550)


    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(450, 450)
    
    def assetOverlapError(self, assetName):
        if self.core.entities.getAsset(assetName):
            title = "⚠️⚠️  ASSET DELATION - EXTREME WARNING  ⚠️⚠️"
            msg = (
                f"Asset already exists. Unable to create, abort mission. "
            )
            self.core.popup(msg, title=title, icon=QMessageBox.Critical)
            return False
        else: return True

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.createBtn.click()
        else:
            super().keyPressEvent(event)

    @err_catcher(name=__name__)
    def previewMouseReleaseEvent(self, event):
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                self.rclThumbnail()

    @err_catcher(name=__name__)
    def rclThumbnail(self, pos=None):
        rcmenu = QMenu(self)

        copAct = QAction("Capture thumbnail", self)
        copAct.triggered.connect(self.capturePreview)
        rcmenu.addAction(copAct)

        copAct = QAction("Browse thumbnail...", self)
        copAct.triggered.connect(self.browsePreview)
        rcmenu.addAction(copAct)

        clipAct = QAction("Paste thumbnail from clipboard", self)
        clipAct.triggered.connect(self.pastePreviewFromClipboard)
        rcmenu.addAction(clipAct)

        rcmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def capturePreview(self):
        from PrismUtils import ScreenShot

        previewImg = ScreenShot.grabScreenArea(self.core)

        if previewImg:
            previewImg = self.core.media.scalePixmap(
                previewImg,
                self.thumbXres,
                self.thumbYres,
            )
            self.setPixmap(previewImg)

    @err_catcher(name=__name__)
    def pastePreviewFromClipboard(self):
        pmap = self.core.media.getPixmapFromClipboard()
        if not pmap:
            self.core.popup("No image in clipboard.", parent=self)
            return

        pmap = self.core.media.scalePixmap(
            pmap,
            self.thumbXres,
            self.thumbYres,
        )
        self.setPixmap(pmap)

    @err_catcher(name=__name__)
    def browsePreview(self):
        formats = "Image File (*.jpg *.png *.exr)"

        imgPath = QFileDialog.getOpenFileName(
            self, "Select thumbnail-image", self.imgPath, formats
        )[0]

        if not imgPath:
            return

        if os.path.splitext(imgPath)[1] == ".exr":
            pmsmall = self.core.media.getPixmapFromExrPath(
                imgPath,
                width=self.thumbXres,
                height=self.thumbYres,
            )
        else:
            pm = self.core.media.getPixmapFromPath(imgPath)
            if pm.width() == 0:
                warnStr = "Cannot read image: %s" % imgPath
                self.core.popup(warnStr, parent=self)
                return

            pmsmall = self.core.media.scalePixmap(
                pm,
                self.thumbXres,
                self.thumbYres,
            )

        self.setPixmap(pmsmall)

    @err_catcher(name=__name__)
    def setPixmap(self, pmsmall):
        self.pmap = pmsmall
        self.l_thumbnail.setMinimumSize(self.pmap.width(), self.pmap.height())
        self.l_thumbnail.setPixmap(self.pmap)

    @err_catcher(name=__name__)
    def getDescription(self):
        return self.te_text.toPlainText()
    
    @err_catcher(name=__name__)
    def getThumbnail(self):
        return self.pmap
    
    def getDataValues(self):
        values = {
            "subdivision": self.sb_subdivision.value(),
            "lod": self.sb_tx.value(),
            "txSize": (
                self.cb_txSize.currentText()
                if hasattr(self.cb_txSize, "currentText")
                else self.cb_txSize.value()
            )
        }
        return values
    

    def camelCase(self, text):
        path, filename = os.path.split(text)
        filename = filename[:1].lower() + filename[1:]


        return os.path.join(path, filename) if path else filename


    def saveUsdPathEmpty(self, assetName, assetProduct, usdExample, version, save_dir=None, format="usda"):
        if not save_dir: return None

        assetName = self.camelCase(assetName) 

        file_name = f"{assetName}_{assetProduct}_{version}.{format}"
        save_path = os.path.join(save_dir, file_name)
        os.makedirs(save_dir, exist_ok=True)
        usdTemplate = usdExample.replace("[ASSETNAME]", assetName)

        with open(save_path, "w") as f:
            f.write(usdTemplate)
        print(f"USDA saved at: {save_path}")
        return save_path
    

    def saveUsdCopyPath(self, assetName, assetProduct, version, save_dir=None):
        if not save_dir: return None

        assetName = self.camelCase(assetName) 

        new_file_name = f"{assetName}_{assetProduct}_{version}.usdc"
        old_file_material_path = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Plugins\Custom\laud2\Scripts\materials\basicMaterial_MTL.usdc"
        save_path = os.path.join(save_dir, new_file_name)
        
        import shutil

        shutil.copy(old_file_material_path, save_path)

        print(f"USDA saved at: {save_path}")
        return save_path
    
    def deleteFileFromPath(self, file_path):
        try:
            os.remove(file_path)
        except FileNotFoundError:
            print("File not found:", file_path)
        except PermissionError:
            print("No permission to delete:", file_path)
        
    def removePath(self):
        base = os.path.normpath(self.assetPath)
        full = os.path.normpath(self.path)

        if full.startswith(base):
            relative = full[len(base):].lstrip(os.sep)
        else:
            relative = full

        return relative.replace(os.sep, "/")

    def onLoud2CreateButtonClicked(self, dataValues):
        #entity = {'type': 'asset', 'asset_path': 'ASSET NAME'}
        #metadata = {'sd': {'value': '1', 'show': True}, 's': {'value': 's', 'show': True}, 'a': {'value': 'a', 'show': True}}

        # if self.assetOverlapError():
        



        assetName = self.e_item.text().strip()
        description = self.getDescription()
        thumbnail = self.getThumbnail()

        metValues = self.getDataValues()
        assetName = self.camelCase(assetName) 
        assetCoreName = assetName.split("\\")[-1]

        if not assetName:
            print("No asset name")
            return

        if not description:
            description = ""

        entity = {
            'type': 'asset', 
            'asset_path': f'{assetName}'
        }
        print(f"Asset created in path: {assetName}")

        metadata = {'isAsset2loud': 
                        {'value': 'True', 'show': False},
                    'subdivision': 
                        {'value': f'{metValues["subdivision"]}', 'show': True}, 
                    'LoD': 
                        {'value': f'{metValues["lod"]}', 'show': True},
                    'txSize': 
                        {'value': f'{metValues["txSize"]}', 'show': True},
                    'assetType': 
                        {'value': 'staticAsset', 'show': False}
                    }

        result = self.core.entities.createEntity(
            entity=entity,
            description=description, 
            metaData=metadata,
            preview=thumbnail
        )

        products = ["asset", "binding", "geometry", "materials", "mesh", "textures"]
        filesToDelete = []
        for prod in products:
            path = self.core.products.createProduct(entity=entity, product=f"{prod}")
            print(f"Created product: {prod} {entity}")
            if prod == "asset":
                pt = self.saveUsdPathEmpty(assetCoreName, prod, CUSTOM_ASSET_BASIC_USD, "temp", r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\temp")
                productInfo = self.core.products.ingestProductVersion([pt], entity, prod)
                self.core.products.updateMasterVersion(productInfo["createdFiles"][0])
                filesToDelete.append(pt)
            if prod == "binding":
                pt = self.saveUsdPathEmpty(assetCoreName, prod, CUSTOM_BINDING_BASIC_USD, "temp", r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\temp")
                productInfo = self.core.products.ingestProductVersion([pt], entity, prod)
                self.core.products.updateMasterVersion(productInfo["createdFiles"][0])
                filesToDelete.append(pt)
            if prod == "materials":
                pt = self.saveUsdCopyPath(assetCoreName, prod, "temp", r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\temp")
                productInfo = self.core.products.ingestProductVersion([pt], entity, prod)
                self.core.products.updateMasterVersion(productInfo["createdFiles"][0])
                filesToDelete.append(pt)

            print("Prod created")

        for dep in DEPRATMENT_TASKS:
            self.core.entities.createDepartment(dep[0], entity, createCat=False)
            for task in dep[1]:
                self.core.entities.createCategory(entity, dep[0], task)

        for deleteFile in filesToDelete:
            self.deleteFileFromPath(deleteFile)

        self.core.pb.refreshUI()
        print(result)
        print("created custom 2loud asset")