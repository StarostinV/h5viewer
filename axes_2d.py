import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QMenu, QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector

from myGUIApplication.colormap_window import ColormapWindow


class Axes2D(object):
    def __init__(self, ax, parent):
        self.ax = ax
        self.parent = parent

        self.params_2d = {}
        self.extent = None
        self.y, self.x1, self.x2, self.data = [], [], [], []
        self.rectangle_coordinates = None
        self.RectangleSelector = None
        self.cut_window = None
        self.colormap_window = None
        self.apply_log_status = False
        self.plot_obj = None
        self.Ranges = Plot2DRangesHandler(self)

    def set_rectangle(self):
        self.RectangleSelector = RectangleSelector(self.ax,
                                                   self.line_select_callback,
                                                   drawtype='box',
                                                   button=[1],  # don't use middle button
                                                   minspanx=5,
                                                   minspany=5,
                                                   spancoords='pixels',
                                                   interactive=True)

        def update_rs(event):
            if self.RectangleSelector is not None:
                if self.RectangleSelector.active and self.parent.status == 2:
                    self.RectangleSelector.update()

        self.parent.mpl_connect('draw_event', update_rs)
        if self.rectangle_coordinates is not None:
            x1, y1, x2, y2 = self.rectangle_coordinates
            self.RectangleSelector.extents = (x1, x2, y1, y2)
            self.RectangleSelector.update()

    def line_select_callback(self, eclick, erelease):
        """eclick and erelease are the press and release events"""
        assert self.cut_window is not None
        self.rectangle_coordinates = int(eclick.xdata), int(eclick.ydata), int(erelease.xdata), int(erelease.ydata)
        self.cut_window.canvas.update_cut_plot()

    def context_menu(self, event):
        menu = QMenu()
        y = self.parent.parent().height()
        position = self.parent.mapFromParent(QPoint(event.x, y - event.y))
        parameter_menu = menu.addMenu('Plot parameters')
        change_colormap_action = parameter_menu.addAction("Change colormap")
        change_colormap_action.triggered.connect(self.open_colormap_window)

        log_action_name = "Disable log" if self.apply_log_status else "Apply log"
        change_log_action = parameter_menu.addAction(log_action_name)
        change_log_action.triggered.connect(self.change_log_status)

        reset_action = parameter_menu.addAction("Reset parameters")
        reset_action.triggered.connect(self.reset_parameters)

        menu.addSeparator()
        open_cut_window_action = menu.addAction("Open cut window")
        open_cut_window_action.triggered.connect(self.open_cut_window)
        open_cut_window_action.setEnabled(self.cut_window is None)
        menu.exec_(self.parent.parent().mapToGlobal(position))

    def open_colormap_window(self, event):
        range_init, range_whole = self.Ranges.get_ranges_for_colormap(self.y)
        self.colormap_window = ColormapWindow(range_init, range_whole, title='Colormap')
        self.colormap_window.set_callback(self.colormap_callback)
        self.colormap_window.show()

    def redraw_2d_plot(self):
        self.ax.cla()
        self.plot_obj = self.ax.imshow(self.y, **self.params_2d)
        if self.cut_window:
            self.set_rectangle()

    def colormap_callback(self, range_):
        self.Ranges.update_params(range_)
        self.redraw_2d_plot()
        self.parent.draw()

    def change_log_status(self, event):
        self.apply_log_status = not self.apply_log_status
        if self.apply_log_status:
            self.y = self.apply_log(self.data)
        else:
            self.y = self.data
        self.Ranges.change_regime()
        self.redraw_2d_plot()
        self.parent.draw()

    def reset_parameters(self, event):
        self.apply_log_status = False
        self.params_2d = {}
        self.redraw_2d_plot()
        self.parent.draw()

    @staticmethod
    def apply_log(data):
        min_value = max([0.1, np.amin(data)])
        max_value = np.amax(data)
        return np.log(np.clip(data, min_value, max_value))

    def update_plot(self, data, x=None):
        self.data = data
        if self.apply_log_status:
            self.y = self.apply_log(data)
        else:
            self.y = data
        if self.plot_obj is not None:
            self.plot_obj.set_data(self.y)
            self.ax.relim()  # Recalculate limits
            self.ax.autoscale_view(True, True, True)
        else:
            self.plot_obj = self.ax.imshow(self.y, **self.params_2d)
        if x is not None:
            assert type(x) == tuple
            assert len(x) == 2
            assert (len(x[0]), len(x[1])) == data.shape
            self.extent = (x[0][0], x[0][-1], x[1][0], x[1][-1])
            self.plot_obj.set_extent(self.extent)
        else:
            self.extent = None
        self.parent.draw()
        if self.cut_window:
            self.cut_window.canvas.update_cut_plot()

    def open_cut_window(self):
        self.cut_window = CutWindow(self)
        self.set_rectangle()
        if self.rectangle_coordinates:
            self.cut_window.canvas.update_cut_plot()

    def on_closing_cut_window(self):
        self.RectangleSelector.set_visible(False)
        self.RectangleSelector.update()
        self.RectangleSelector = None
        self.cut_window = None


class Plot2DRangesHandler(object):
    MIN_LOG_ARG = 0.1
    DEFAULT_PARAMS = {}

    def __init__(self, plotWidget):
        self.plotWidget = plotWidget
        self.absolute_range = None
        self.log_range = None

    def get_ranges_for_colormap(self, data):
        range_whole = (np.amin(data), np.amax(data))
        if 'vmax' in self.plotWidget.params_2d:
            range_init = (self.plotWidget.params_2d['vmin'], self.plotWidget.params_2d['vmax'])
        else:
            range_init = range_whole
        return range_init, range_whole

    def _update_params(self):
        vmin = self.plotWidget.params_2d.get('vmin', None)
        vmax = self.plotWidget.params_2d.get('vmax', None)
        if self.plotWidget.apply_log_status:
            self.log_range = (vmin, vmax)
            self.absolute_range = (np.exp(vmin), np.exp(vmax))
        else:
            self.absolute_range = (vmin, vmax)
            self.log_range = (np.log(max([vmin, self.MIN_LOG_ARG])), np.log(vmax))

    def update_params(self, range_):
        self.plotWidget.params_2d.update({'vmin': range_[0], 'vmax': range_[1]})
        self._update_params()

    def change_regime(self):
        if 'vmax' in self.plotWidget.params_2d:
            if self.plotWidget.apply_log_status:
                self.plotWidget.params_2d.update({'vmin': self.log_range[0],
                                                  'vmax': self.log_range[1]})
            else:
                self.plotWidget.params_2d.update({'vmin': self.absolute_range[0],
                                                  'vmax': self.absolute_range[1]})


class CutWindow(QWidget):
    def __init__(self, plot2d_canvas):
        super(CutWindow, self).__init__()
        self.setLayout(QVBoxLayout())
        self.canvas = CutCanvas(plot2d_canvas, self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)
        self.setWindowTitle('Cut window')
        self.show()

    def closeEvent(self, event):
        event.accept()
        self.canvas.plot2d_canvas.on_closing_cut_window()


class CutCanvas(FigureCanvas):
    def __init__(self, plot2d_canvas, parent=None):
        self.plot2d_canvas = plot2d_canvas
        self.fig = Figure()
        super(CutCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.mpl_connect('button_press_event', self.context_menu)
        self.ax_cut = self.fig.add_subplot(111)
        self.x, self.y, self.data = [], [], []
        self.cut_y, self.cut_x = [], []
        self.cut_plot, = self.ax_cut.plot(self.cut_x, self.cut_y)
        self.plot_list = [self.cut_plot]
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    @staticmethod
    def lorentzian(x, a, w, x0):
        return a / ((x - x0) ** 2 + w)

    def default_fit_function(self, x, central_a, central_w, side_a, side_w, side_x0):
        return self.lorentzian(x, central_a, central_w, 0) + \
               self.lorentzian(x, side_a, side_w, side_x0) + \
               self.lorentzian(x, side_a, side_w, - side_x0)

    def context_menu(self, event):
        if event.button == 3:
            y = self.parent().height()
            position = self.mapFromParent(QPoint(event.x, y - event.y))
            menu = QMenu()
            freeze_cut_action = menu.addAction(self.tr('Freeze current cut'))
            freeze_cut_action.triggered.connect(self.freeze_cut)
            freeze_cut_action.setEnabled(len(self.cut_y) > 0)

            delete_cuts_action = menu.addAction(self.tr('Delete cuts'))
            delete_cuts_action.triggered.connect(self.delete_cuts)
            delete_cuts_action.setEnabled(len(self.plot_list) > 1)

            menu.addSeparator()
            fit_action = menu.addAction(self.tr('Plot fit'))
            fit_action.triggered.connect(self.get_fit)
            fit_action.setEnabled(len(self.plot_list) > 0)
            menu.exec_(self.parent().mapToGlobal(position))

    def freeze_cut(self):
        self.plot_list.append(self.ax_cut.plot(self.cut_x, self.cut_y)[0])
        self.cut_x = []
        self.cut_y = []
        self.cut_plot.set_ydata(self.cut_y)
        self.cut_plot.set_xdata(self.cut_x)
        self.ax_cut.relim()  # Recalculate limits
        self.ax_cut.autoscale_view(True, True, True)
        self.draw()

    def get_fit(self):
        pass

    def delete_cuts(self):
        assert len(self.plot_list) > 1
        for _ in range(len(self.plot_list) - 1):
            self.plot_list.pop(1).remove()
        self.ax_cut.relim()  # Recalculate limits
        self.ax_cut.autoscale_view(True, True, True)
        self.draw()

    def update_cut_plot(self):
        frame = self.plot2d_canvas.data
        x1, y1, x2, y2 = self.plot2d_canvas.rectangle_coordinates
        frame = frame[y1:y2, x1:x2]

        if abs(y2 - y1) < abs(x2 - x1):
            mean_axis = 0
            self.cut_x = list(range(x1, x2, 1))
        else:
            mean_axis = 1
            self.cut_x = list(range(y1, y2, 1))

        self.cut_y = np.mean(frame, axis=mean_axis)
        assert len(self.cut_y) == len(self.cut_x)
        self.cut_plot.set_ydata(self.cut_y)
        self.cut_plot.set_xdata(self.cut_x)
        self.ax_cut.relim()  # Recalculate limits
        self.ax_cut.autoscale_view(True, True, True)
        self.draw()
