import os
import json
import socket

from queue import Queue
from datetime import datetime
from urllib.request import urlopen
from urllib.error import HTTPError

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit,
                             QCheckBox, QComboBox, QHBoxLayout,
                             QVBoxLayout, QPushButton, QProgressBar,
                             QMessageBox, QFileDialog)

from lib.reader import Reader
from lib.writer import Writer
from lib.worker_launcher import WorkerLauncher
from lib.utils import join_path, build_alert_box, is_fingerprint_valid, is_masterhash_valid
from ui.download_choice_window import DownloadChoiceWindow


class DownloadWidget(QWidget):
    def __init__(self, parent, config):
        super().__init__()

        self.parent = parent
        self.config = config
        self.masterhash = None
        self.assets_host = None
        self.fingerprint = None

        self.download_started = False
        self.bruteforce_started = False

        self.major = self.config['major']
        self.build = self.config['build']

        self.total_files = 0
        self.downloaded_files = 0

        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout()

        self.init_left_panel()
        self.init_right_panel()

        self.setLayout(self.main_layout)

    def init_left_panel(self):
        self.left_panel_widget = QWidget()
        self.left_panel_layout = QVBoxLayout()

        self.download_method_combo_box = QComboBox()
        self.download_method_combo_box.addItems(['Latest Patch', 'Masterhash', 'Fingerprint file'])
        self.download_method_combo_box.currentIndexChanged.connect(self.on_combo_box_change)

        self.masterhash_input = QLineEdit()

        self.masterhash_input.setPlaceholderText('Enter a masterhash')
        self.masterhash_input.setAlignment(Qt.AlignCenter)
        self.masterhash_input.setMaxLength(40)
        self.masterhash_input.textChanged.connect(self.on_masterhash_changed)
        self.masterhash_input.hide()

        self.masterhash_validity_widget = QWidget()
        self.masterhash_validity_layout = QHBoxLayout()

        self.masterhash_validity_icon = QLabel()
        self.masterhash_validity_icon.setPixmap(QPixmap('ui/assets/warning-icon.png').scaled(17, 17))
        self.masterhash_validity_label = QLabel('Invalid  hash !')

        self.masterhash_validity_layout.addWidget(self.masterhash_validity_icon)
        self.masterhash_validity_layout.addWidget(self.masterhash_validity_label)

        self.masterhash_validity_widget.setLayout(self.masterhash_validity_layout)
        self.masterhash_validity_widget.hide()

        self.browse_fingerprint_widget = QWidget()
        self.browse_fingerprint_layout = QHBoxLayout()

        self.fingerprint_path_input = QLineEdit()
        self.fingerprint_path_input.setEnabled(False)

        self.browse_fingerprint_button = QPushButton('', self)
        self.browse_fingerprint_button.setIcon(QIcon('ui/assets/browse.png'))
        self.browse_fingerprint_button.setIconSize(QSize(17, 17))
        self.browse_fingerprint_button.clicked.connect(self.browse_fingerprint)

        self.browse_fingerprint_layout.addWidget(self.fingerprint_path_input)
        self.browse_fingerprint_layout.addWidget(self.browse_fingerprint_button)

        self.browse_fingerprint_widget.setLayout(self.browse_fingerprint_layout)
        self.browse_fingerprint_widget.hide()

        self.enable_compression_checkbox = QCheckBox('Enable LZMA/LZHAM\ndecompression for\nCSV / SC files')

        self.left_panel_layout.addWidget(QLabel('Download from:'))
        self.left_panel_layout.addWidget(self.download_method_combo_box)
        self.left_panel_layout.addWidget(self.masterhash_input)
        self.left_panel_layout.addWidget(self.masterhash_validity_widget)
        self.left_panel_layout.addWidget(self.browse_fingerprint_widget)
        self.left_panel_layout.addWidget(self.enable_compression_checkbox)

        self.left_panel_layout.addStretch(1)

        self.left_panel_widget.setLayout(self.left_panel_layout)

        self.main_layout.addWidget(self.left_panel_widget)

    def init_right_panel(self):
        self.right_panel_widget = QWidget()
        self.right_panel_layout = QVBoxLayout()

        self.download_buttons_widget = QWidget()
        self.download_buttons_layout = QHBoxLayout()

        self.start_button = QPushButton('Start Download', self)
        self.start_button.setIcon(QIcon('ui/assets/start.png'))
        self.start_button.setIconSize(QSize(17, 17))
        self.start_button.clicked.connect(self.request_info)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.setIcon(QIcon('ui/assets/stop.png'))
        self.stop_button.setIconSize(QSize(17, 17))
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_download)

        self.download_buttons_layout.addWidget(self.start_button)
        self.download_buttons_layout.addWidget(self.stop_button)

        self.download_buttons_widget.setLayout(self.download_buttons_layout)

        self.progress_bar = QProgressBar(self)

        self.right_panel_layout.addWidget(self.download_buttons_widget)
        self.right_panel_layout.addWidget(self.progress_bar)

        self.right_panel_layout.addStretch(20)

        self.right_panel_widget.setLayout(self.right_panel_layout)

        self.main_layout.addWidget(self.right_panel_widget)

    def on_combo_box_change(self, _):
        method = self.download_method_combo_box.currentText()

        if method != 'Masterhash':
            self.start_button.setEnabled(True)
            self.masterhash_validity_widget.hide()

        if method == 'Latest Patch':
            self.masterhash_input.hide()
            self.browse_fingerprint_widget.hide()

        elif method == 'Masterhash':
            masterhash = self.masterhash_input.text()

            if masterhash:
                self.on_masterhash_changed(masterhash)

            self.masterhash_input.show()
            self.browse_fingerprint_widget.hide()

        else:
            self.masterhash_input.hide()
            self.browse_fingerprint_widget.show()

    def browse_fingerprint(self):
        fingerprint_path, _ = QFileDialog.getOpenFileName(self, 'Open fingerprint',
                                                          '', "JSON file (*.json)")

        self.fingerprint_path_input.setText(fingerprint_path)

    def request_info(self):
        download_method = self.download_method_combo_box.currentText()

        if download_method == 'Masterhash':
            masterhash = self.masterhash_input.text()

            if not masterhash:
                return build_alert_box('Missing masterhash', 'Please enter a masterhash first !')

        elif download_method == 'Fingerprint file':
            fingerprint_path = self.fingerprint_path_input.text()

            if fingerprint_path:
                if os.path.isfile(fingerprint_path):
                    with open(fingerprint_path) as f:
                        try:
                            fingerprint = json.load(f)

                            if is_fingerprint_valid(fingerprint):
                                self.fingerprint = fingerprint

                            else:
                                return build_alert_box('Invalid fingerprint', 'The given fingerprint is missing needed fields !')

                        except json.decoder.JSONDecodeError:
                            return build_alert_box('Invalid fingerprint', 'Couldn\'t parse the given fingerprint !')

                else:
                    return build_alert_box('Fingerprint error', 'Cannot retrieve fingerprint !')

            else:
                return build_alert_box('Missing fingerprint', 'Please select a fingerprint first !')

        self.parent.show_loading()
        self.parent.status_bar_label.setText('Fetching assets host & fingerprint from supercell servers')

        self.info_fetcher_thread = InfoFetcherThread(self)
        self.info_fetcher_thread.info_fetched.connect(self.on_info_fetched)

        self.info_fetcher_thread.start()

    def on_info_fetched(self, login_failed):
        self.info_fetcher_thread.quit()

        download_method = self.download_method_combo_box.currentText()

        login_failed_error_code = login_failed.read_vint()

        if login_failed_error_code == 7:
            fingerprint = login_failed.read_string()

            login_failed.read_string()
            login_failed.read_string()
            login_failed.read_string()
            login_failed.read_vint()
            login_failed.read_byte()
            login_failed.read_string()

            assets_host_count = login_failed.read_vint()

            if assets_host_count:
                self.assets_host = login_failed.read_string()

            else:
                return build_alert_box('Download error', 'Couldn\'t find any host to download assets !')

        elif login_failed_error_code == 8:
            reply = QMessageBox.question(
                self, 'Warning', 'Can\'t fetch current info, build and major from config are outdated. There was probably a game update, would you like to automatically update them ?', QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.update_client_hello_version()

            return

        elif login_failed_error_code == 10:
            return build_alert_box('Error', 'Server is in maintenance, cannot fetch current info')

        else:
            return build_alert_box('Error', 'Wrong login failed code: {}'.format(login_failed_error_code))

        if download_method == 'Latest Patch':
            self.fingerprint = json.loads(fingerprint)

        elif download_method == 'Masterhash':
            masterhash = self.masterhash_input.text()

            try:
                self.fingerprint = json.load(urlopen(self.assets_host + '/' + masterhash + '/fingerprint.json'))

            except HTTPError:
                self.parent.reset_status_bar()
                return build_alert_box('Download error', 'Couldn\'t fetch any fingerprint for this masterhash !')

        self.parent.hide_loading()
        self.parent.status_bar_label.setText('Fingerprint successfully fetched, version: {}'.format(self.fingerprint['version']))

        files_extension = []

        for file in self.fingerprint['files']:
            ext = os.path.splitext(file['file'])[1]

            if ext not in files_extension:
                files_extension.append(ext)

        self.start_button.setEnabled(False)
        self.download_method_combo_box.setEnabled(False)

        download_choice_windows = DownloadChoiceWindow(self, files_extension)
        download_choice_windows.show()
    def request_login_failed(self):
        client_hello_writer = Writer()

        client_hello_writer.write_int(3)
        client_hello_writer.write_int(27)
        client_hello_writer.write_int(self.major)
        client_hello_writer.write_int(0)
        client_hello_writer.write_int(self.build)
        client_hello_writer.write_string('')
        client_hello_writer.write_int(2)
        client_hello_writer.write_int(2)

        client_hello = (10100).to_bytes(2, 'big') + len(client_hello_writer.buffer).to_bytes(3, 'big') + bytes(2) + client_hello_writer.buffer

        s = socket.create_connection(('game.clashroyaleapp.com', 9339))
        s.send(client_hello)

        header = s.recv(7)
        message_length = int.from_bytes(header[2:5], 'big')

        login_failed = b''

        while message_length:
            data = s.recv(message_length)
            message_length -= len(data)
            login_failed += data

        return Reader(login_failed)

    def update_client_hello_version(self):
        self.start_button.setEnabled(False)
        self.download_method_combo_box.setEnabled(False)

        self.parent.show_loading()

        self.bruteforce_thread = UpdateClientHelloVersionThread(self)

        self.bruteforce_thread.values_found.connect(self.on_values_found)

        self.bruteforce_thread.start()

    def on_values_found(self):
        self.bruteforce_thread.quit()

        self.parent.hide_loading()
        self.parent.status_bar_label.setText('Successfully bruteforced build and major ! New major version: {}, new build version: {}'.format(self.major, self.build))

        self.config['major'] = self.major
        self.config['build'] = self.build

        self.parent.save_config()

        self.start_button.setEnabled(True)
        self.download_method_combo_box.setEnabled(True)

    def stop_download(self):
        self.worker_launcher.stop()
        self.worker_launcher.quit()

        self.on_donwload_finish()

    def on_masterhash_changed(self, masterhash):
        if not is_masterhash_valid(masterhash):
            self.masterhash_validity_widget.show()
            self.start_button.setEnabled(False)

        else:
            self.masterhash_validity_widget.hide()
            self.start_button.setEnabled(True)

    def start_download(self, wanted_extensions):
        self.downloaded_files = 0
        self.download_start_time = datetime.utcnow()
        self.download_queue = Queue()

        overwrite_existing_file = False

        if os.path.isdir(join_path(self.parent.settings_widget.folder_path_input.text(), self.fingerprint['sha'])):
            reply = QMessageBox.question(self, 'Warning', 'This patch was already downloaded, would you like to overwrite existing files ?', QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                overwrite_existing_file = True

        self.fingerprint['files'].append({'file': 'fingerprint.json'})

        for file in self.fingerprint['files']:
            if file['file'].endswith(wanted_extensions):
                if overwrite_existing_file:
                    self.download_queue.put(file['file'])

                else:
                    if not os.path.isfile(join_path(self.parent.settings_widget.folder_path_input.text(), self.fingerprint['sha'], file['file'])):
                        self.download_queue.put(file['file'])

        self.total_files = self.download_queue.qsize()

        self.parent.show_loading()

        self.worker_launcher = WorkerLauncher(self)

        self.worker_launcher.file_downloaded.connect(self.update_download_count)
        self.worker_launcher.download_finished.connect(self.on_donwload_finish)

        self.worker_launcher.start()

    def update_download_count(self, update_status):
        self.downloaded_files += 1

        if update_status:
            self.progress_bar.setValue(self.downloaded_files / self.total_files * 100)
            self.parent.status_bar_label.setText('Download started with {} workers, {}/{} files downloaded !'.format(self.workers_count,
                                                                                                                     self.downloaded_files,
                                                                                                                     self.total_files))

    def on_donwload_finish(self):
        self.parent.hide_loading()
        self.download_method_combo_box.setEnabled(True)

        if self.downloaded_files:
            elapsed_time = (datetime.utcnow() - self.download_start_time).seconds

            self.parent.status_bar_label.setText('''Download finished ! {} files downloaded in {}min {}s'''.format(self.downloaded_files,
                                                                                                                   *divmod(elapsed_time, 60)))

        else:
            self.parent.status_bar_label.setText('No files were downloaded !')

        self.progress_bar.reset()
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)

    def display_bruteforce_info(self):
        self.parent.status_bar_label.setText('Bruteforce started ! Trying with major {} and build {}'.format(self.major, self.build))


class InfoFetcherThread(QThread):
    info_fetched = pyqtSignal(object)

    def __init__(self, parent):
        self.parent = parent
        QThread.__init__(self)

    def run(self):
        login_failed = self.parent.request_login_failed()

        self.info_fetched.emit(login_failed)


class UpdateClientHelloVersionThread(QThread):

    values_found = pyqtSignal()

    def __init__(self, parent):
        self.parent = parent
        QThread.__init__(self)

    def run(self):
        major_found = False
        build_found = False

        # Check major first with build 0 to avoid getting error code 9 due to too high build instead of too high major
        build = self.parent.build

        self.parent.build = 0

        while not major_found:
            self.parent.major += 1
            self.parent.display_bruteforce_info()
            login_failed = self.parent.request_login_failed()

            major_found = login_failed.read_vint() == 9

        self.parent.major -= 1
        self.parent.build = build

        reset_build = self.parent.request_login_failed().read_vint() == 9

        if reset_build:
            self.parent.build = 0

        while not build_found:
            self.parent.build += 1
            self.parent.display_bruteforce_info()
            login_failed = self.parent.request_login_failed()

            build_found = login_failed.read_vint() == 7

        self.values_found.emit()
