from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from PrismUtils import PrismWidgets

from PrismUtils.Decorators import err_catcher
import os

DEPARTMENTS = ["Default", "All"]
USD_PRODUCTS = ["Default", "All"]
ASSET_TYPES = ["Static Asset", "Dynamic Asset", "Character", "Environment"]

CUSTOM_ASSET_BASIC_USD = """
#usda 1.0
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
        @../../binding/master/[ASSETNAME]_binding_master.usda@</sandBag>,
        @../../geometry/master/[ASSETNAME]_geometry_master.usdc@</sandBag>
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
    def __init__(self, core, parent=None, startText=None):
        startText = startText or ""
        super(CreateAssetCustomDlg, self).__init__(startText=startText.lstrip("/"), core=core, mode="assetHierarchy", allowChars=["/"])
        self.parentDlg = parent
        self.core = core
        self.thumbXres = 250
        self.thumbYres = 141
        self.imgPath = ""
        self.pmap = None

        self.loudCreateAssetImagePath = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Icons\2Loud_tool.png"

        self.setupUi_()

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create 2loud custom Asset...")
        self.core.parentWindow(self, parent=self.parentDlg)

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

        self.w_item.setContentsMargins(0, 0, 0, 0)
        self.e_item.setFocus()
        self.e_item.setToolTip("Asset name or comma separated list of asset names.\nParent nFolders can be included using slashes.")
        self.l_item.setText("Asset(s):")
        # self.l_assetIcon = QLabel()
        # self.w_item.layout().insertWidget(0, self.l_assetIcon)
        # iconPath = os.path.join(
        #     self.core.prismRoot, "Scripts", "UserInterfacesPrism", "asset.png"
        # )
        # icon = self.core.media.getColoredIcon(iconPath)
        # self.l_assetIcon.setPixmap(icon.pixmap(15, 15))

        # =======================================
        # Custom layout working
        # =======================================

        self.layout().setContentsMargins(20, 20, 20, 20)

        self.logoLabel = QLabel(self)
        self.logoLabel.setFixedSize(50, 50)
        self.logoLabel.setScaledContents(True)

        pixmap = QPixmap(self.loudCreateAssetImagePath)  # ← your given image path
        self.logoLabel.setPixmap(pixmap)

        self.w_logoContainer = QWidget()
        lo_logo = QHBoxLayout(self.w_logoContainer)
        lo_logo.setContentsMargins(10, 10, 10, 10)  # top, left, bottom, right
        lo_logo.addWidget(self.logoLabel, alignment=Qt.AlignCenter)

        # Insert the container into the main layout
        self.layout().insertWidget(
            0,   # top of the layout
            self.w_logoContainer,
            alignment=Qt.AlignHCenter
        )

        self.titleLabel = QLabel("2Loud Asset Creator", self)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: white;  /* or a Prism theme color */
            }
        """)

        self.layout().insertWidget(
            0,  # top of layout
            self.titleLabel,
            alignment=Qt.AlignHCenter
        )

        # =======================================
        # End of custom layout working
        # =======================================


        self.createBtn = QPushButton("Create 2Loud Asset", self)
        self.createBtn.setIcon(iconC)
        self.createBtn.setToolTip("Create asset using 2Loud pipeline")
        self.createBtn.clicked.connect(self.onLoud2CreateButtonClicked)

        self.layout().addWidget(self.createBtn)


        self.w_thumbnail = QWidget()
        self.lo_thumbnail = QHBoxLayout(self.w_thumbnail)
        self.lo_thumbnail.setContentsMargins(0, 0, 0, 0)
        self.l_thumbnailStr = QLabel("Thumbnail:")
        self.l_thumbnail = QLabel()
        self.lo_thumbnail.addWidget(self.l_thumbnailStr)
        self.lo_thumbnail.addWidget(self.l_thumbnail)
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.w_thumbnail)

        self.w_taskPreset = QWidget()
        self.lo_taskPreset = QHBoxLayout(self.w_taskPreset)
        self.lo_taskPreset.setContentsMargins(0, 0, 0, 0)
        self.l_taskPreset = QLabel("Task Preset:")
        self.chb_taskPreset = QCheckBox()
        self.cb_taskPreset = QComboBox()
        self.cb_taskPreset.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.lo_taskPreset.addWidget(self.l_taskPreset)
        self.lo_taskPreset.addStretch()
        self.lo_taskPreset.addWidget(self.chb_taskPreset)
        self.lo_taskPreset.addWidget(self.cb_taskPreset)
        self.cb_taskPreset.setEnabled(self.chb_taskPreset.isChecked())
        self.chb_taskPreset.toggled.connect(self.cb_taskPreset.setEnabled)
        presets = self.core.projects.getAssetTaskPresets()
        if presets:
            for preset in presets:
                self.cb_taskPreset.addItem(preset.get("name", ""), preset)

            self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.w_taskPreset)
    

        # =================================
        # CUSTOM DATA CONFIGURATION
        # =================================
        self.w_settings = QWidget()
        self.lo_settings = QHBoxLayout(self.w_settings)
        self.lo_settings.setContentsMargins(0, 0, 0, 0)

        self.l_subdivision = QLabel("Subdivision:")
        self.sb_subdivision = QSpinBox()
        self.sb_subdivision.setRange(1, 10)
        self.sb_subdivision.setValue(2)

        self.l_tx = QLabel("LoD:")
        self.sb_tx = QSpinBox()
        self.sb_tx.setRange(1, 16)
        self.sb_tx.setValue(2)

        self.l_txSize = QLabel("TX Size:")
        self.cb_txSize = QComboBox()
        self.cb_txSize.addItems(["512", "1024", "2048", "4096", "8192", "16384"])
        self.cb_txSize.setCurrentText("1024")

        self.lo_settings.addWidget(self.l_subdivision)
        self.lo_settings.addWidget(self.sb_subdivision)
        self.lo_settings.addWidget(self.l_tx)
        self.lo_settings.addWidget(self.sb_tx)
        self.lo_settings.addWidget(self.l_txSize)
        self.lo_settings.addWidget(self.cb_txSize)

        self.layout().insertWidget(
            self.layout().indexOf(self.buttonBox) - 2,
            self.w_settings
        )


        # =================================
        # END OF CUSTOM DATA CONFIGURATION
        # =================================


        self.l_info = QLabel("Description:")
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.l_info)
        self.te_text = QTextEdit()
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.te_text)

        import MetaDataWidget
        self.w_meta = MetaDataWidget.MetaDataWidget(self.core)
        self.layout().insertWidget(
            self.layout().indexOf(self.buttonBox)-2, self.w_meta
        )
        # self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.layout().insertItem(
        #     self.layout().indexOf(self.buttonBox), self.spacer
        # )

        imgFile = os.path.join(
            self.core.projects.getFallbackFolder(), "noFileSmall.jpg"
        )
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

    def saveUsdPathEmpty(self, assetName, assetProduct, version, save_dir=None):
        if not save_dir: return None
        file_name = f"{assetName}_{assetProduct}_{version}.usda"
        save_path = os.path.join(save_dir, file_name)
        os.makedirs(save_dir, exist_ok=True)
        usdTemplate = CUSTOM_ASSET_BASIC_USD .replace("[ASSETNAME]", assetName)

        with open(save_path, "w") as f:
            f.write(usdTemplate)
        print(f"USDA saved at: {save_path}")
        return save_path
    
    def deleteFileFromPath(self, file_path):
        try:
            os.remove(file_path)
        except FileNotFoundError:
            print("File not found:", file_path)
        except PermissionError:
            print("No permission to delete:", file_path)



    def onLoud2CreateButtonClicked(self, dataValues):
        #entity = {'type': 'asset', 'asset_path': 'ASSET NAME'}
        #metadata = {'sd': {'value': '1', 'show': True}, 's': {'value': 's', 'show': True}, 'a': {'value': 'a', 'show': True}}

        assetName = self.e_item.text().strip()
        description = self.getDescription()
        thumbnail = self.getThumbnail()

        metValues = self.getDataValues()



        if not assetName:
            print("No asset name")
            return

        if not description:
            description = ""

        entity = {
            'type': 'asset', 
            'asset_path': f'{assetName}'
        }

        metadata = {'isAsset2loud': 
                        {'value': 'True', 'show': False}, 
                    'id': 
                        {'value': 'MATRICULATEST', 'show': True}, 
                    'subdivision': 
                        {'value': f'{metValues["subdivision"]}', 'show': True}, 
                    'lod': 
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
            if prod == "asset":
                pt = self.saveUsdPathEmpty(assetName, prod, "temp", r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\temp")
                productInfo = self.core.products.ingestProductVersion([pt], entity, prod)
                self.core.products.updateMasterVersion(productInfo["createdFiles"][0])
                filesToDelete.append(pt)
            print("Prod created")

        for deleteFile in filesToDelete:
            self.deleteFileFromPath(deleteFile)

        self.core.pb.refreshUI()
        print(result)
        print("created custom 2loud asset")