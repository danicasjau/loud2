import sys
from qtpy.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
    QHBoxLayout, QPushButton, QStyle
)
from qtpy.QtWebEngineWidgets import QWebEngineView
from qtpy.QtCore import QUrl, Qt

# Configurable Websites
WEBSITES = [
    "https://discord.com/login",   # 0: dis
    "https://docs.google.com/spreadsheets/d/1mmQ5FJe0TMNH4_iFkOTGpe9UWQlQC96e_YLwIOs6EtI/edit?gid=1020148285#gid=1020148285",     # 1: exc
    "https://www.2loudstudio.com/",    # 2: other
    "https://www.canva.com/design/DAG0_aemKmM/bG1WwHe7W23bfQRH3qe_-Q/edit" # 3: can
]

class WebViewer(QMainWindow):
    def __init__(self, windowType="dis", parent=None):
        super(WebViewer, self).__init__(parent)
        self.windowType = windowType
        self.initUI()
        self.load_url()

    def initUI(self):
        self.setWindowTitle("2Loud Prism Source Viewer")
        self.resize(800, 600)
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main Layout
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # --- CUSTOM TOP BAR ---
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(30)
        self.top_bar.setMinimumHeight(30)
        self.top_bar.setMaximumHeight(30)
        self.top_bar.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Back Button
        self.btn_back = QPushButton()
        self.btn_back.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.btn_back.clicked.connect(self.on_back)
        self.top_bar_layout.addWidget(self.btn_back)
        
        # Forward Button
        self.btn_fwd = QPushButton()
        self.btn_fwd.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.btn_fwd.clicked.connect(self.on_forward)
        self.top_bar_layout.addWidget(self.btn_fwd)
        
        # Title Label: 2LOUD - [windowType]
        self.lbl_title = QLabel(f"2LOUD - {self.windowType}")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-left: 10px;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.top_bar_layout.addWidget(self.lbl_title)
        
        # Stretch to push buttons left and potentially title center/left
        self.top_bar_layout.addStretch()
        
        self.layout.addWidget(self.top_bar)

        # --- WEB VIEW ---
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

    def load_url(self):
        """Loads URL based on windowType"""
        url_str = ""
        
        if self.windowType == "dis":
            url_str = WEBSITES[0]
        elif self.windowType == "exc":
            url_str = WEBSITES[1]
        elif self.windowType == "can":
            url_str = WEBSITES[3]
        else:
            url_str = WEBSITES[2] 
            
        print(f"Navigating to: {url_str}")
        self.browser.setUrl(QUrl(url_str))
        
    def on_back(self):
        self.browser.back()
        
    def on_forward(self):
        self.browser.forward()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebViewer(windowType="dis") 
    window.show()
    sys.exit(app.exec())
