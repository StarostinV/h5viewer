from PyQt5 import QtWidgets, QtCore
import h5py

from myGUIApplication_ver2.h5tree import H5Tree
from myGUIApplication_ver2.my_label import DescriptiveLabel
from myGUIApplication_ver2.plotWidget import H5Plot


class MyApp(QtWidgets.QWidget):
    def __init__(self, h5file_list=None, parent=None):
        super(MyApp, self).__init__(parent)
        self.setWindowTitle('My H5 Viewer')
        self.current_df_win = None
        self.tree = H5Tree(self, h5file_list)
        self.tree.clicked.connect(self.on_clicked)
        self.plot_widget = H5Plot()
        self.plot_handler = self.plot_widget.canvas
        self.plot_handler.mpl_connect('button_press_event', self.graph_params_window)
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
        selected_object = self.tree.get_selected_object_by_index(signal)
        self.update_label(selected_object.__repr__())
        if isinstance(selected_object, h5py.Dataset):
            if selected_object.shape:
                if type(selected_object[0]) in self.plot_handler.allowed_types:
                    self.plot_handler.update_plot(y=selected_object[()])
                else:
                    print(selected_object[0])
                    print(type(selected_object[0]))

    def update_label(self, label):
        self.h5InfoWidget.setText(label)

    def graph_params_window(self, event):
        if event.button == 3 and self.plot_handler.status == 2:
            x = self.tree.frameGeometry().width()
            y = self.plot_handler.frameGeometry().height()
            position = self.mapFromParent(QtCore.QPoint(event.x + x, -event.y+y))

            menu = QtWidgets.QMenu()
            parameter_menu = menu.addMenu(self.tr('Plot parameters'))
            change_colormap_action = parameter_menu.addAction(self.tr("Change colormap"))
            change_colormap_action.triggered.connect(self.plot_handler.open_colormap_window)

            log_action_name = "Disable log" if self.plot_handler.apply_log_status else "Apply log"
            change_log_action = parameter_menu.addAction(self.tr(log_action_name))
            change_log_action.triggered.connect(self.plot_handler.change_log_status)

            reset_action = parameter_menu.addAction(self.tr("Reset parameters"))
            reset_action.triggered.connect(self.plot_handler.reset_parameters)

            menu.addSeparator()
            open_cut_window_action = menu.addAction(self.tr("Open cut window"))
            open_cut_window_action.triggered.connect(self.plot_handler.open_cut_window)
            open_cut_window_action.setEnabled(self.plot_handler.cut_window is None)
            menu.exec_(self.tree.viewport().mapToGlobal(position))
            # TODO handle position in a normal way and move function to plot_handler class

    def close_files(self):
        self.tree.close_files()
