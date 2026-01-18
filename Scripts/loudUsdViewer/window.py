import sys

sys.path.append(r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Plugins\Custom\laud2\Scripts\loudUsdViewer")
sys.path.append("C:\Program Files\Prism2\PythonLibs\Python3\PySide")
sys.path.append(r"C:\Program Files\Nuke15.2v6")

from tviewer import TViewer
from setScene import getUsdScene
from PySide6 import QtWidgets, QtCore

app = QtWidgets.QApplication(sys.argv)
viewer = TViewer(stage=getUsdScene())
viewer.resize(QtCore.QSize(700, 950))
viewer.show()
viewer.view.updateView(resetCam=False, forceComputeBBox=True)
sys.exit(app.exec())