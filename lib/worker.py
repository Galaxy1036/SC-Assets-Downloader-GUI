import os

from urllib.request import urlopen
from PyQt5.QtCore import QThread, pyqtSignal

from lib.utils import join_path
from lib.compression import decompress


class DownloadWorker(QThread):

    file_downloaded = pyqtSignal(bool)

    def __init__(self, download_queue,
                 masterhash, assets_url,
                 decompress_data, output_dir):

        self.stopped = False
        self.is_running = True

        self.assets_url = assets_url
        self.masterhash = masterhash
        self.output_dir = output_dir
        self.download_queue = download_queue
        self.decompress_data = decompress_data

        QThread.__init__(self)

    def run(self):
        while self.is_running:
            filename = self.download_queue.get()

            if filename is not None:
                file_url = join_path(self.assets_url, self.masterhash, filename)

                file_data = urlopen(file_url)

                os.makedirs(os.path.dirname(join_path(self.output_dir, filename)), exist_ok=True)

                with open(join_path(self.output_dir, filename), 'wb') as f:
                    if self.decompress_data and filename.endswith(('.csv', '.sc')):
                        f.write(decompress(file_data.read()))

                    else:
                        f.write(file_data.read())

                    f.close()

                self.file_downloaded.emit(self.is_running)

            self.download_queue.task_done()

    def stop(self):
        self.download_queue.put(None)
        self.is_running = False
