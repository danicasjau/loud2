from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from PrismUtils import PrismWidgets

from PrismUtils.Decorators import err_catcher
import os

DEPARTMENTS = ["Default", "All"]
USD_PRODUCTS = ["Default", "All"]
ASSET_TYPES = ["Static Asset", "Dynamic Asset", "Character", "Environment"]

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
        self.setupUi_()

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create 2loud custom Asset...")
        self.core.parentWindow(self, parent=self.parentDlg)

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "create.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.buttonBox.buttons()[0].setIcon(icon)

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

        self.layout().setContentsMargins(20, 20, 20, 20)

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
