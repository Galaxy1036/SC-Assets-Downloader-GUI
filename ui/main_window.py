import json

from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QWidget, QLabel, QToolBar, QVBoxLayout,
                             QMainWindow, QStackedWidget, QToolButton)

from ui.download_widget import DownloadWidget
from ui.settings_widget import SettingsWidget


class MainWindow(QMainWindow):

    def __init__(self, app, config):
        super().__init__()

        self.app = app
        self.config = config
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()

        self.central_widget.setLayout(self.central_layout)

        self.setCentralWidget(self.central_widget)

        self.init_toolbar()
        self.init_status_bar()

        self.main_widget = QStackedWidget()
        self.central_layout.addWidget(self.main_widget)

        self.download_widget = DownloadWidget(self, self.config)
        self.settings_widget = SettingsWidget(self, self.config)

        self.main_widget.addWidget(self.download_widget)
        self.main_widget.addWidget(self.settings_widget)

        self.main_widget.setCurrentWidget(self.download_widget)

        self.setWindowTitle('SC-Downloader-GUI (alpha build v0.1)')

    def init_toolbar(self):
        self.main_toolbar = QToolBar()

        self.central_layout.addWidget(self.main_toolbar)

        main_button = QToolButton()
        main_button.setText("Download")
        main_button.clicked.connect(self.open_main)

        self.main_toolbar.addWidget(main_button)

        settings_button = QToolButton()
        settings_button.setText("Settings")
        settings_button.clicked.connect(self.open_settings)

        self.main_toolbar.addWidget(settings_button)

    def init_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet('QStatusBar::item {border: None;}')

        self.loading_movie = QLabel()
        self.loading_movie_video = QMovie('ui/assets/loading.gif')
        self.loading_movie_video.setScaledSize(QSize(17, 17))

        self.loading_movie.setMovie(self.loading_movie_video)
        self.loading_movie.hide()

        self.status_bar_label = QLabel()

        self.status_bar.addWidget(self.loading_movie)
        self.status_bar.addWidget(self.status_bar_label)

    def open_main(self):
        self.main_widget.setCurrentWidget(self.download_widget)

    def open_settings(self):
        self.main_widget.setCurrentWidget(self.settings_widget)

    def show_loading(self):
        self.loading_movie_video.start()
        self.loading_movie.show()

    def hide_loading(self):
        self.loading_movie_video.stop()
        self.loading_movie.hide()

    def reset_status_bar(self):
        self.status_bar_label.setText('')
        self.hide_loading()

    def save_config(self):
        with open('config.json', 'w') as f:
            f.write(json.dumps(self.config, indent=4))
