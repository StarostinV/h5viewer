import numpy as np
import h5py
from datetime import datetime as dt

f = h5py.File('test.h5', 'w')
group_1 = f.create_group('first group')
f.create_dataset('data1', data=np.ones(10))
group_1.create_dataset('data0', data=np.zeros(10))
d1 = group_1.create_dataset('data_s', data=[b'1', b'2'])
# f['d1'] = d1
f.close()
