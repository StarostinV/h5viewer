import numpy as np
from matplotlib.figure import Figure
from myGUIApplication.colormap_window import ColormapWindow
from PyQt5.QtWidgets import QSizePolicy, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import use as matplotlib_use
from matplotlib.widgets import RectangleSelector

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
        self.colormap_window = None
        self.apply_log_status = False
        self.Ranges = Plot2DRangesHandler(self)

        self.fig = Figure()
        super(WidgetPlot, self).__init__(self.fig)
        self.setParent(parent)
        self.axes = self.fig.add_subplot(111)
        self.x, self.y, self.data = [], [], []
        self.plot_obj = None
        self.rectangle_coordinates = None
        self.RectangleSelector = None
        self.cursor = None
        self.cut_window = None
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

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

    def set_cursor(self):
        self.cursor = SnaptoCursor(self, self.x, self.y)
        self.mpl_connect('motion_notify_event', self.cursor.mouse_move)
        self.mpl_connect('key_press_event', self.cursor.key_press)
        self.mpl_connect('key_release_event', self.cursor.key_release)

    def set_rectangle(self):
        self.RectangleSelector = RectangleSelector(self.axes,
                                                   self.line_select_callback,
                                                   drawtype='box',
                                                   # useblit=True,
                                                   button=[1, 3],  # don't use middle button
                                                   minspanx=5,
                                                   minspany=5,
                                                   spancoords='pixels',
                                                   interactive=True)

        def update_rs(event):
            if self.RectangleSelector is not None:
                if self.RectangleSelector.active and self.status == 2:
                    self.RectangleSelector.update()

        self.mpl_connect('draw_event', update_rs)
        if self.rectangle_coordinates is not None:
            x1, y1, x2, y2 = self.rectangle_coordinates
            self.RectangleSelector.extents = (x1, x2, y1, y2)
            self.RectangleSelector.update()

    def line_select_callback(self, eclick, erelease):
        """eclick and erelease are the press and release events"""
        self.rectangle_coordinates = int(eclick.xdata), int(eclick.ydata), int(erelease.xdata), int(erelease.ydata)
        self.cut_window.canvas.update_cut_plot()

    def update_plot(self, y, x=None):
        if len(y.shape) == 1:
            self.update_1d_plot(y, x)
        elif len(y.shape) == 2:
            self.update_2d_plot(y)

    def update_1d_plot(self, y, x):
        self.y = y
        self.x = x or list(range(len(y)))
        if self.status != 1:
            self.axes.remove()
            self.axes = self.fig.add_subplot(111)
            self.plot_obj, = self.axes.plot(self.x, self.y,
                                            **self.params_1d)
            # self.set_cursor()
        else:
            self.plot_obj.set_xdata(self.x)
            self.plot_obj.set_ydata(self.y)
        self.axes.relim()  # Recalculate limits
        self.axes.autoscale_view(True, True, True)
        self.draw()
        self.status = 1

    def apply_log(self, data):
        min_value = max([0.1, np.amin(data)])
        max_value = np.amax(data)
        return np.log(np.clip(data, min_value, max_value))

    def update_2d_plot(self, data):
        self.data = data
        if self.apply_log_status:
            self.y = self.apply_log(data)
        else:
            self.y = data
        self.x = None
        if self.status != 2:
            # self.cursor = None
            self.redraw_2d_plot()
        else:
            self.plot_obj.set_data(self.y)
        self.axes.relim()  # Recalculate limits
        self.axes.autoscale_view(True, True, True)
        self.draw()
        if self.cut_window:
            self.cut_window.canvas.update_cut_plot()
        self.status = 2

    def open_colormap_window(self, event):
        if self.status != 2:
            raise ValueError('NOT A 2D STATUS')
        range_init, range_whole = self.Ranges.get_ranges_for_colormap(self.y)
        self.colormap_window = ColormapWindow(range_init, range_whole, title='Colormap')
        self.colormap_window.set_callback(self.colormap_callback)
        self.colormap_window.show()

    def redraw_2d_plot(self):
        self.axes.cla()
        self.plot_obj = self.axes.imshow(self.y, **self.params_2d)
        if self.cut_window:
            self.set_rectangle()

    def colormap_callback(self, range_):
        self.Ranges.update_params(range_)
        self.redraw_2d_plot()
        self.draw()

    def change_log_status(self, event):
        self.apply_log_status = not self.apply_log_status
        if self.apply_log_status:
            self.y = self.apply_log(self.data)
        else:
            self.y = self.data
        self.Ranges.change_regime()
        self.redraw_2d_plot()
        self.draw()

    def reset_parameters(self, event):
        self.apply_log_status = False
        self.params_2d = {}
        self.redraw_2d_plot()
        self.draw()


# class Axes1D(object):
#     def __init__(self, ax, parent):
#         self.ax = ax
#         self.parent = parent
#         self.x = []
#         self.y = []
#         self.plot_obj, = self.ax.plot(self.x, self.y)
#         self.title = ''
#         self.plot_list = []
#
#     def update_plot(self, y, x):
#         self.y = y
#         self.x = x or list(range(len(y)))
#         self.plot_obj.set_xdata(self.x)
#         self.plot_obj.set_ydata(self.y)
#         self.ax.relim()  # Recalculate limits
#         self.ax.autoscale_view(True, True, True)
#
#
# class Axes2D(object):
#     def __init__(self, ax, parent=None):
#         self.ax = ax
#         self.parent = parent


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
        self.ax_cut = self.fig.add_subplot(111)
        self.x, self.y, self.data = [], [], []
        self.cut_y, self.cut_x = [], []
        self.cut_plot, = self.ax_cut.plot(self.cut_x, self.cut_y)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def update_cut_plot(self):
        frame = self.plot2d_canvas.y
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


class SnaptoCursor(object):
    """
    Like Cursor but the crosshair snaps to the nearest x,y point
    For simplicity, I'm assuming x is sorted
    """

    def __init__(self, plt_obj, x, y):
        self.plt_obj = plt_obj
        self.ax = plt_obj.axes
        self.lx = self.ax.axhline(color='k')  # the horiz line
        self.ly = self.ax.axvline(color='k')  # the vert line
        self.x = x
        self.y = y
        # text location in axes coords
        self.txt = self.ax.text(0.7, 0.9, '', transform=self.ax.transAxes)

    def mouse_move(self, event):
        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata

        indx = np.searchsorted(self.x, [x])[0]
        x = self.x[indx]
        y = self.y[indx]
        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)

        self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
        print('x=%1.2f, y=%1.2f' % (x, y))
        self.plt_obj.draw()

    def key_press(self, event):
        if not event.inaxes:
            print('Press away')
            return

        # update the line positions
        print('Pressed')
        self.lx.color = 'red'
        self.ly.color = 'red'

    def key_release(self, event):
        if not event.inaxes:
            return

        # update the line positions
        print('Released')
        self.lx.color = 'black'
        self.ly.color = 'black'