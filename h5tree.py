from PyQt5.QtWidgets import QTreeView
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from myGUIApplication_ver2.dataframe_window import DataFrameWindow
from collections import namedtuple
from copy import deepcopy
from pandas import DataFrame
import h5py
from functools import partial

__all__ = ['H5Tree']

MyItem = namedtuple('MyItem', 'parent_id item')
FileItemKeys = namedtuple('FileItemKeys',
                          'short_name key parent_name filename')


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.app_widget = H5Tree(self)
        self.setCentralWidget(self.app_widget)
        self.setWindowTitle('My h5 viewer')

        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        open_new_file_action = QtWidgets.QAction('Open h5 file', self)
        open_new_file_action.triggered.connect(partial(self.openFileNameDialog,
                                                       func=self.app_widget.open_new_h5))
        file_menu.addAction(open_new_file_action)

        add_file_action = QtWidgets.QAction('Add h5 file', self)
        add_file_action.triggered.connect(partial(self.openFileNameDialog,
                                                  func=self.app_widget.add_h5))
        file_menu.addAction(add_file_action)

        self.center()
        self.show()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                                               "Are you sure to quit?", QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            app = QtWidgets.QApplication.instance()
            self.app_widget.close_files()
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


class H5Tree(QTreeView):
    def __init__(self, parent=None, file_list=None):
        super(QTreeView, self).__init__(parent)
        self.header().setDefaultSectionSize(200)
        # self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.items_to_cut = {}
        self.current_df_win = None
        self.connect_context_menu(self.context_menu)
        self.selected_moving_item = None
        self.model_ = MyItemModel()
        self.setModel(self.model_)
        self.number_of_files = 0
        self.adjustSize()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_dict = {}
        if file_list is not None:
            for filename in file_list:
                self.add_h5(filename)

    def open_new_h5(self, filename):
        self.close_files()
        self.model().removeRows(0, self.model().rowCount())
        self.file_dict = {}
        self.number_of_files = 0
        self.add_file_to_tree(filename)

    def add_h5(self, filename):
        self.add_file_to_tree(filename)

    def add_file_to_tree(self, filename):
        file = h5py.File(filename, 'a')
        self.file_dict.update({file.filename: file})
        item_dict = {}

        def add_to_item_list(name):
            name_list = name.split('/')
            short_name = name_list[-1]
            parent_name = '/'.join(name_list[:-1]) if len(name_list) > 1 else '__root__'
            item = QStandardItem(short_name)
            data = FileItemKeys(short_name, name, parent_name, file.filename)
            item.setData(data)
            item_dict.update({name: item})

        file.visit(add_to_item_list)
        file_short_name = file.filename.split('\\')[-1].split('/')[-1]
        file_item = QStandardItem(file_short_name)
        data = FileItemKeys(file_short_name, '__root__', '', file.filename)
        file_item.setData(data)
        self.model_.setItem(self.number_of_files, 0, file_item)
        self.number_of_files += 1
        for item in item_dict.values():
            data = item.data()
            if data.parent_name == '__root__':
                file_item.appendRow(item)
            else:
                item_dict[data.parent_name].appendRow(item)
        self.model().layoutChanged.emit()

    def context_menu(self, position):

        index = self.selectedIndexes()[0]
        selected_object = self.get_selected_object_by_index(index)
        if self.selected_moving_item is not None:
            selected_item = self.model_.itemFromIndex(index)
            cutted_items = [my_item.item.data().key for my_item in
                            self.items_to_cut.values()]
            forbidden_action = selected_item.data().key in cutted_items
        else:
            forbidden_action = False

        menu = QtWidgets.QMenu()

        new_ = menu.addMenu(self.tr("New"))
        create_action = new_.addAction(self.tr("New group"))
        create_action.triggered.connect(self.open_text_box)
        create_action.setEnabled(type(selected_object) in [h5py.Group,
                                                           h5py.File] \
                                 and not forbidden_action)

        menu.addSeparator()

        copy_action = menu.addAction(self.tr("Cut"))
        copy_action.triggered.connect(self.cut_item)
        copy_action.setEnabled(type(selected_object) in [h5py.Group,
                                                         h5py.Dataset])

        cancel_cut_action = menu.addAction(self.tr("Cancel cut"))
        cancel_cut_action.triggered.connect(self.cancel_cut)
        cancel_cut_action.setEnabled(self.selected_moving_item is not None)

        paste_action = menu.addAction(self.tr("Paste"))
        paste_action.triggered.connect(self.move_item)
        paste_action.setEnabled(type(selected_object) in [h5py.Group,
                                                          h5py.File] \
                                and not forbidden_action
                                and len(self.items_to_cut) > 0)
        menu.addSeparator()

        remove_action = menu.addAction(self.tr("Delete"))
        remove_action.triggered.connect(self.remove_item)
        remove_action.setEnabled(type(selected_object) in [h5py.Group,
                                                           h5py.Dataset]
                                 and not forbidden_action)

        menu.addSeparator()

        show_action = menu.addAction(self.tr("Open as a table"))
        open_df = partial(self.open_dataframe_window, obj=selected_object)
        show_action.triggered.connect(open_df)
        show_action.setEnabled(isinstance(selected_object, h5py.Dataset))

        menu.exec_(self.viewport().mapToGlobal(position))

    def open_dataframe_window(self, obj):
        assert isinstance(obj, h5py.Dataset)
        if obj.shape:
            df = DataFrame(obj[()])
        else:
            df = DataFrame()
        self.current_df_win = DataFrameWindow(df)

    def open_text_box(self):
        text, okPressed = QtWidgets.QInputDialog.getText(self, "Create group",
                                                         "Name of new group:",
                                                         QtWidgets.QLineEdit.Normal, "")
        if okPressed and text != '':
            self.create_item(text)

    def create_item(self, text):
        item = self.model_.itemFromIndex(self.selectedIndexes()[0])
        data = item.data()
        filename = data.filename
        new_key = text if data.key == '__root__' else f'{data.key}/{text}'
        parent_key = data.key
        new_item = QStandardItem(text)
        new_item.setData(FileItemKeys(text, new_key, parent_key, filename))
        item.insertRow(0, new_item)
        selected_obj = self.get_selected_object()
        selected_obj.create_group(text)

    def remove_item(self):
        index, = self.selectedIndexes()
        item_to_remove = self.model_.itemFromIndex(index)
        name = item_to_remove.data().short_name
        buttonReply = QtWidgets.QMessageBox.question(self, 'PyQt5 message',
                                                     f"Do you really want to delete {name}"
                                                     f" from h5 file?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                     QtWidgets.QMessageBox.No)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self._remove_by_item(item_to_remove)

    def _remove_by_item(self, item):
        file = self.file_dict[item.data().filename]
        key = item.data().key
        del file[key]
        parent = item.parent() or self.model_
        parent.removeRow(item.index().row())

    def cut_item(self):
        if self.selected_moving_item is not None:
            self.apply_color(self.selected_moving_item, Qt.black)

        def iterate_over_branch(item, parent_id, id_):
            id_ += 1
            number_of_children = item.rowCount()
            my_id = deepcopy(id_)
            copied_item = QStandardItem(item.text())
            copied_item.setData(item.data())
            my_item = MyItem(parent_id, copied_item)
            self.items_to_cut.update({id_: my_item})
            for num in range(number_of_children):
                id_ = iterate_over_branch(item.child(num), my_id, id_)
            return id_

        self.items_to_cut = {}
        index, = self.selectedIndexes()
        item_to_copy = self.model_.itemFromIndex(index)
        iterate_over_branch(item_to_copy, 0, 0)
        self.selected_moving_item = item_to_copy
        self.apply_color(item_to_copy, Qt.red)

    def apply_color(self, item, color=None):
        color = color or Qt.black

        def _paint(item_):
            self.model_.setData(item_.index(),
                                QtGui.QBrush(color),
                                QtCore.Qt.ForegroundRole)
            number_of_children = item_.rowCount()
            for num in range(number_of_children):
                _paint(item_.child(num))

        _paint(item)

    def cancel_cut(self):
        self.apply_color(self.selected_moving_item)
        self.selected_moving_item = None
        self.items_to_cut = {}

    def move_item(self):
        item_to_move_to = self.model_.itemFromIndex(self.selectedIndexes()[0])
        root_item = MyItem(-1, item_to_move_to)
        if item_to_move_to == self.selected_moving_item.parent():
            self.apply_color(self.selected_moving_item)
            self.selected_moving_item = None
            self.items_to_cut = {}
            return
        items_to_copy = {0: root_item}
        items_to_copy.update(self.items_to_cut)
        old_filename = next(iter(self.items_to_cut.values())).item.data().filename
        new_filename = root_item.item.data().filename
        if old_filename == new_filename:
            file = self.file_dict[old_filename]
            old_key = items_to_copy[1].item.data().key
            name = items_to_copy[1].item.data().short_name
            root_item_key = root_item.item.data().key
            if root_item_key == '__root__':
                new_key = name
            else:
                new_key = f'{root_item_key}/{name}'
            message = f'Do you want to move item from {old_key} to {new_key}?'
            buttonReply = QtWidgets.QMessageBox.question(self,
                                                         'PyQt5 message',
                                                         message,
                                                         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                         QtWidgets.QMessageBox.No)
            if buttonReply == QtWidgets.QMessageBox.Yes:
                try:
                    file[new_key] = file[old_key]
                except RuntimeError as err:
                    print(err)
                    return
                id_list = list(self.items_to_cut.keys())
                id_list.sort()

                for id_ in id_list:
                    my_item = self.items_to_cut[id_]
                    parent_id = my_item.parent_id
                    parent = items_to_copy[parent_id].item
                    if parent.data().key == '__root__':
                        new_key = my_item.item.data().short_name
                        parent_name = '__root__'
                    else:
                        new_key = '/'.join([parent.data().key,
                                            my_item.item.data().short_name])
                        parent_name = parent.data().short_name

                    data = FileItemKeys(my_item.item.data().short_name,
                                        new_key, parent_name,
                                        new_filename)
                    print(data)
                    my_item.item.setData(data)
                    if parent_id == 0:
                        parent.insertRow(0, my_item.item)
                    else:
                        parent.appendRow(my_item.item)

                self._remove_by_item(self.selected_moving_item)
                self.selected_moving_item = None
                self.items_to_cut = {}
        else:
            QtWidgets.QMessageBox.question(self, 'PyQt5 message',
                                           'Moving between different'
                                           'h5 files is not supported yet',
                                           QtWidgets.QMessageBox.Ok)

    def connect_context_menu(self, callback):
        self.customContextMenuRequested.connect(callback)

    def get_selected_object_by_index(self, index):
        item = self.model_.itemFromIndex(index)
        data = item.data()
        file = self.file_dict[data.filename]
        if data.key == '__root__':
            return file
        else:
            return file[data.key]

    def get_selected_object(self):
        index = self.selectedIndexes()[0]
        return self.get_selected_object_by_index(index)

    def close_files(self):
        for file in self.file_dict.values():
            file.close()


class MyItemModel(QStandardItemModel):
    def __init__(self):
        super(QStandardItemModel, self).__init__()
        self.setHorizontalHeaderLabels(['Name'])
        self.setRowCount(0)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
