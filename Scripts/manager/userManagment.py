import json
import os

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QLineEdit, QSpinBox, QComboBox, QMessageBox
)

# -------------------------------------------------------------------
# USER LOGIC (UNCHANGED – YOUR CODE)
# -------------------------------------------------------------------

file_path = r"users.json"


class User:
    def __init__(self):
        self.id = None
        self.name = None
        self.username = None
        self.abreviation = None
        self.role = "Artist"
        self.power = 1
        self.discordID = None
        self.knownNames = None

    def _load_users(self):
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r") as f:
            return json.load(f)

    def _save_users(self, users):
        with open(file_path, "w") as f:
            json.dump(users, f, indent=4)

    def setUser(self, id):
        users = self._load_users()
        for user in users:
            if user["id"] == id:
                self.__dict__.update(user)
                return True
        return False

    def saveUser(self):
        users = self._load_users()
        for i, user in enumerate(users):
            if user["id"] == self.id:
                users[i] = self.__dict__
                self._save_users(users)
                return True
        return False

    def addUser(self):
        users = self._load_users()

        if any(u["id"] == self.id for u in users):
            return False

        users.append(self.__dict__)
        self._save_users(users)
        return True


# -------------------------------------------------------------------
# USER MANAGEMENT GUI
# -------------------------------------------------------------------

class UserManagementWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("User Management")
        self.current_user = None

        self._build_ui()
        self._load_user_list()

    # ------------------------------------------------------------
    # UI
    # ------------------------------------------------------------
    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # ---------------- LEFT : USER LIST ----------------
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Users"))

        self.user_list = QListWidget()
        self.user_list.currentItemChanged.connect(self._on_user_selected)
        left_layout.addWidget(self.user_list)

        btn_new = QPushButton("New User")
        btn_new.clicked.connect(self._new_user)
        left_layout.addWidget(btn_new)

        main_layout.addLayout(left_layout, 1)

        # ---------------- RIGHT : USER EDIT ----------------
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("User Details"))

        self.e_id = QSpinBox()
        self.e_id.setMaximum(999999)
        right_layout.addLayout(self._row("ID", self.e_id))

        self.e_name = QLineEdit()
        right_layout.addLayout(self._row("Name", self.e_name))

        self.e_username = QLineEdit()
        right_layout.addLayout(self._row("Username", self.e_username))

        self.e_abrev = QLineEdit()
        right_layout.addLayout(self._row("Abbreviation", self.e_abrev))

        self.cb_role = QComboBox()
        self.cb_role.addItems(["Colabo", "Artist", "Lead", "Supervisor", "Admin"])
        right_layout.addLayout(self._row("Role", self.cb_role))

        self.sb_power = QSpinBox()
        self.sb_power.setRange(1, 10)
        right_layout.addLayout(self._row("Power", self.sb_power))

        self.e_discordid = QLineEdit()
        right_layout.addLayout(self._row("Discord ID", self.e_discordid))

        self.e_knownNames = QLineEdit()
        right_layout.addLayout(self._row("Known PC names", self.e_knownNames))

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self._save_user)
        btn_layout.addWidget(btn_save)

        right_layout.addLayout(btn_layout)
        right_layout.addStretch()

        main_layout.addLayout(right_layout, 2)

    def _row(self, label, widget):
        lo = QHBoxLayout()
        lo.addWidget(QLabel(label))
        lo.addWidget(widget)
        return lo

    # ------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------
    def _load_user_list(self):
        self.user_list.clear()
        if not os.path.exists(file_path):
            return

        with open(file_path, "r") as f:
            users = json.load(f)

        for u in users:
            self.user_list.addItem(f'{u["id"]} - {u["name"]}')

    def _on_user_selected(self, item):
        if not item:
            return

        user_id = int(item.text().split(" - ")[0])
        self.current_user = User()
        self.current_user.setUser(user_id)

        self._populate_fields()

    def _populate_fields(self):
        u = self.current_user
        self.e_id.setValue(u.id)
        self.e_name.setText(u.name)
        self.e_username.setText(u.username)
        self.e_abrev.setText(u.abreviation)
        self.cb_role.setCurrentText(u.role)
        self.sb_power.setValue(u.power)
        self.e_discordid.setText(u.discordID)
        self.e_knownNames.setText(u.knownNames)

    def _new_user(self):
        self.current_user = User()
        self.e_id.setValue(0)
        self.e_name.clear()
        self.e_username.clear()
        self.e_abrev.clear()
        self.cb_role.setCurrentText("Artist")
        self.sb_power.setValue(1)
        self.e_discordid.clear()

    def _save_user(self):
        if not self.current_user:
            return

        self.current_user.id = self.e_id.value()
        self.current_user.name = self.e_name.text()
        self.current_user.username = self.e_username.text()
        self.current_user.abreviation = self.e_abrev.text()
        self.current_user.role = self.cb_role.currentText()
        self.current_user.power = self.sb_power.value()
        self.current_user.discordID = self.e_discordid.text()
        self.current_user.knownNames = self.e_knownNames.Text().split(", ") if self.e_knownNames.Text() else []

        # Decide add vs update
        if not self.current_user.saveUser():
            if not self.current_user.addUser():
                QMessageBox.warning(self, "Error", "User ID already exists")
                return

        self._load_user_list()
        QMessageBox.information(self, "Saved", "User saved successfully")
