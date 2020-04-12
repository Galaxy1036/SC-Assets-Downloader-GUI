from PyQt5.QtWidgets import QMessageBox


def join_path(*path):
    return '/'.join(path)


def is_masterhash_valid(masterhash):
    return not masterhash or (all(char in '0123456789abcdef' for char in masterhash) and len(masterhash) == 40)


def is_fingerprint_valid(fingerprint):
    if 'sha' in fingerprint:
        if 'files' in fingerprint:
            for file in fingerprint['files']:
                if 'file' not in file:
                    return False

        else:
            return False

    else:
        return False

    return True


def build_alert_box(title, message):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText("""<p style='text-align: center;'><img src='ui/assets/warning-icon.png' alt='' width='42' height='42'/></p>
                   <p style='align: center;'><strong>{}</strong></p>""".format(message))

    msg.exec_()
