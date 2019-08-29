from PyQt5.QtWidgets import QTableView
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QSizePolicy, QHeaderView
from PyQt5.QtCore import Qt
import numpy as np
import h5py

_TYPE_DICT = {h5py.Dataset: 'Dataset', h5py.Group: 'Group',
              h5py.File: 'File'}


class DescriptiveLabel(QTableView):
    def __init__(self):
        super(QTableView, self).__init__()
        self.model_ = QStandardItemModel()
        self.setModel(self.model_)
        self.model().setRowCount(0)
        self.setSizePolicy(QSizePolicy.Expanding,
                           QSizePolicy.Fixed)
        self.setMaximumHeight(120)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def update_table(self, obj):
        self.model().removeRows(0, self.model().rowCount())
        self.model().removeColumns(0, self.model().columnCount())
        name = self._get_label(obj)
        attrs_keys = list(obj.attrs.keys())
        if len(attrs_keys) == 0:
            self.model().appendRow(QStandardItem(name))
        else:
            first_row = [QStandardItem(attr_name) for attr_name in attrs_keys]
            self.model().appendRow([QStandardItem(name)] + first_row)
            second_row = []
            for k in attrs_keys:
                if isinstance(obj.attrs[k], np.ndarray):
                    second_row.append(QStandardItem(f'Array of shape {obj.attrs[k].shape}'))
                elif isinstance(obj.attrs[k], h5py.Reference):
                    second_row.append(QStandardItem('Reference'))
                elif isinstance(obj.attrs[k], h5py.Reference):
                    second_row.append(QStandardItem('Byte array'))
                else:
                    try:
                        second_row.append(QStandardItem(obj.attrs[k]))
                    except TypeError:
                        second_row.append(QStandardItem(type(obj.attrs[k])))
            self.model().appendRow([QStandardItem('Attrs')] + second_row)

    @staticmethod
    def _get_label(obj):
        type_ = _TYPE_DICT.get(type(obj), '')
        return type_
