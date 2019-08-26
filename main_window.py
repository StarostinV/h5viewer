from PyQt5 import QtWidgets
from myGUIApplication_ver2.my_app import MyApp
from directories import Directories
import sys
from functools import partial

__all__ = ['run_viewer']


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, h5filelist=None, parent=None):
        super(MainWindow, self).__init__(parent)
        self.app_widget = MyApp(h5filelist, self)
        self.setCentralWidget(self.app_widget)
        self.setWindowTitle('My h5 viewer')
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        open_new_file_action = QtWidgets.QAction('Open h5 file', self)
        open_new_file_action.triggered.connect(partial(self.openFileNameDialog,
                                                       func=self.app_widget.tree.open_new_h5))
        file_menu.addAction(open_new_file_action)

        add_file_action = QtWidgets.QAction('Add h5 file', self)
        add_file_action.triggered.connect(partial(self.openFileNameDialog,
                                                  func=self.app_widget.tree.add_h5))
        file_menu.addAction(add_file_action)

        self.center()
        self.show()

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

    def openFileNameDialog(self, func):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
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
