import sys
import json
import os
import shutil
import datetime
import zipfile
import psutil
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QProgressBar, QSystemTrayIcon, QMenu,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QGroupBox,
                             QGridLayout, QFrame, QAbstractItemView)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QSize, QUrl, QDate
from PyQt6.QtGui import QIcon, QAction, QPixmap, QDesktopServices, QFont, QColor

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configuration.json")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

class ExternalBackupWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, source_path, dest_path, username):
        super().__init__()
        self.source_path = source_path
        self.dest_path = dest_path
        self.username = username
        self.is_running = True

    def run(self):
        try:
            self.status.emit("Calculating size...")
            total_size = 0
            file_list = []
            for dirpath, dirnames, filenames in os.walk(self.source_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        s = os.path.getsize(fp)
                        total_size += s
                        file_list.append((fp, s))
                    except OSError:
                        pass
            
            if total_size == 0:
                total_size = 1 # Avoid division by zero

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = os.path.join(self.dest_path, f"{self.username}_FULL_{timestamp}.zip")
            
            self.status.emit("Zipping and Copying...")
            
            copied_size = 0
            start_time = datetime.datetime.now()
            
            with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add info.json
                info = {
                    "backup_date": str(datetime.datetime.now()),
                    "type": "FULL_EXTERNAL_BACKUP",
                    "user": self.username,
                    "files_count": len(file_list),
                    "source": self.source_path
                }
                zipf.writestr("info.json", json.dumps(info, indent=4))

                for file_path, size in file_list:
                    if not self.is_running: break
                    
                    try:
                        arcname = os.path.relpath(file_path, self.source_path)
                        zipf.write(file_path, arcname)
                        
                        copied_size += size
                        percentage = int((copied_size / total_size) * 100)
                        self.progress.emit(percentage)
                        
                        # Calculate ETC
                        elapsed = (datetime.datetime.now() - start_time).total_seconds()
                        if elapsed > 0 and copied_size > 0:
                            speed = copied_size / elapsed
                            remaining_bytes = total_size - copied_size
                            etc_seconds = remaining_bytes / speed
                            etc_str = str(datetime.timedelta(seconds=int(etc_seconds)))
                            self.status.emit(f"Backing up... {percentage}% (ETC: {etc_str})")
                    except Exception as e:
                        print(f"Error packing file {file_path}: {e}")
            
            if self.is_running:
                self.status.emit("Backup Completed!")
            else:
                self.status.emit("Backup Cancelled.")
                if os.path.exists(archive_name):
                    try:
                        os.remove(archive_name) # Cleanup incomplete file
                    except:
                        pass
            
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
        finally:
            self.finished.emit()

    def stop(self):
        self.is_running = False

class SafeCopyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.snooze_until = None
        self.snooze_levels = [120, 60, 30, 10, 5] 
        self.current_snooze_level_index = 0
        self.last_external_backup_drive = None
        
        self.initUI()
        self.init_timer()
        self.check_paths_status() # Initial check

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            QMessageBox.critical(self, "Error", "configuration.json not found!")
            sys.exit(1)
        
        with open(CONFIG_PATH, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid JSON in configuration.json")
                sys.exit(1)

    def save_config(self):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.config, f, indent=4)

    def initUI(self):
        self.setWindowTitle("SafeCopy Backup Manager")
        self.resize(900, 650)
        self.setStyleSheet("""
/* Base */
QWidget {
    background-color: #121414;          /* soft black */
    font-family: "Segoe UI", sans-serif;
    color: #e6ebe9;                     /* light gray-green text */
}

/* Group Boxes */
QGroupBox {
    background-color: #1a1d1c;          /* dark surface */
    border-radius: 2px;
    border: 1px solid #2b3a34;
    margin-top: 1.6em;
    font-weight: 600;
    padding: 16px;
    qproperty-alignment: AlignLeft;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #6fb89f;                     /* soft green accent */
}

/* Titles & Labels */
QLabel#TitleLabel {
    font-size: 24px;
    font-weight: 700;
    color: #eaf5f1;                     /* near-white */
}

QLabel#UserLabel {
    font-size: 14px;
    color: #9fb7af;                     /* muted green-gray */
}

/* Buttons */
QPushButton {
    background-color: #3f7f68;          /* primary green */
    color: #ffffff;
    border: none;
    padding: 9px 18px;
    border-radius: 2px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #346a58;
}

QPushButton:pressed {
    background-color: #2b5748;
}

QPushButton#SecondaryBtn {
    background-color: #262a28;          /* dark neutral */
    color: #e6ebe9;
}

QPushButton#SecondaryBtn:hover {
    background-color: #323836;
}

/* Tables */
QTableWidget {
    background-color: #1a1d1c;
    border: 1px solid #2b3a34;
    gridline-color: #242c29;
    color: #e6ebe9;
    selection-background-color: #2f5f4f;
    selection-color: #ffffff;
}

/* Progress Bar */
QProgressBar {
    background-color: #262c2a;
    border-radius: 2px;
    text-align: center;
    color: #e6ebe9;
}

QProgressBar::chunk {
    background-color: #4caf8f;          /* soft green */
    border-radius: 2px;
}

        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- Header Section ---
        header_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        self.title_label = QLabel("LOUD2 PROJECT - BACKUP MANAGER")
        self.title_label.setObjectName("TitleLabel")
        
        self.user_label = QLabel(f"Current User: {self.config.get('current_username', 'Unknown')}")
        self.user_label.setObjectName("UserLabel")
        
        title_container.addWidget(self.title_label)
        title_container.addWidget(self.user_label)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        # Logo/Icon placeholder or branding could go right 
        
        main_layout.addLayout(header_layout)

        # --- Status Dashboard ---
        status_group = QGroupBox("System Status")
        status_layout = QHBoxLayout()
        
        # Source Path Status
        self.source_status_icon = QLabel()
        self.source_status_icon.setFixedSize(48, 48)
        self.source_status_label = QLabel("Source: Checking...")
        
        # Destination Path Status
        self.dest_status_icon = QLabel()
        self.dest_status_icon.setFixedSize(48, 48)
        self.dest_status_label = QLabel("Backup Dest: Checking...")
        
        # Disk Detection Status
        self.disk_status_icon = QLabel()
        self.disk_status_icon.setFixedSize(48, 48)
        self.disk_status_label = QLabel("Ext. Drive: Scanning...")
        
        status_layout.addWidget(self.source_status_icon)
        status_layout.addWidget(self.source_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.dest_status_icon)
        status_layout.addWidget(self.dest_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.disk_status_icon)
        status_layout.addWidget(self.disk_status_label)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # --- Middle Section (Backups & Planning) ---
        middle_layout = QHBoxLayout()

        # Left: Backups List
        backups_group = QGroupBox("Existing Backups")
        backups_layout = QVBoxLayout()
        
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(3)
        self.backups_table.setHorizontalHeaderLabels(["Name", "Date Modified", "Size"])
        self.backups_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backups_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.backups_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        button_row = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh List")
        self.btn_refresh.setObjectName("SecondaryBtn")
        self.btn_refresh.clicked.connect(self.refresh_backups_list)
        
        self.btn_open_folder = QPushButton("Open Backup Folder")
        self.btn_open_folder.clicked.connect(self.open_backup_folder)
        
        button_row.addWidget(self.btn_refresh)
        button_row.addWidget(self.btn_open_folder)
        
        backups_layout.addWidget(self.backups_table)
        backups_layout.addLayout(button_row)
        backups_group.setLayout(backups_layout)
        
        # Right: Planning & Info
        right_panel = QVBoxLayout()
        
        # Backup Plan
        plan_group = QGroupBox("Backup Plan")
        plan_layout = QGridLayout()
        
        plan_layout.addWidget(QLabel("Scheduled Day:"), 0, 0)
        
        self.day_combo = QComboBox()
        self.day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.load_current_schedule()
        plan_layout.addWidget(self.day_combo, 0, 1)
        
        self.btn_save_plan = QPushButton("Update Schedule")
        self.btn_save_plan.clicked.connect(self.save_schedule)
        plan_layout.addWidget(self.btn_save_plan, 1, 0, 1, 2)
        
        plan_group.setLayout(plan_layout)
        
        right_panel.addWidget(plan_group)
        right_panel.addStretch()
        
        middle_layout.addWidget(backups_group, stretch=2)
        middle_layout.addLayout(right_panel, stretch=1)
        
        main_layout.addLayout(middle_layout)

        # --- Footer Actions ---
        footer_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        
        self.status_bar_label = QLabel("Ready")
        
        self.btn_backup_now = QPushButton("Run Incremental Backup Now")
        self.btn_backup_now.clicked.connect(lambda: self.check_regular_backup(force=True))
        
        footer_layout.addWidget(self.status_bar_label)
        footer_layout.addWidget(self.progress_bar)
        footer_layout.addWidget(self.btn_backup_now)
        
        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

        # Load resources
        self.refresh_backups_list()

    def set_icon(self, label, name):
        pixmap = QPixmap(os.path.join(ASSETS_DIR, name))
        if not pixmap.isNull():
            scaled = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(scaled)
        else:
            label.setText(name) # Fallback

    def check_paths_status(self):
        # Source
        src = self.config.get("handle_path", "")
        if os.path.exists(src):
            self.set_icon(self.source_status_icon, "path_found.png")
            self.source_status_label.setText(f"Source Found\n{src}")
            self.source_status_label.setStyleSheet("color: green;")
        else:
            self.set_icon(self.source_status_icon, "path_missing.png")
            self.source_status_label.setText(f"Source Missing!\n{src}")
            self.source_status_label.setStyleSheet("color: red;")

        # Dest
        dst = self.config.get("temp_save_path", "")
        if not os.path.exists(dst):
            try:
                os.makedirs(dst)
            except:
                pass
        
        if os.path.exists(dst):
            self.set_icon(self.dest_status_icon, "path_found.png")
            self.dest_status_label.setText(f"Backup Dir Found\n{dst}")
            self.dest_status_label.setStyleSheet("color: green;")
        else:
            self.set_icon(self.dest_status_icon, "path_missing.png")
            self.dest_status_label.setText(f"Backup Dir Error!\n{dst}")
            self.dest_status_label.setStyleSheet("color: red;")
            
        # Drive (initially scanning)
        self.set_icon(self.disk_status_icon, "disk_scanning.png")

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_tasks)
        self.timer.start(5000) # Check every 5 seconds for responsiveness
        
        # Initial check
        QTimer.singleShot(1000, self.check_tasks)

    def check_tasks(self):
        self.check_regular_backup()
        self.check_weekly_popup()
        self.detect_external_drives()

    def refresh_backups_list(self):
        self.backups_table.setRowCount(0)
        path = self.config.get("temp_save_path")
        if not os.path.exists(path):
            return

        try:
            files = []
            for f in os.listdir(path):
                if f.endswith('.zip'):
                    full_path = os.path.join(path, f)
                    stats = os.stat(full_path)
                    files.append({
                        "name": f,
                        "time": stats.st_mtime,
                        "size": stats.st_size
                    })
            
            # Sort by time desc
            files.sort(key=lambda x: x['time'], reverse=True)
            
            self.backups_table.setRowCount(len(files))
            for i, f in enumerate(files):
                self.backups_table.setItem(i, 0, QTableWidgetItem(f['name']))
                
                dt = datetime.datetime.fromtimestamp(f['time'])
                self.backups_table.setItem(i, 1, QTableWidgetItem(dt.strftime("%Y-%m-%d %H:%M")))
                
                size_mb = f['size'] / (1024 * 1024)
                self.backups_table.setItem(i, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
        except Exception as e:
            print(f"Error listing backups: {e}")

    def open_backup_folder(self):
        path = self.config.get("temp_save_path")
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Error", f"Path does not exist:\n{path}")

    def load_current_schedule(self):
        user = self.config.get("current_username")
        schedules = self.config.get("user_schedules", {})
        day_idx = schedules.get(user, 1) # Default Monday (1)
        # Combo is 0-indexed (0=Mon, 6=Sun), day_idx is 1=Mon, 7=Sun
        combo_idx = day_idx - 1
        if 0 <= combo_idx < 7:
            self.day_combo.setCurrentIndex(combo_idx)

    def save_schedule(self):
        user = self.config.get("current_username")
        # Combo index: 0=Mon -> day_idx=1
        new_day_idx = self.day_combo.currentIndex() + 1
        
        self.config.setdefault("user_schedules", {})[user] = new_day_idx
        self.save_config()
        QMessageBox.information(self, "Success", f"Backup schedule for {user} updated to {self.day_combo.currentText()}.")
        self.log_audit("Schedule Update", "Success", f"Changed to {self.day_combo.currentText()}")

    def log_audit(self, action, status, details=""):
        try:
            log_path = self.config.get("audit_log_path", "audit.dat")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = self.config.get("current_username", "Unknown")
            message = f"[{timestamp}] User: {user} | Action: {action} | Status: {status} | Details: {details}\n"
            
            with open(log_path, "a") as f:
                f.write(message)
        except Exception as e:
            print(f"Logging failed: {e}")

    def check_regular_backup(self, force=False):
        # Implementation for 2-day incremental backup logic
        try:
            temp_path = self.config.get("temp_save_path")
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)

            state_file = os.path.join(temp_path, "backup_state.json")
            last_backup_time = 0
            
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    last_backup_time = state.get("last_backup_timestamp", 0)

            # Check if 2 days (48 hours) have passed
            if force or (datetime.datetime.now().timestamp() - last_backup_time) >= (48 * 3600):
                self.status_bar_label.setText("Performing Incremental Backup...")
                self.log_audit("Check Regular Backup", "Triggered", "Manual or 48h threshold triggered")
                self.perform_incremental_backup(temp_path, state_file)
                self.cleanup_old_backups(temp_path)
                self.status_bar_label.setText("Idle")
                self.refresh_backups_list()
            
        except Exception as e:
            self.status_bar_label.setText(f"Error: {e}")
            self.log_audit("Check Regular Backup", "Error", str(e))

    def perform_incremental_backup(self, temp_path, state_file):
        try:
            source_path = self.config.get("handle_path")
            current_timestamp = datetime.datetime.now().timestamp()
            
            last_backup = 0
            if os.path.exists(state_file):
                try:
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                    last_backup = state.get("last_backup_timestamp", 0)
                except:
                    pass
            
            files_to_backup = []
            for dirpath, _, filenames in os.walk(source_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.getmtime(fp) > last_backup:
                        files_to_backup.append(fp)
            
            if not files_to_backup:
                self.update_backup_state(state_file, current_timestamp)
                self.log_audit("Incremental Backup", "Skipped", "No modified files found")
                QMessageBox.information(self, "Backup", "No files modified since last backup.")
                return

            zip_name = f"{self.config.get('current_username')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join(temp_path, zip_name)
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(files_to_backup))
            self.progress_bar.setValue(0)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, file_path in enumerate(files_to_backup):
                    arcname = os.path.relpath(file_path, source_path)
                    zf.write(file_path, arcname)
                    self.progress_bar.setValue(i + 1)
                    QApplication.processEvents()
                
                # Add info.json inside zip
                info = {
                    "backup_date": str(datetime.datetime.now()),
                    "user": self.config.get("current_username"),
                    "files_count": len(files_to_backup),
                    "source": source_path
                }
                zf.writestr("info.json", json.dumps(info, indent=4))

            self.update_backup_state(state_file, current_timestamp)
            self.log_audit("Incremental Backup", "Success", f"Created {zip_name} with {len(files_to_backup)} files")
            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "Backup", f"Backup Successful!\nCreated {zip_name}")

        except Exception as e:
            print(f"Backup failed: {e}")
            self.log_audit("Incremental Backup", "Failed", str(e))
            QMessageBox.critical(self, "Error", f"Backup failed: {e}")
            self.progress_bar.setVisible(False)

    def update_backup_state(self, state_file, timestamp):
        with open(state_file, 'w') as f:
            json.dump({"last_backup_timestamp": timestamp}, f)

    def cleanup_old_backups(self, temp_path):
        max_backups = self.config.get("max_backups", 10)
        files = [os.path.join(temp_path, f) for f in os.listdir(temp_path) if f.endswith('.zip') and not f.startswith("FULL_BACKUP")]
        files.sort(key=os.path.getmtime)
        
        deleted_count = 0
        while len(files) > max_backups:
            f_to_del = files[0]
            try:
                os.remove(f_to_del)
                files.pop(0)
                deleted_count += 1
            except:
                pass
            
        if deleted_count > 0:
            self.log_audit("Cleanup", "Success", f"Deleted {deleted_count} old backups (Limit: {max_backups})")

    def check_weekly_popup(self):
        if not self.config.get("weekly_save_enabled", False):
            return
            
        current_user = self.config.get("current_username")
        user_schedules = self.config.get("user_schedules", {})
        
        # Get scheduled day for current user (1=Mon, 7=Sun)
        scheduled_day = user_schedules.get(current_user)
        if not scheduled_day:
            return

        now = datetime.datetime.now()
        if now.isoweekday() == scheduled_day:
            # Check if snoozed
            if self.snooze_until and now < self.snooze_until:
                return
            
            if hasattr(self, 'weekly_action_taken') and self.weekly_action_taken == now.date():
                return
            
            # Use QTimer to show unique popup so it doesn't block main thread indefinitely in loop
            # But here we are in a timer event anyway.
            self.show_weekly_popup(scheduled_day)

    def show_weekly_popup(self, day_int):
        # Prevent multiple popups
        if hasattr(self, '_popup_active') and self._popup_active:
            return
        self._popup_active = True
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Weekly Backup Rule")
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = day_names[day_int - 1] if 1 <= day_int <= 7 else "Day " + str(day_int)
        
        msg.setText(f"It is {day_name}. Regular Backup Protocol.")
        
        backup_btn = msg.addButton("Backup Now", QMessageBox.ButtonRole.AcceptRole)
        snooze_btn = msg.addButton("Snooze", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        self._popup_active = False
        
        if msg.clickedButton() == backup_btn:
            self.status_bar_label.setText("Performing Weekly Backup...")
            QApplication.processEvents()
            self.perform_incremental_backup(self.config.get("temp_save_path"), os.path.join(self.config.get("temp_save_path"), "backup_state.json"))
            self.snooze_until = None
            self.current_snooze_level_index = 0
            self.weekly_action_taken = datetime.date.today()
            self.status_bar_label.setText("Idle")
        elif msg.clickedButton() == snooze_btn:
            minutes = self.snooze_levels[self.current_snooze_level_index]
            self.snooze_until = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            if self.current_snooze_level_index < len(self.snooze_levels) - 1:
                self.current_snooze_level_index += 1
            self.log_audit("Weekly Prompt", "Snoozed", f"Snoozed for {minutes} min")
        else:
            self.snooze_until = datetime.datetime.now() + datetime.timedelta(minutes=60)
            self.log_audit("Weekly Prompt", "Cancelled", "User cancelled")

    def detect_external_drives(self):
        drives = []
        try:
            for partition in psutil.disk_partitions():
                if 'removable' in partition.opts:
                    drives.append(partition.mountpoint)
        except:
            pass
        
        if drives:
            drive_letter = drives[0]
            self.disk_status_label.setText(f"Drive Detected:\n{drive_letter}")
            self.disk_status_label.setStyleSheet("color: green;")
            self.set_icon(self.disk_status_icon, "disk_detected.png")
            
            if not hasattr(self, 'last_external_backup_drive') or self.last_external_backup_drive != drive_letter:
                # Ask user
                reply = QMessageBox.question(self, 'External Drive Detected', 
                                            f"Drive {drive_letter} detected. Perform FULL Backup to it?",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                            QMessageBox.StandardButton.No)

                if reply == QMessageBox.StandardButton.Yes:
                    self.start_external_backup(drive_letter)
                
                self.last_external_backup_drive = drive_letter
        else:
            self.disk_status_label.setText("No Ext. Drive")
            self.disk_status_label.setStyleSheet("color: gray;")
            self.set_icon(self.disk_status_icon, "disk_scanning.png")
            self.last_external_backup_drive = None

    def start_external_backup(self, drive_letter):
        self.progress_bar.setVisible(True)
        self.status_bar_label.setText(f"Backing up to {drive_letter}...")
        
        self.worker = ExternalBackupWorker(self.config.get("handle_path"), drive_letter, self.config.get("current_username"))
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.backup_finished)
        self.worker.start()

    def update_progress(self, val):
        self.progress_bar.setValue(val)
        
    def update_status(self, text):
        self.status_bar_label.setText(text)

    def backup_finished(self):
        self.progress_bar.setVisible(False)
        self.status_bar_label.setText("External Backup Finished")
        QMessageBox.information(self, "Backup", "External Backup Completed Successfully")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SafeCopyApp()
    ex.show()
    sys.exit(app.exec())
