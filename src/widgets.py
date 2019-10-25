
from __future__ import division
import time
from collections import OrderedDict
from copy import deepcopy
import pkg_resources
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_SHININESS
from pyqtgraph.Qt import QtCore,QtGui,QtOpenGL
import pyqtgraph as pg
from objloader import WFObject
import numpy as np
import time
import pdb
from matplotlib.backends.qt_compat import QtWidgets

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    from OpenGL.GLU import *
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None,"OpenGL Error",
                               "PyOpenGL must be installed to run this program.")

pyqtSignal = QtCore.pyqtSignal

resource_package = __name__ 

def get_source_name(file_path_name):
    return pkg_resources.resource_filename(resource_package,file_path_name)  

def move_model(x,y,z):
    def process_draw(some_draw_func):
        def new_draw_func():
            glPushMatrix()
            glTranslatef(x,y,z)
            some_draw_func()
            glPopMatrix()
        return new_draw_func
    return process_draw

def rotate_model(roll,pitch, yaw):
    """3-1-2 rotation transform"""
    def process_draw(some_draw_func):
        def new_draw_func():
            glPushMatrix()
            glRotatef(pitch,0,1,0)
            glRotatef(roll,1,0,0)
            glRotatef(yaw,0,0,1)
            some_draw_func()
            glPopMatrix()
        return new_draw_func
    return process_draw

class Marker(QtGui.QComboBox):
    sigMarkerChanged = pyqtSignal(object)
    def __init__(self, marker=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marker = marker
        self._markerdict = OrderedDict([('None',None), ('☐','s'), ('▽','t'), ('○','o'), ('+','+')])
        for key in self._markerdict.keys():
            self.addItem(key)
        self.setCurrentIndex(list(self._markerdict.values()).index(self.marker))
        self.currentIndexChanged.connect(self.callback_markerChanged)
    
    def callback_markerChanged(self):
        self.marker = list(self._markerdict.values())[self.currentIndex()]
        self.sigMarkerChanged.emit(self)
    
    def set_marker(self, marker=None):
        if marker in self._markerdict.values():
            self.marker = marker
            self.setCurrentIndex(list(self._markerdict.values()).index(marker))
        else:
            raise TypeError('marker not in the MarkerList')

class PropertyLabel(QtGui.QLabel):
    sigPropertyChanged = pyqtSignal(bool)
    def __init__(self, item_id, mainwindow, *args, **kwargs):
        self.id = item_id
        self.mainwindow = mainwindow
        self.markdict = OrderedDict([(None,'None'), ('s','☐'), ('t','▽'), ('o','○'), ('+','+')])
        super().__init__(*args, **kwargs)
        
    def mouseDoubleClickEvent(self, event, *args, **kwargs):
        print('label double clicked')
        self.win = CurveModifyWin(self.id, self.mainwindow)
        self.win.sigCurveChanged.connect(self.callback_sigchanged)
        self.win.show()
        QtGui.QApplication.processEvents()
        time.sleep(0.2)
        
    def update_tab_text(self):
        curve = self.mainwindow.data_plotting[self.id][2]
        marker = curve.opts['symbol']
        color = curve.opts['pen']
        color_text = '#{0[0]:02x}{0[1]:02x}{0[2]:02x}'.format(color)
        self.setText("<font color='{0}'>{1}</font> {2}".format(color_text,'▇▇',self.markdict[marker]))
    
    def callback_sigchanged(self):
        self.sigPropertyChanged.emit(True)

class ThreadQDialog(QtCore.QThread):
    def __init__(self,  loading_widget,  parent=None,  *args,  **kwargs):
        super(ThreadQDialog, self).__init__(parent,  *args,  **kwargs)
        self.dialog = QtGui.QMessageBox()
        self.dialog.setWindowTitle('Info:Loading')
        self.dialog.setModal(True)
        self.dialog.hide()
        self.loading_widget = loading_widget
        self.loading_widget.loadFinished.connect(self.callback_close)
    
    def run(self):
        self.dialog.setText('Loading...')
        self.dialog.setStyleSheet('QLabel{min-width: 100px;}')
        self.dialog.show()
        
    def callback_close(self, isFinished):
        if isFinished:
            self.dialog.close()
            return

class ColorPushButton(pg.ColorButton):
    def __init__(self, id, *args, **kwargs):
        self.id = id
        super(ColorPushButton, self).__init__(*args,  **kwargs)

class Checkbox(QtGui.QCheckBox):
    sigStateChanged = pyqtSignal(object) 
    def __init__(self, id, *args, **kwargs):
        self.id = id
        super(Checkbox, self).__init__(*args, **kwargs)
        self.stateChanged.connect(self.callback_stateChanged)
    
    def callback_stateChanged(self):
        self.sigStateChanged.emit(self)
        
class LineEdit(QtGui.QLineEdit):
    sigTextChanged = pyqtSignal(bool)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() == QtCore.Qt.Key_Enter:
            self.sigTextChanged.emit(True)
        else:
            QtGui.QLineEdit.keyPressEvent(self, event, *args, **kwargs)


class TabBar(QtWidgets.QTabBar):
    def __init__(self, colors, parent=None):
        super(TabBar, self).__init__(parent)
        self.mColors = colors

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            if opt.text in self.mColors:
                opt.palette.setColor(
                    QtGui.QPalette.Button, self.mColors[opt.text]
                )
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        d = {
            "custom": QtGui.QColor("#e7e7e7"),
            "other": QtGui.QColor("#f0f0f0"),
            "POS Sales": QtGui.QColor("#90EE90"),
            "Cash Sales": QtGui.QColor("pink"),
            "invoice": QtGui.QColor("#800080"),
        }
        self.setTabBar(TabBar(d))

class CurveModifyWin(QtGui.QMainWindow):
    sigCurveChanged = pyqtSignal(bool)
    def __init__(self, item_id, mainwindow, *args, **kargs):
        self.id = item_id
        self.mainwindow = mainwindow
        super().__init__(*args, **kargs)
        self.resize(QtCore.QSize(300, 200))
        self.properties_table = QtGui.QTableWidget()
#         self.setCentralWidget(self.properties_table)
        self.properties_table.setSortingEnabled(False)
        self.properties_table.horizontalHeader().setStretchLastSection(True)
        self.properties_table.resizeColumnsToContents()
        self.properties_table.setColumnCount(2)
        self.properties_table.setColumnWidth(0, 120)
        self.properties_table.setColumnWidth(1, 50)
        self.properties_table.setHorizontalHeaderLabels(['Property', 'value'])
        # first row --- color
        self.properties_table.insertRow(0)
        self.properties_table.setCellWidget(0, 0, QtGui.QLabel('Color'))
        self.curve = mainwindow.data_plotting[self.id][2]
        self.btn = ColorPushButton(self.id, self.properties_table, self.curve.opts['pen'])
        self.properties_table.setCellWidget(0, 1, self.btn)
        # second row --- symbol
        self.properties_table.insertRow(1)
        self.properties_table.setCellWidget(1, 0, QtGui.QLabel('Marker'))
        self.mkr = Marker(self.curve.opts['symbol'])
        self.properties_table.setCellWidget(1, 1, self.mkr)
        # third row --- symbol size
        self.properties_table.insertRow(2)
        self.properties_table.setCellWidget(2, 0, QtGui.QLabel('Marker Size'))
        print('symbolSize:', str(self.curve.opts['symbolSize']))
        self.ln = LineEdit(str(self.curve.opts['symbolSize']))
        self.properties_table.setCellWidget(2, 1, self.ln)
        w = QtGui.QWidget()
        self.vlayout = QtGui.QVBoxLayout()
        self.hlayout = QtGui.QHBoxLayout()
        self.setCentralWidget(w)
        self.centralWidget().setLayout(self.vlayout)
        self.vlayout.addWidget(self.properties_table)
        self.vlayout.addLayout(self.hlayout)
        self.cancel_btn = QtGui.QPushButton('Cancel')
        self.ok_btn = QtGui.QPushButton('OK')
        self.cancel_btn.clicked.connect(self.callback_cancel_clicked)
        self.ok_btn.clicked.connect(self.callback_properties_changed)
        self.hlayout.addWidget(self.cancel_btn)
        self.hlayout.addWidget(self.ok_btn)
    
    def closeEvent(self, *args, **kwargs):
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)
    
    def callback_cancel_clicked(self):
        self.close()
    
    def callback_properties_changed(self, *args, **kwargs):
        self.curve.opts['symbol'] = self.mkr.marker
        self.curve.opts['pen'] = self.btn.color()
        try:
            self.curve.opts['symbolSize'] = int(self.ln.text())
            print('set size finished to ', self.curve.opts['symbolSize'])
        except:
            d = QtGui.QDialog('Input Error')
            b1 = QtGui.QPushButton("ok",d)
            d.setWindowModality(QtCore.Qt.ApplicationModal)
            d.exec_()
        # update graph and items in plot list pane
        self.sigCurveChanged.emit(True)
            

class InfoWin(QtGui.QMainWindow):
    closed = pyqtSignal(bool)
    
    def __init__(self, info_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(QtCore.QSize(500,500))
        self.info_table = QtGui.QTableWidget()
        self.setCentralWidget(self.info_table)
        self.info_table.setSortingEnabled(False)
        self.info_table.horizontalHeader().setStretchLastSection(True)
        self.info_table.resizeColumnsToContents()
        self.info_table.setColumnCount(2)
        self.info_table.setColumnWidth(0, 120)
        self.info_table.setColumnWidth(1, 50)
        self.info_table.setHorizontalHeaderLabels(['Name', 'value'])
        index = 0
        for name, value in info_data.items():
            self.info_table.insertRow(index)
            self.info_table.setCellWidget(index, 0, QtGui.QLabel(name))
            self.info_table.setCellWidget(index, 1, QtGui.QLabel(str(value)))
            index += 1
#             self.info_table.setCellWidget(index, 0, QtGui.QLabel(des))
    
    def closeEvent(self, *args, **kwargs):
        self.closed.emit(True)
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)

class ParamsWin(QtGui.QMainWindow):
    closed = pyqtSignal(bool)
    def __init__(self, params_data, changed_params_data, *args, **kwargs):
        self.params_data = params_data
        self.params_data_show = list(self.params_data.keys())
        self.changed_params_data = changed_params_data
        super().__init__(*args, **kwargs)
        self.resize(QtCore.QSize(500,500))
        self.params_table = QtGui.QTableWidget()
        self.choose_item_lineEdit = QtGui.QLineEdit(self)
        self.choose_item_lineEdit.setPlaceholderText('filter by data name')
        self.choose_item_lineEdit.textChanged.connect(self.callback_filter)
        self.btn_changed_filter = QtGui.QPushButton('Changed')
        self.btn_changed_filter.clicked.connect(self.btn_changed_filter_clicked) 
        w = QtGui.QWidget()
        self.vlayout = QtGui.QVBoxLayout(w)
        self.hlayout = QtGui.QHBoxLayout(self)
        self.setCentralWidget(w)
        self.centralWidget().setLayout(self.vlayout)
        self.vlayout.addWidget(self.params_table)
        self.vlayout.addLayout(self.hlayout)
        self.hlayout.addWidget(self.btn_changed_filter)
        self.hlayout.addWidget(self.choose_item_lineEdit)
        self.params_table.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | 
                                                     QtGui.QAbstractItemView.SelectedClicked)
        self.params_table.setSortingEnabled(False)
        self.params_table.horizontalHeader().setStretchLastSection(True)
        self.params_table.resizeColumnsToContents()
        self.params_table.setColumnCount(2)
        self.params_table.setColumnWidth(0, 120)
        self.params_table.setColumnWidth(1, 50)
        self.params_table.setHorizontalHeaderLabels(['Name', 'value'])
        self.show_all_params = True
        self.filtertext = ''
        self.update_table()
        
    def closeEvent(self, *args, **kwargs):
        self.closed.emit(True)
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)
    
    def filter(self):
        if self.show_all_params:
            self.params_data_show = list(self.params_data.keys())
        else:
            self.params_data_show = deepcopy(self.changed_params_data)
        names_to_be_removed = []
        for name in self.params_data_show:
            if self.filtertext not in name:
                names_to_be_removed.append(name)
        for name in names_to_be_removed:
            self.params_data_show.remove(name)
    
    def callback_filter(self, filtertext):
        self.filtertext = str(filtertext)
        self.filter()
        self.update_table()
        
    def btn_changed_filter_clicked(self):
        self.show_all_params  = not self.show_all_params
        if self.show_all_params:
            text = 'Changed'
        else:
            text = 'All'
        self.btn_changed_filter.setText(text)
        self.filter()
        self.update_table()
    
    def update_table(self):
        self.params_table.setRowCount(0)
        index = 0
        for name, value in self.params_data.items():
            if name in self.params_data_show:
                self.params_table.insertRow(index)
                if name in self.changed_params_data:
                    name_str = "<font color='red'>%s</font>"%(name)
                    value_str = "<font color='red'>%s</font>"%(str(value))
                else:
                    name_str = name
                    value_str = str(value)
                name_lbl = QtGui.QLabel(name_str)
                value_lbl = QtGui.QLabel(value_str)
                self.params_table.setCellWidget(index, 0, name_lbl)
                self.params_table.setCellWidget(index, 1, value_lbl)
                index += 1
                
class AnalysisGraphWin(QtGui.QMainWindow):
    sigChecked = pyqtSignal(tuple)
    sigUnchecked = pyqtSignal(str)
    closed = pyqtSignal(bool)
    def __init__(self, mainwindow, *args, **kwargs):
        self.mainwindow = mainwindow
        # gui
        self.graph_predefined_list = ['XY_Estimation',
                                       'Altitude Estimate',
                                       'Roll Angle',
                                       'Pitch Angle',
                                       'Yaw Angle',
                                       'Roll Angle Rate',
                                       'Pitch Angle Rate',
                                       'Yaw Angle Rate',
                                       'Local Position X',
                                       'Local Position Y',
                                       'Local Position Z',
                                       'Velocity',
                                       'Manual Control Input',
                                       'Actuator Controls 0',
                                       'Actuation Outputs(Main)',
                                       'Actuation Outputs(Aux)',
                                       'Magnetic field strength',
                                       'Distance Sensor',
                                       'GPS Uncertainty',
                                       'GPS noise and jamming',
                                       'CPU & RAM',
                                       'Power']
        super().__init__(*args,**kwargs)
        self.setFixedSize(QtCore.QSize(300, 660))
        self.graph_table = QtGui.QTableWidget(self)
        self.graph_table.setColumnCount(2)
        self.graph_table.setColumnWidth(0, 200)
        self.graph_table.setColumnWidth(1, 40)
        for index, item in enumerate(self.graph_predefined_list):
            self.graph_table.insertRow(index)
            lbl = QtGui.QLabel(item)
            lbl.mouseDoubleClickEvent = self.callback_double_clicked(item)
            self.graph_table.setCellWidget(index, 0, lbl)
            chk = Checkbox(item)
            if item in self.mainwindow.analysis_graph_list:
                chk.setChecked(True)
            chk.sigStateChanged.connect(self.callback_check_state_changed)
            self.graph_table.setCellWidget(index, 1, chk)
        self.clear_btn = QtGui.QPushButton('Clear all')
        self.clear_btn.clicked.connect(self.callback_clear)
        #
        w = QtGui.QWidget()
        self.vlayout = QtGui.QVBoxLayout(w)
        self.setCentralWidget(w)
        self.centralWidget().setLayout(self.vlayout)
        self.vlayout.addWidget(self.graph_table)
        self.vlayout.addWidget(self.clear_btn)    
    
    def callback_double_clicked(self, lbl_text):
        def func(*args, **kwargs):
            if lbl_text in self.mainwindow.analysis_graph_list:
                ind = list(self.mainwindow.analysis_graph_list.keys()).index(lbl_text)
                self.mainwindow.default_tab.setCurrentIndex(ind + 3)
        return func
    
    def callback_item_clicked(self):
        pass
    
    def callback_clear(self):
        for index in range(self.graph_table.columnCount()):
            self.graph_table.item(index, 1).setChecked(False)
    
    def callback_check_state_changed(self, chk):
        graph_name = chk.id
        if not chk.isChecked():
            self.sigUnchecked.emit(graph_name)
        else:
            if graph_name == 'XY_Estimation':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_local_position')
                x = self.mainwindow.log_data_list[data_index].data['x']
                y = self.mainwindow.log_data_list[data_index].data['y']
                data = ['2d',(x,y, 'XY_Estimation')]
            elif graph_name == 'Altitude Estimate':
                data = ['t']
                # gps
                try:
                    data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_gps_position')
                    gps_alt = self.mainwindow.log_data_list[data_index].data['alt'] * 0.001
                    gps_t = self.mainwindow.log_data_list[data_index].data['timestamp']
                    data.append((gps_t, gps_alt, 'GPS Altitude'))
                except:
                    print('No vehicle_gps_position')
                
                # barometer
                try:
                    data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_air_data')
                    bra_alt = self.mainwindow.log_data_list[data_index].data['baro_alt_meter']
                    bra_t = self.mainwindow.log_data_list[data_index].data['timestamp']
                    data.append((bra_t, bra_alt, 'Barometer Altitude'))
                except:
                    print('No vehicle_air_data')
                # Fused 
                try:
                    data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_global_position')
                    fused_alt = self.mainwindow.log_data_list[data_index].data['alt']
                    fused_t = self.mainwindow.log_data_list[data_index].data['timestamp']
                    data.append((fused_t, fused_alt, 'Fused Altitude'))
                except:
                    print('No vehicle_global_position')
                    
                # setpoint
                try:
                    data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_setpoint_triplet')
                    current_alt = self.mainwindow.log_data_list[data_index].data['current.alt']
                    current_t = self.mainwindow.log_data_list[data_index].data['timestamp']
                    data.append((current_t, current_alt, 'Altitude Setpoint'))
                except:
                    print('No vehicle_setpoint_triplet')
                
                # actuator_controls_0
                try:
                    data_index = list(list(self.mainwindow.data_dict.keys())).index('actuator_controls_0')
                    thrust_v = self.mainwindow.log_data_list[data_index].data['control[3]'] * 100
                    thrust_t = self.mainwindow.log_data_list[data_index].data['timestamp']
                    data.append((thrust_t, thrust_v, 'Thust [0, 100]'))
                except:
                    print('No actuator_controls_0')
                
            elif graph_name in ['Roll Angle',
                                'Pitch Angle',
                                'Yaw Angle']:
                data_index_dict = {'Roll Angle':0,
                                   'Pitch Angle':1,
                                   'Yaw Angle':2}
                data_index = data_index_dict[graph_name]
                angle = [angles[data_index] for angles in self.mainwindow.attitude_history]
                angle_t = self.mainwindow.time_stamp_attitude
                angle_setpoint = [angles[data_index] for angles in self.mainwindow.attitude_setpoint_history]
                angle_setpoint_t = self.mainwindow.time_stamp_attitude_setpoint
                data = ['t', (angle_t, angle, graph_name + ' Estimated'), 
                        (angle_setpoint_t, angle_setpoint, graph_name + ' Setpoint')]
                
            elif graph_name in ['Roll Angle Rate',
                                'Pitch Angle Rate',
                                'Yaw Angle Rate',]:
                data_index_dict = {'Roll Angle Rate':['rollspeed', 'roll'], 
                                   'Pitch Angle Rate':['pitchspeed', 'pitch'],
                                   'Yaw Angle Rate':['yawspeed', 'yaw']}
                data_name = data_index_dict[graph_name]
                data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_attitude')
                angle_rate = np.rad2deg(self.mainwindow.log_data_list[data_index].data[data_name[0]])
                t_angle_rate = self.mainwindow.log_data_list[data_index].data['timestamp']
                data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_rates_setpoint')
                angle_rate_setpoint = np.rad2deg(self.mainwindow.log_data_list[data_index].data[data_name[1]])
                t_angle_rate_setpoint = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t', (t_angle_rate, angle_rate, graph_name + ' Estimated'), 
                            (t_angle_rate_setpoint, angle_rate_setpoint, graph_name + ' Setpoint')]
                
            elif graph_name in ['Local Position X',
                                'Local Position Y',
                                'Local Position Z']:
                data_index_dict = {'Local Position X':'x',
                                    'Local Position Y':'y',
                                    'Local Position Z':'z'}
                data_name = data_index_dict[graph_name]
                data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_local_position')
                x = self.mainwindow.log_data_list[data_index].data[data_name]
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t', (t, x, graph_name + ' Estimated')]
                try:
                    data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_local_position_setpoint')
                    x_setpoint = self.mainwindow.log_data_list[data_index].data[data_name]
                    t_x_setpoint = self.mainwindow.log_data_list[data_index].data['timestamp']
                    data.append((t_x_setpoint, x_setpoint, graph_name + ' Setpoint'))
                except:
                    pass
                
            elif graph_name == 'Velocity':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_local_position')
                vx = self.mainwindow.log_data_list[data_index].data['vx']
                vy = self.mainwindow.log_data_list[data_index].data['vy']
                vz = self.mainwindow.log_data_list[data_index].data['vz']
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t', 
                        (t, vx, 'VX'),
                        (t, vy, 'VY'), 
                        (t, vz, 'VZ')]
                try:
                    data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_local_position_setpoint')
                    vx_setpoint = self.mainwindow.log_data_list[data_index].data['vx']
                    vy_setpoint = self.mainwindow.log_data_list[data_index].data['vy']
                    vz_setpoint = self.mainwindow.log_data_list[data_index].data['vz']
                    t_setpoint = self.mainwindow.log_data_list[data_index].data['timestamp'] 
                    data.extend([(t_setpoint, vx_setpoint, 'VX setpoint'),
                            (t_setpoint, vy_setpoint, 'VY setpoint'),
                            (t_setpoint, vz_setpoint, 'VZ setpoint')])
                except:
                    pass
                
            elif graph_name == 'Manual Control Input':
                # not compatible to other format
                data_index = list(list(self.mainwindow.data_dict.keys())).index('manual_control_setpoint')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t']
                data_name_dict = {'y':'Y / Roll', 'x':'X / Pitch', 'r':'Yaw', 
                                  'z': 'Throttle [0, 1]', 'mode_slot': 'Flight Mode', 
                                  'aux1': 'Aux1', 'aux2':'Aux2',
                                  'kill_switch':'Kill Switch'}
                for name, label in data_name_dict.items():
                    if name == 'mode_slot':
                        data.append((t, self.mainwindow.log_data_list[data_index].data[name]/6, label))
                    elif name == 'kill_switch':
                        data.append((t, (self.mainwindow.log_data_list[data_index].data[name] == 1).astype(np.uint32), label))
                    else:
                        data.append((t, self.mainwindow.log_data_list[data_index].data[name], label))
            elif graph_name == 'Actuator Controls 0':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('actuator_controls_0')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t']
                data_name_list = ['Roll', 'Pitch', 'Yaw', 'Thrust']
                for i in range(4):
                    name = 'control[%d]' % (i)
                    data.append((t, self.mainwindow.log_data_list[data_index].data[name]), 
                                data_name_list[i])
                
            elif graph_name == 'Actuation Outputs(Main)':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('actuator_outputs')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t']
                for i in range(8):
                    name = 'control[%d]' % (i)
                    data.append((t, self.mainwindow.log_data_list[name], name))
                    
            elif graph_name == 'Actuation Outputs(Aux)':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('actuator_outputs_1')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                num_outputs = np.max(self.mainwindow.log_data_list[data_index].data['noutputs'])
                data = ['t']
                for i in range(num_outputs):
                    name = 'control[%d]' % (i)
                    data.append((t, self.mainwindow.log_data_list[name], name))
            elif graph_name == 'Magnetic field strength':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('sensor_combined')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t']
                for i in range(3):
                    name = 'magnetometer_ga[%d]'%(i)
                    data.append((t, self.mainwindow.log_data_list[name], name))
                    
            elif graph_name == 'Distance Sensor':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('sensor_combined')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                current_distance = self.mainwindow.log_data_list[data_index].data['current_distance']
                covariance = self.mainwindow.log_data_list[data_index].data['covariance']
                data = ['t', (t, current_distance, 'Distance'), (t, covariance, 'Covariance')]
            elif graph_name == 'GPS Uncertainty':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_gps_position')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t']
                data_dict = {'eph':'Horizontal position accuracy [m]', 
                             'epv':'Vertical position accuracy [m]',
                             'satellites_used': 'Num Satellites used',
                             'fix_type':'GPS fix'}
                for index, label in data_dict.items():
                    data.append((t, self.mainwindow.log_data_list[data_index].data['eph'], label))
            elif graph_name == 'GPS noise and jamming':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('vehicle_gps_position')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                noise_per_ms = self.mainwindow.log_data_list[data_index].data['noise_per_ms']
                jamming_indicator = self.mainwindow.log_data_list[data_index].data['jamming_indicator']
                data = ['t', (t, noise_per_ms, 'Noise per ms'), (t, jamming_indicator, 'Jamming Indicator')]
            elif graph_name == 'CPU & RAM':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('cpuload')
                x1 = self.mainwindow.log_data_list[data_index].data['load']
                x2 = self.mainwindow.log_data_list[data_index].data['ram_usage']
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                data = ['t', (t, x1, 'CPU'), (t, x2, 'Ram usage')]
            elif graph_name == 'Power':
                data_index = list(list(self.mainwindow.data_dict.keys())).index('battery_status')
                t = self.mainwindow.log_data_list[data_index].data['timestamp']
                v = self.mainwindow.log_data_list[data_index].data['voltage_v']
                data = ['t', (t, v, 'Votage(V)')]
            
            self.sigChecked.emit((graph_name, data))
            
    def closeEvent(self, *args, **kwargs):
        self.closed.emit(True)
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)
            
class HelpWin(QtGui.QMainWindow):
    closed = pyqtSignal(bool)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(QtCore.QSize(600, 400))
        w = QtGui.QWidget()
        self.setCentralWidget(w)
        vlayout = QtGui.QVBoxLayout()
        w.setLayout(vlayout)
        self.htmlView = QtWidgets.QTextBrowser(self)
        font = QtGui.QFont()
        font.setFamily('Arial')
        self.htmlView.setReadOnly(True)
        self.htmlView.setFont(font)
        self.htmlView.setOpenExternalLinks(True)
        self.htmlView.setObjectName('Help information')
        html_help_path = get_source_name('docs/help.html')
        ret = self.htmlView.setSource(QtCore.QUrl(html_help_path))
        print('load result:', ret)
#         self.htmlView.append(ret)
        vlayout.addWidget(self.htmlView)
    
    def closeEvent(self, *args, **kwargs):
        self.closed.emit(True)
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)

class QuadrotorWin(QtGui.QMainWindow):
    closed = pyqtSignal(bool)
    
    def __init__(self,*args,**kwargs):
        super(QuadrotorWin,self).__init__(*args,**kwargs)
        self.toolBar = self.addToolBar('showSetting')
        self.trace_show = QtGui.QAction(QtGui.QIcon(get_source_name('icons/trace.gif')),
                                        'show trace',
                                        self)
        self.trace_show.triggered.connect(self.callback_show_trace)
        self.trace_showed = False
        self.vector_show = QtGui.QAction(QtGui.QIcon(get_source_name('icons/rotor_vector.gif')),
                                         'show rotation speed vector',self)
        self.vector_show.triggered.connect(self.callback_show_vector)
        self.vector_showed = False
        self.toolBar.addAction(self.trace_show)
        self.toolBar.addAction(self.vector_show)
        self.quadrotor_win_main_widget = QtGui.QWidget(self)
        self.quadrotor_win_main_layout = QtGui.QHBoxLayout() 
        self.quadrotor_win_main_widget.setLayout(self.quadrotor_win_main_layout)
        self.quadrotor_widget = QuadrotorWidget(self.quadrotor_win_main_widget)
        self.quadrotor_win_main_layout.addWidget(self.quadrotor_widget)
        self.setCentralWidget(self.quadrotor_win_main_widget)
        self.setWindowTitle("pyFlightAnalysis  Trace plot")
        
    def closeEvent(self, *args, **kwargs):
        self.closed.emit(True)
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)
    
    def callback_show_trace(self):
        if self.trace_showed:
            self.trace_show.setIcon(QtGui.QIcon(get_source_name('icons/trace.gif')))
            self.quadrotor_widget.trace_visible = False
        else:
            self.trace_show.setIcon(QtGui.QIcon(get_source_name("icons/trace_pressed.gif")))
            self.quadrotor_widget.trace_visible = True
        self.trace_showed = not self.trace_showed
        
    def callback_show_vector(self):
        if self.vector_showed:
            self.vector_show.setIcon(QtGui.QIcon(get_source_name("icons/rotor_vector.gif")))
            self.quadrotor_widget.vector_visible = False
        else:
            self.vector_show.setIcon(QtGui.QIcon(get_source_name("icons/rotor_vector_pressed.gif")))
            self.quadrotor_widget.vector_visible = True
        self.vector_showed = not self.vector_showed
    
    def callback_update_quadrotor_pos(self,state):
        self.quadrotor_widget.update_state(state)
    
    def callback_quadrotor_state_reset(self):
        self.quadrotor_widget.reset()

class QuadrotorWidget(QtOpenGL.QGLWidget):
    """
    Quadrotor 3D viewer
    """
    loadFinished = pyqtSignal(bool)
    
    def __init__(self,*args,**kwargs):
        super(QuadrotorWidget,self).__init__(*args,**kwargs)
        
        self.object = 0
        
        self.lastPos = QtCore.QPoint()
        
        self.trolltechGreen = QtGui.QColor.fromCmykF(0.40,0.0,1.0,0.0)
        self.trolltechPurple = QtGui.QColor.fromCmykF(0.39,0.39,0.0,0.0)
        
        # window parameters
        self.window = 0
        ## window size in pixels. width and height
        self.window_size = (800,800)
        self.window_size_minimum = (400,400)
        ## perspective
        self.fovy = 60
        self.near = 0.01
        self.far = 2000
        
        # axes parameters
        self.tip = 0
        self.ORG = [0,0,0]
        self.AXES = [[2,0,0],[0,2,0],[0,0,2]]
        self.AXES_NORM = [[-1,0,0],[0,-1,0],[0,0,-1]]
        self.mat_diffuse = (1.0,0.0,0.0,0.0)
        
        # material and light parameters
        self.mat_specular = (0.2,0.2,0.2,0.2)
        self.mat_shininess = 0.2
        self.light_position = (10.0,10.0,10.0,0.0)
        self.white_light = (1.0,1.0,1.0,1.0)
        self.lmodel_ambient = (0.1,0.1,0.1,1.0)
        
        # load model
        self.drone_base = WFObject()
        self.drone_base.loadFile(get_source_name("models/drone_base.obj"))
        self.drone_propeller1 = WFObject()
        self.drone_propeller1.loadFile(get_source_name("models/drone_propeller1.obj"))
        self.drone_propeller2 = WFObject()
        self.drone_propeller2.loadFile(get_source_name("models/drone_propeller2.obj"))
        self.drone_propeller3 = WFObject()
        self.drone_propeller3.loadFile(get_source_name("models/drone_propeller3.obj"))
        self.drone_propeller4 = WFObject()
        self.drone_propeller4.loadFile(get_source_name("models/drone_propeller4.obj"))
        
        # Base Plane Size
        self.floor_size = (-100,100)
        self.floor_grid_num = 60
        self.floor_color = (0.3,0.3,0.3)
        
        # rotation vector
        self.vector_radius = 0.4
        self.vector_radius_color = [0.8,0.0,0.0]
        
        # quadrotor state set
        self.drone_position = [0,0,0]
        ## 312 yaw-roll-pitch
        self.drone_angles = [0,0,0] 
        ## drone_motor_speed
        self.drone_motors_speed = [100.0,200.0,250.0,10.0]
        
        # info screen
        self.info_screen = None
        self.info_screen_size = (150,200)
        ## gap between the left border/top border and info screen  
        self.info_screen_gap = (10,10)
        ## view size
        self.info_screen_L = 10
        ## char size
        self.char_height = 4
        self.char_gap = 2
        
        # interaction parameters
        self.mouse_state = {'button':None,'position':[0,0]}
        self.scene_movement = [0,0]
        self.movement_ratio = 0.1
        self.rotation_ratio = 0.1
        self.scale_ratio = 0.01
        self.camera_azimuth = 45
        self.camera_attitude = 45
        ## distance between eye and origin
        self.eye_R = 180
        self.camera_view_center = [0,0,0]
        self.follow = True
        self.trace_visible = False
        self.vector_visible = False
        self.drone_position_history = []
        ## drone trace color
        self.drone_trace_color = [1,0,0]
        
        # GUI
        glutInit()
        
        self.animationTimer = QtCore.QTimer()
        self.animationTimer.setSingleShot(False)
        self.animationTimer.timeout.connect(self.animate)
        self.animationTimer.start(25)
        
    
    def minimumSizeHint(self):
        return QtCore.QSize(*self.window_size_minimum)

    def sizeHint(self):
        return QtCore.QSize(*self.window_size)

    def initializeGL(self):
        glClearColor(0.0,0.0,0.0,0.0)
        glShadeModel(GL_SMOOTH)
        w,h = self.window_size
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60,w/h,self.near,self.far)
        
        # Isolate the light position
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMaterialfv(GL_FRONT,GL_AMBIENT_AND_DIFFUSE,self.mat_diffuse)
        glMaterialfv(GL_FRONT,GL_SPECULAR,self.mat_specular)
        glMaterialfv(GL_FRONT,GL_SHININESS,self.mat_shininess)
        
        glLightfv(GL_LIGHT0,GL_POSITION,self.light_position)
        glLightfv(GL_LIGHT0,GL_DIFFUSE,self.white_light)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT,self.lmodel_ambient)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        # keep unit of  normal vector 
        glEnable(GL_NORMALIZE)
        print('End initialization.')
        
    def setRotation(self,dxdy):
        dx,dy = dxdy
        # rotate the view port
        self.camera_azimuth -= dx * self.rotation_ratio
        self.camera_attitude += dy * self.rotation_ratio
        self.update()
    
    def setScale(self,scale_size):
        _, y = scale_size.x(), scale_size.y()
        if self.eye_R > 5:
            self.eye_R += self.scale_ratio * y
            self.update() 
        
    def setMovement(self,dxdy):
        dx,dy = dxdy
        self.scene_movement[0] += self.movement_ratio*dx
        self.scene_movement[1] += self.movement_ratio*dy
        self.update()
    
    def paintGL(self):
        #glutSetWindow(self.main_window)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
# # debug code
#         num = glGetIntegerv (GL_MODELVIEW_STACK_DEPTH)
#         if num == 31:
#             sys.exit()
#         print('The number of ModelVIEW:',num)

        glPushMatrix()
        # scene
        ## move
        glTranslatef(self.scene_movement[0],-self.scene_movement[1],0.0)
        ## rotation
        eyex,eyey,eyez = self.calculate_eyepoint()
        if self.follow:
            centerx,centery,centerz = self.drone_position
        else:
            centerx,centery,centerz = self.camera_view_center
        
        if self.camera_attitude > 90:
        # solve the situation where the up vector is upward
            glRotatef(180,0.0,0.0,1.0)
            gluLookAt(eyex,eyey,eyez,centerx,centery,centerz,0.0,0.0,1.0)
        else:
            gluLookAt(eyex,eyey,eyez,centerx,centery,centerz,0.0,0.0,1.0)
            
        glLightfv(GL_LIGHT0,GL_POSITION,self.light_position)
        self.draw_model(self.drone_position,self.drone_angles,self.draw_drone)
        self.draw_axes()
        if self.trace_visible:
            self.draw_trace()
        self.draw_floor()
        glPopMatrix()
        #glutSwapBuffers()
    
    def resizeGL(self,w,h):
        glViewport(0,0,w,h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0,w/h,self.near,self.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0,0.0,-5.0)
    
    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & QtCore.Qt.LeftButton:
            # move the scene
            self.setMovement((dx,dy)) 
        elif event.buttons() & QtCore.Qt.MiddleButton:
            self.setRotation((dx,dy))
            
        self.lastPos = event.pos()
    
    def wheelEvent(self, event):
        # scale the scene
        self.setScale(event.angleDelta())

    def normalizeAngle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle
    
    @staticmethod   
    def calc_angle(t,speed):
        return t * speed % 1.0 / 1.0  * 360
    
    def draw_vector(self,speed):
        glPushMatrix()
        glColor3f(*self.vector_radius_color)
        glRotatef(-90,1.0,0.0,0.0)
        glutSolidCylinder(self.vector_radius,speed/100.0,8,10)
        glTranslatef(0.0,0.0,speed/100.0)
        glutSolidCone(2*self.vector_radius,3*self.vector_radius,8,10)
        glPopMatrix()
        
    def draw_propeller(self,t,pos,propeller_num,propeller_obj):
        glPushMatrix()
        angle = self.calc_angle(t,self.drone_motors_speed[propeller_num])
        if self.vector_visible:
            glPushMatrix()
            glTranslatef(pos[0],pos[1]+2.2,pos[2])
            self.draw_vector(self.drone_motors_speed[propeller_num])
            glPopMatrix()
        
        neg_pos = [-item for item in pos]
        glTranslatef(*neg_pos)
        glRotatef(angle,0.0,-1.0,0.0)
        glTranslatef(*pos)
        propeller_obj.draw()
        
        glPopMatrix()
        
    def draw_model(self,displacement,angles,draw_func):
        move_model(*displacement)(rotate_model(*angles)(draw_func))()
    
    def draw_drone(self):
#       print('In draw model')
        glPushMatrix()
        # model plot
        glTranslatef(0.0,0.0,9.5)
        # 312
        glRotatef(90,1.0,0.0,0.0)
        
        self.drone_base.draw()
        
        t = time.time()
        self.draw_propeller(t, [11.0,0.0,11.0], 0, self.drone_propeller1)
        self.draw_propeller(t, [11.0,0.0,-11.0], 1, self.drone_propeller2)
        self.draw_propeller(t, [-11.0,0.0,-11.0], 2, self.drone_propeller3)
        self.draw_propeller(t, [-11.0,0.0,11.0],3, self.drone_propeller4)
        
        glPopMatrix()
    
    def draw_trace(self):
        """Draw the drone history trace"""
        glPushMatrix()
        glDisable(GL_LIGHTING)
        glColor3f(*self.drone_trace_color)
        glBegin(GL_LINE_STRIP)
        for pos in self.drone_position_history:
            glVertex3f(*pos) 
        glEnd()
        glEnable(GL_LIGHTING)
        glPopMatrix()
    
    def draw_axes(self):
        """ Draw axes
        """
        glPushMatrix()
        glTranslatef(0,0,0)
        glRotatef(self.tip,1,0,0)
        #glScalef(0.25,0.25,0.25)
        glLineWidth(2.0)
        glDisable(GL_LIGHTING)
        # X axis
        glColor3f(1,0,0)
        glBegin(GL_LINE_STRIP)
        glVertex3fv(self.ORG)
        glVertex3fv(self.AXES[0])
        glEnd()
        glRasterPos3f(np.linalg.norm(self.AXES[0]),0.0,0.0)
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12,ord('x'))
        
        # Y axis
        glColor3f(0,1,0)
        glBegin(GL_LINE_STRIP)
        glVertex3fv(self.ORG)
        glVertex3fv(self.AXES[1])
        glEnd()
        glRasterPos3f(0.0,np.linalg.norm(self.AXES[1]),0.0)
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12,ord('y'))
        
        # Z axis
        glColor3f(0,0,1)
        glBegin(GL_LINE_STRIP)
        glVertex3fv(self.ORG)
        glVertex3fv(self.AXES[2])
        glEnd()
        glRasterPos3f(0.0,0.0,np.linalg.norm(self.AXES[2]))
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12,ord('z'))
        
        glEnable(GL_LIGHTING)
        glPopMatrix()
        
    
    def draw_floor(self):
        """Draw the floor"""
        glPushMatrix()
        #glLoadIdentity()
        glLineWidth(2.0)
        glDisable(GL_LIGHTING)
        glColor3fv(self.floor_color)
        dl = (self.floor_size[1] - self.floor_size[0])/self.floor_grid_num
        glBegin(GL_LINES)
        for i in range(self.floor_grid_num+1):
            glVertex3f(self.floor_size[0] + dl * i,self.floor_size[0],0.0)
            glVertex3f(self.floor_size[0] + dl * i,self.floor_size[1],0.0)
            glVertex3f(self.floor_size[0],self.floor_size[0] + dl * i,0.0)
            glVertex3f(self.floor_size[1],self.floor_size[0] + dl * i,0.0)
        glEnd()
        glPopMatrix()
        glEnable(GL_LIGHTING)
        
    def calculate_eyepoint(self):
        """Calculate gluLookAt eye point from azimuth and attitude"""
        L_xy = self.eye_R * np.cos(self.camera_attitude * np.pi/180)
        x = L_xy * np.cos(self.camera_azimuth * np.pi / 180)
        y = L_xy * np.sin(self.camera_azimuth * np.pi / 180)
        z = self.eye_R * np.sin(self.camera_attitude * np.pi /180)
        return (x,y,z)
    
    def animate(self):
        self.update()
    
    def update(self, *args, **kwargs):
        self.loadFinished.emit(True)
        return QtOpenGL.QGLWidget.update(self, *args, **kwargs)
    
    def update_state(self,state):
        """Update motor animation state from state"""
        try:
            pos,attitude,output = state
            self.drone_position_history.append(self.drone_position)
            self.drone_position = [pos[0], pos[1], -pos[2]]
            self.drone_angles = attitude
            self.drone_motors_speed = output
            self.update()
        except Exception as ex:
            print(ex)
    
    def reset(self):
        """Go back to origin."""
        self.position_history = []
        self.drone_position = [0,0,0]
        self.drone_motors_speed = [0,0,0,0]
