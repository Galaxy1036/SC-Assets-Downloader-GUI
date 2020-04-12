import os
import sys
import json
import qdarkstyle

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow


if __name__ == '__main__':
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    if os.path.isfile('config.json'):
        with open('config.json') as f:
            config = json.load(f)

        application = MainWindow(app, config)

        # Disable window resize and the maximize button
        application.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        application.show()
        application.setFixedSize(application.size())

        sys.exit(app.exec_())

    else:
        msg = QMessageBox()
        msg.setWindowTitle('Config missing')
        msg.setText("""<p style='text-align: center;'><img src='ui/assets/warning-icon.png' alt='' width='42' height='42'/></p>
                           <p style='align: center;'><strong>config.json file is missing, cannot continue !</strong></p>""")

        msg.exec_()
