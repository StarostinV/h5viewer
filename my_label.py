from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont


class DescriptiveLabel(QLabel):
    def __init__(self):
        super(QLabel, self).__init__('')
        self.setFont(QFont("Times", 9))
        self.adjustSize()
