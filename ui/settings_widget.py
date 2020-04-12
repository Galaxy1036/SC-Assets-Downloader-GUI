import os

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QWidget, QLabel, QSpinBox,
                             QLineEdit, QHBoxLayout, QVBoxLayout,
                             QPushButton, QFileDialog)


class SettingsWidget(QWidget):
    def __init__(self, parent, config):
        super().__init__()

        self.parent = parent
        self.config = config

        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()

        self.browse_folder_widget = QWidget()
        self.browse_folder_layout = QHBoxLayout()

        self.folder_path_input = QLineEdit()
        self.folder_path_input.setEnabled(False)

        if os.path.isabs(self.config['output_path']):
            self.folder_path_input.setText(self.config['output_path'])

        else:
            self.folder_path_input.setText(os.path.abspath(self.config['output_path']))

        self.browse_folder_button = QPushButton('', self)
        self.browse_folder_button.setIcon(QIcon('ui/assets/browse.png'))
        self.browse_folder_button.setIconSize(QSize(17, 17))
        self.browse_folder_button.clicked.connect(self.browse_folder)

        self.browse_folder_layout.addWidget(self.folder_path_input)
        self.browse_folder_layout.addWidget(self.browse_folder_button)

        self.browse_folder_widget.setLayout(self.browse_folder_layout)

        self.workers_spinbox = QSpinBox()

        self.workers_spinbox.setRange(1, 10)
        self.workers_spinbox.setValue(max(min(self.config['workers_count'], 10), 1))

        self.save_settings_button = QPushButton('Save settings', self)
        self.save_settings_button.setIcon(QIcon('ui/assets/save.png'))
        self.save_settings_button.setIconSize(QSize(17, 17))
        self.save_settings_button.clicked.connect(self.save_settings)

        self.main_layout.addWidget(QLabel('Output folder:'))
        self.main_layout.addWidget(self.browse_folder_widget)
        self.main_layout.addWidget(QLabel('Workers count (up to 10):'))
        self.main_layout.addWidget(self.workers_spinbox)
        self.main_layout.addWidget(self.save_settings_button)

        self.setLayout(self.main_layout)

    def browse_folder(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select an output directory')
        self.config['output_path'] = directory
        self.folder_path_input.setText(directory)

    def save_settings(self):
        self.config['workers_count'] = self.workers_spinbox.value()

        self.parent.save_config()
