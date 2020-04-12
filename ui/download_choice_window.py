from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QWidget, QLabel, QCheckBox,
                             QComboBox, QGridLayout, QMainWindow,
                             QPushButton, QVBoxLayout)


class DownloadChoiceWindow(QMainWindow):

    def __init__(self, parent, files_types):
        super().__init__(parent)
        self.files_types = files_types
        self.files_types_widget = []

        self.download_started = False

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()

        self.download_combo_box = QComboBox()
        self.download_combo_box.addItems(['Every files', 'Only specific files'])
        self.download_combo_box.currentIndexChanged.connect(self.on_combo_box_change)

        self.files_types_widget = QWidget()
        self.files_types_layout = QGridLayout()

        for index, file_type in enumerate(self.files_types):
            self.files_types_layout.addWidget(QCheckBox(file_type), index // 3, index % 3)

        self.files_types_widget.setLayout(self.files_types_layout)
        self.files_types_widget.hide()

        self.start_button = QPushButton('Start Download', self)
        self.start_button.setIcon(QIcon('ui/assets/start.png'))
        self.start_button.setIconSize(QSize(17, 17))

        self.start_button.clicked.connect(self.start_download)

        self.central_layout.addWidget(QLabel('Download:'))
        self.central_layout.addWidget(self.download_combo_box)
        self.central_layout.addWidget(self.files_types_widget)
        self.central_layout.addWidget(self.start_button)

        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

    def on_combo_box_change(self, _):
        choice = self.download_combo_box.currentText()

        if choice == 'Every files':
            self.files_types_widget.hide()

        else:
            self.files_types_widget.show()

    def start_download(self):
        self.download_started = True

        self.parent().stop_button.setEnabled(True)
        self.parent().start_button.setEnabled(False)
        self.close()

        choice = self.download_combo_box.currentText()

        wanted_extensions = []

        if choice == 'Every files':
            wanted_extensions = self.files_types

        else:
            for index in range(self.files_types_layout.count()):
                widget = self.files_types_layout.itemAt(index).widget()

                if widget.isChecked():
                    wanted_extensions.append(widget.text())

        self.parent().start_download(tuple(wanted_extensions))

    def closeEvent(self, _):
        if not self.download_started:
            self.parent().start_button.setEnabled(True)
            self.parent().download_method_combo_box.setEnabled(True)
