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
        pass
