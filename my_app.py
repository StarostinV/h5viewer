from PyQt5 import QtWidgets
import h5py

from myGUIApplication_ver2.h5tree import H5Tree
from myGUIApplication_ver2.my_label import DescriptiveLabel
from myGUIApplication_ver2.h5plot import H5Plot


class MyApp(QtWidgets.QWidget):
    def __init__(self, h5file_list=None, parent=None):
        super(MyApp, self).__init__(parent)
        self.setWindowTitle('My H5 Viewer')
        self.current_df_win = None
        self.tree = H5Tree(self, h5file_list)
        self.tree.clicked.connect(self.on_clicked)
        self.plot_widget = H5Plot()
        self.plot_handler = self.plot_widget.canvas
        self.h5InfoWidget = DescriptiveLabel()

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.tree, 0, 0, 0, 1)
        self.grid.addWidget(self.h5InfoWidget, 0, 1)
        self.grid.addWidget(self.plot_widget, 1, 1)

    def open_new_h5(self, filename):
        self.tree.change_file(filename)

    def add_h5(self, filename):
        self.tree.add_file(filename)

    def on_clicked(self, signal):
        selected_object, file = self.tree.get_obj_with_file(signal)
        self.update_label(selected_object)
        try:
            if isinstance(selected_object, h5py.Dataset):
                if selected_object.shape:
                    if type(selected_object[0]) in self.plot_handler.allowed_types:
                        self.plot_handler.update_plot(selected_obj=selected_object, file=file)
                    else:
                        print(selected_object[0])
                        print(type(selected_object[0]))
        except Exception as err:
            print('ERROR OCCURED!!!')
            print(err)

    def update_label(self, obj):
        self.h5InfoWidget.update_table(obj)

    def close_files(self):
        self.tree.close_files()
