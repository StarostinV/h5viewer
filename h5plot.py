import numpy as np
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import use as matplotlib_use

from myGUIApplication_ver2.axes_1d import Axes1D
from myGUIApplication_ver2.axes_2d import Axes2D

matplotlib_use("Qt5Agg")


class H5Plot(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = WidgetPlot(self)
        self.toolbar = NavigationToolbar(self.canvas, self, coordinates=True)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)


class WidgetPlot(FigureCanvas):
    def __init__(self, parent=None):
        self.status = 0
        self.params_2d = {}
        self.params_1d = {}
        self.allowed_types = [np.float64, np.float32, np.ndarray, np.int32]

        self.fig = Figure()
        super(WidgetPlot, self).__init__(self.fig)
        self.setParent(parent)
        self.mpl_connect('button_press_event', self.context_menu)
        ax_1d = self.fig.add_subplot(111, label='ax_1d')
        self.axes_1d = Axes1D(ax_1d, self)
        ax_1d.set_visible(False)
        ax_2d = self.fig.add_subplot(111, label='ax_2d')
        ax_2d.set_visible(False)
        self.axes_2d = Axes2D(ax_2d, self)
        self.axes_dict = {0: None, 1: self.axes_1d, 2: self.axes_2d}
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def update_plot(self, selected_obj, file):
        if len(selected_obj.shape) not in [1, 2]:
            return
        new_status = len(selected_obj.shape)
        current_ax = self.axes_dict[new_status]
        if new_status != self.status and self.status:
            self.axes_dict[self.status].ax.set_visible(False)
        current_ax.ax.set_visible(True)
        current_ax.update_plot(selected_obj, file)
        self.status = new_status

    def context_menu(self, event):
        if event.button == 3 and self.status:
            self.axes_dict[self.status].context_menu(event)
