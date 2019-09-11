from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from myGUIApplication_ver2.my_app import MyApp
from directories import Directories
import sys

__all__ = ['run_viewer']


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, h5filelist=None, parent=None):
        super(MainWindow, self).__init__(parent)
        self.app_widget = MyApp(h5filelist, self)
        self.setCentralWidget(self.app_widget)
        self.setWindowTitle('My h5 viewer')

        self.init_menu()
        self.init_toolbar()
        self.center()
        self.show()

    def init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        open_new_file_action = QtWidgets.QAction('Open h5 file', self)
        open_new_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_new_file_action)

        add_file_action = QtWidgets.QAction('Add h5 file', self)
        add_file_action.triggered.connect(self.add_file)
        file_menu.addAction(add_file_action)

    def init_toolbar(self):
        add_action = QtWidgets.QAction(QIcon('add.png'), 'Add', self)
        add_action.setShortcut('Ctrl+A')
        add_action.triggered.connect(self.add_file)

        zoom_action = QtWidgets.QAction(QIcon('zoom.png'), 'Zoom', self)

        color_action = QtWidgets.QAction(QIcon('color.png'), 'Colormap', self)

        profile_action = QtWidgets.QAction(QIcon('profile.png'), 'Profile', self)

        exit_action = QtWidgets.QAction(QIcon('exit.png'), 'Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)

        toolbar = self.addToolBar('Common')
        toolbar.addAction(add_action)
        toolbar.addSeparator()
        toolbar.addAction(color_action)
        toolbar.addAction(profile_action)
        toolbar.addAction(zoom_action)

    def add_file(self):
        self.open_file_name_dialog(self.app_widget.tree.add_h5)

    def open_file(self):
        self.open_file_name_dialog(self.app_widget.tree.open_new_h5)

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                                               "Are you sure to quit?", QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.app_widget.close_files()
            event.accept()
            app = QtWidgets.QApplication.instance()
            app.closeAllWindows()
        else:
            event.ignore()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def open_file_name_dialog(self, func):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open h5 file", "",
                                                            "hdf5 files (*.h5)", options=options)
        if fileName:
            func(fileName)


def run_viewer(filelist):
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(filelist)
    sys.exit(app.exec_())


if __name__ == '__main__':
    import os

    h5_filename = os.path.join(Directories.get_dir_to_save_images(), 'whole_data.h5')
    run_viewer([h5_filename, 'new_metadata.h5'])
