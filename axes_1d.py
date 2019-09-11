from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QMenu


class Axes1D(object):
    def __init__(self, ax, parent):
        self.ax = ax
        self.parent = parent
        self.x = []
        self.y = []
        self.plot_obj, = self.ax.plot(self.x, self.y)
        self.title = ''
        self.plot_list = []

    def update_plot(self, obj, file):
        self.y = obj[()]
        self.x = obj.attrs.get('x_axis', None)
        try:
            self.x = file[obj.attrs['x_axis']][()]
            assert len(self.x) == len(self.y)
        except (AssertionError, TypeError, KeyError):
            self.x = range(len(self.y))

        self.plot_obj.set_xdata(self.x)
        self.plot_obj.set_ydata(self.y)
        self.ax.relim()  # Recalculate limits
        self.ax.autoscale_view(True, True, True)
        self.parent.draw()

    def context_menu(self, event):
        menu = QMenu()
        y = self.parent.parent().height()
        position = self.parent.mapFromParent(QPoint(event.x, y - event.y))
        reset_graph_action = menu.addAction('Redraw graph')
        reset_graph_action.triggered.connect(self.redraw_graph)

        menu.exec_(self.parent.parent().mapToGlobal(position))

    def redraw_graph(self):
        self.ax.cla()
        self.plot_obj = self.ax.plot(self.x, self.y)[0]
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)
        self.parent.draw()
