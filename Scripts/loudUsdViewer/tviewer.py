"""
TViewer: PyQt6/PySide6-based Hydra USD viewer.
Adds playback controls and frame display.
"""

import sys

sys.path.append(r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Plugins\Custom\laud2\Scripts\loudUsdViewer")
sys.path.append("C:\Program Files\Prism2\PythonLibs\Python3\PySide")
sys.path.append(r"C:\Program Files\Side Effects Software\Houdini 21.0.440\bin")

from usdt import Usd, UsdUtils, UsdGeom, UsdAppUtils, UsdLux
from usdt import StageView

import os
import sys
from PySide6 import QtWidgets, QtCore


from timeline import TimelineWidget
#from configuration.confwin import ConfigSubWindow
#from configuration import configuration as config



# Define the main widget and application
class TViewer(QtWidgets.QMainWindow):
    movementConnection = QtCore.Signal(dict)
    llmConnection = QtCore.Signal(dict)

    def __init__(self, stage=None, camera=None):
        super(TViewer, self).__init__()
        self.model = StageView.DefaultDataModel()
        self.view = StageView(dataModel=self.model)

        ############ SET CAMERA
        #self.setCamera(stage, config.usd_camera_path)

        self.timeline = TimelineWidget()

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QtWidgets.QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        # Make the StageView expand to fill all available space,
        # keep the timeline at its preferred (fixed) height.
        self.view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.timeline.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.main_layout.addWidget(self.view, stretch=1)
        self.main_layout.addWidget(self.timeline, stretch=0)

        # Ensure stretch factors so the view gets all extra space.
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 0)
        
        self.timeline.frameChanged.connect(self.on_frame_changed)
        self.timeline.playbackStarted.connect(self.on_playback_started)
        self.timeline.playbackStopped.connect(self.on_playback_stopped)

        self.set_bottom_div()
        self.config_win = None

        menu_bar = QtWidgets.QMenuBar(self)
        self._set_window_menu(menu_bar)
        self.layout().setMenuBar(menu_bar)

        self.logo_widget = None
        self.logo_visible = None

        if stage:
            self.setStage(stage)


    def setCamera(self, stage, cameraPath):
        print("Setting camera:", cameraPath)

        camera_prim = stage.GetPrimAtPath(cameraPath)
        if not camera_prim or not camera_prim.IsValid():
            raise RuntimeError(f"Camera not found or invalid: {cameraPath}")

        # --- STEP 0: make sure model knows the stage ---
        self.model.stage = stage  # <-- this fixes the NoneType error

        # --- STEP 1: assign USD camera path to StageView ---
        self.model.viewSettings.cameraPrimPath = camera_prim.GetPath()

        # --- STEP 2: update view ---
        self.view.updateView(resetCam=False, forceComputeBBox=True)

        # --- STEP 3: optional fit to stage ---
        try:
            self.view.fitToStage()
        except Exception as e:
            print("Warning: fitToStage failed:", e)

        # --- STEP 4: optional UI lock ---
        self.view.setMouseTracking(False)
        self.view.setFocusPolicy(QtCore.Qt.NoFocus)
        self.view.setEnabled(False)

        # --- STEP 5: keep camera reference ---
        self.camera = camera_prim

        print("Camera successfully applied:", cameraPath)

    def set_bottom_div(self):
        """Create a bottom input bar with an entry and send button."""
        bottom_widget = QtWidgets.QWidget()
        bottom_widget.setMaximumHeight(30)
        bottom_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        bottom_layout = QtWidgets.QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        bottom_layout.setSpacing(6)

        # Entry box
        self.entry = QtWidgets.QLineEdit()
        self.entry.setPlaceholderText("Type something and press Enter...")
        self.entry.returnPressed.connect(self.send_input)
        self.entry.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.entry.setMaximumHeight(24)

        # Send button
        send_button = QtWidgets.QPushButton("Send")
        send_button.clicked.connect(self.send_input)
        send_button.setStyleSheet(
                "background-color: #222; color: #eee; padding: 6px; border-radius: 6px;"
            )
        send_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        send_button.setMaximumHeight(24)

        # Add to layout
        bottom_layout.addWidget(self.entry)
        bottom_layout.addWidget(send_button)

        # Keep bar at bottom
        self.main_layout.addStretch()
        self.main_layout.addWidget(bottom_widget)

    def send_input(self):
        """Emit the text input as a string."""
        text = self.entry.text().strip()
        if text:
            self.llmConnection.emit({"input": text})
            self.entry.clear()

    def setStage(self, stage):
        self.model.stage = stage
        earliest = Usd.TimeCode.EarliestTime()
        self.model.currentFrame = Usd.TimeCode(earliest)

        frames = 42

        if stage.HasAuthoredTimeCodeRange():
            self.timeline.setVisible(True)
            self.timeline.setStartFrame(stage.GetStartTimeCode())
            self.timeline.setEndFrame(frames)#stage.GetEndTimeCode())
            self.timeline.framesPerSecond = stage.GetFramesPerSecond()
        else:
            self.timeline.setStartFrame(stage.GetStartTimeCode() + 1)
            self.timeline.setEndFrame(frames + 1)
            self.timeline.setVisible(False)

    def closeEvent(self, event):
        self.timeline.playing = False
        self.view.closeRenderer()

    def on_frame_changed(self, value, playback):
        self.model.currentFrame = Usd.TimeCode(value)

        # Update the label text with the current frame value
        try:
            frame_val = int(self.model.currentFrame.GetValue())
        except Exception:
            frame_val = self.model.currentFrame.GetValue()

        self.setWindowTitle(f"Frame: {frame_val}")

        if int(self.model.currentFrame.GetValue()) == 1: #% (196*2) 
            print("Frame divisble between 50. Lounching animation")
            print("------------------------------------------------------------------------------------------------ ANIMATION DIVIDING")
            self.movementConnection.emit({"frame": int(self.model.currentFrame.GetValue())})

        if playback:
            self.view.updateForPlayback()
        else:
            self.view.updateView()

    def _set_window_menu(self, menu_bar: QtWidgets.QMenuBar):
        control_menu = menu_bar.addMenu("Controls")

        # Play
        play_action = control_menu.addAction("Play")
        play_action.triggered.connect(lambda: self.timeline.toggle_play())
        control_menu.addAction(play_action)

        def reloadCamera():
            print("reloading camera")
            self.view.updateView(resetCam=False, forceComputeBBox=True)

        # Recenter
        recenter_action = control_menu.addAction("Recenter View")
        recenter_action.triggered.connect(reloadCamera)
        control_menu.addAction(recenter_action)

        window_menu = menu_bar.addMenu("Window")
        config_action = window_menu.addAction("Configuration")
        config_action.triggered.connect(lambda: print("NO"))



    def on_playback_stopped(self):
        self.model.playing = False
        self.view.updateView()

    def on_playback_started(self):
        self.model.playing = True
        self.view.updateForPlayback()

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Space:
            self.timeline.toggle_play()
        elif key == QtCore.Qt.Key_F:
            self.view.updateView(resetCam=False, forceComputeBBox=True)

    def _show_logo(self):
        # If logo widget doesn't exist, create it
        if not self.logo_widget:
            """self.logo_widget = QtWidgets.QLabel(
                "2LOUD"
            )
            self.logo_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)"""
            # Title
            self.logo_widget = QtWidgets.QLabel(
                """
                <h1 style="font-size: 58px; height: 58px; font-weight: bold; margin-bottom: 0; text-align: center; min-width: 100%;">THE BOX</h1>
                <h3 style="font-size: 14px; margin-top: 4px;">Local Dynamic Interactive Virtual Character.</h3>
                <p style="font-size: 11px; margin-top: 10px;">by Daniel Casadevall Jauhiainen. version v.1.0</p>
                <br> <br>
                <p style="font-size: 11px; margin-top: 10px;">Loading models, wait for initialization to complete...</p>
                """
            )
            self.logo_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.logo_widget)
        self.logo_visible = True

    def _hide_logo(self):
        # Replace logo with an empty widget or main content
        placeholder = QtWidgets.QWidget()
        self.setCentralWidget(placeholder)
        self.logo_visible = False

    def toggle_logo(self):
        if self.logo_visible:
            self._hide_logo()
        else:
            self._show_logo()