#coding:utf-8
"""
creator: Marx Liu
"""
from __future__ import division
import sys
import os
import time
import pkg_resources
from collections import OrderedDict
import random
import numpy as np
from pyulog.core import ULog
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
# from hypothesis.strategies import none
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import pdb
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from widgets import (QuadrotorWin, InfoWin, ParamsWin, 
                     TabWidget, CurveModifyWin, Checkbox,
                     ThreadQDialog, PropertyLabel, AnalysisGraphWin,
                     HelpWin)

__version__ = '1.1.0b'
pyqtSignal = QtCore.pyqtSignal

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context,  text,  disambig):
        return QtGui.QApplication.translate(context,  text,  disambig,  _encoding)
except AttributeError:
    def _translate(context,  text,  disambig):
        return QtGui.QApplication.translate(context,  text,  disambig)

resource_package = __name__  

def get_source_name(file_path_name):
    return pkg_resources.resource_filename(resource_package, file_path_name)  

basepath = os.path.dirname(__file__)

def show_curve_property_diag(id, parent):
    def func(event):
        print('curve was double clicked')
        print(event)
        win = CurveModifyWin(id, parent)
        win.show()
        QtGui.QApplication.processEvents()
        print('end')
        
    return func

def show_curve_property_diag_(id, info_data):
    def func(event):
        print('curve was double clicked')
        print(event)
        win = InfoWin(info_data)
        win.show()
        print('end')
    return func

def load_file_first_info():
    msg = QtGui.QMessageBox()
    msg.setText('Please open an ULog file first.')
    msg.setWindowTitle('Info')
    msg.setStandardButtons(QtGui.QMessageBox.Ok)
    msg.buttonClicked.connect(msg.close)
    msg.exec_()


class TableView(QtGui.QTableWidget):    
    """
    A simple table to demonstrate the QComboBox delegate.
    """
    def __init__(self,  *args,  **kwargs):
        QtGui.QTableView.__init__(self,  *args,  **kwargs)


class MainWindow(QtGui.QMainWindow):
    
    deletePressed = pyqtSignal(bool)
    quadrotorStateChanged = pyqtSignal(object)
    motorSpeedChanged = pyqtSignal(object)
    quadrotorStateReseted = pyqtSignal(bool)
    SCALE_FACTOR = 80
    
    def __init__(self):
        """
        Frame of GUI
        ===========================
        | ToolBar____ ____        |
        |_______|tab1|tab2|_______|
        |    | |                  |
        |plot| |     graph1       |
        |list| |------------------|
        |----|<|                  |
        |data| |     graph2       |
        |list| |                  |
        ===========================
        """
        super(MainWindow, self).__init__()
        
        self.log_data_list = None
        self.log_file_name = None
        self.data_dict = None
        self.log_info_data = None
        self.log_params_data = None
        self.log_changed_params = []

        self.main_widget = QtGui.QWidget(self)
        self.mainlayout = QtGui.QHBoxLayout()
        self.main_widget.setLayout(self.mainlayout)
        
        # ToolBar
        self.toolbar = self.addToolBar('FileManager')
        self.basic_tool_group = QtGui.QActionGroup(self)
        ## load log file
        self.loadfile_action = QtGui.QAction(QtGui.QIcon(get_source_name('icons/open.gif')), 'Open log file', self)
        self.loadfile_action.setShortcut('Ctrl+O')
        self.loadfile_action.triggered.connect(self.callback_open_log_file)
        self.toolbar.addAction(self.loadfile_action)
        ## plot quadrotor in 3d graph
        self.show_quadrotor_3d = QtGui.QAction(QtGui.QIcon(get_source_name('icons/quadrotor.gif')), 'show 3d viewer', self)
        self.show_quadrotor_3d.setShortcut('Ctrl+Shift+Q')
        self.show_quadrotor_3d.triggered.connect(self.callback_show_quadrotor)
        self.toolbar.addAction(self.show_quadrotor_3d)
        ## show quadrotor info
        self.show_info = QtGui.QAction(QtGui.QIcon(get_source_name('icons/info.gif')), 'show log info', self)
        self.show_info.setShortcut('Ctrl+I')
        self.show_info.triggered.connect(self.callback_show_info_pane)
        self.toolbar.addAction(self.show_info)
        self.info_pane_showed = False
        ## show quadrotor param
        self.show_params = QtGui.QAction(QtGui.QIcon(get_source_name('icons/params.gif')), 'show params', self)
        self.show_params.setShortcut('Ctrl+P')
        self.show_params.triggered.connect(self.callback_show_parameters_pane)
        self.toolbar.addAction(self.show_params)
        self.params_pane_showed = False
        ## show some default analysis graphs
        self.show_analysis_graphs = QtGui.QAction(QtGui.QIcon(get_source_name('icons/analysis_graph.gif')), 
                                                  'show default analysis graph control pane', self)
        self.show_analysis_graphs.setShortcut('Ctrl+G')
        self.show_analysis_graphs.triggered.connect(self.callback_show_analysis_graph_pane)
        self.toolbar.addAction(self.show_analysis_graphs)
        self.analysis_graphs_showed = False
        self.analysis_graphs_pane = None
        ## show help
        self.show_help = QtGui.QAction(QtGui.QIcon(get_source_name('icons/help.gif')),
                                                    'show help', self)
        self.show_help.setShortcut('Ctrl+H')
        self.show_help.triggered.connect(self.callback_show_help_pane)
        self.toolbar.addAction(self.show_help)
        self.help_pane_showed = False
        self.help_pane = None
        
        self.basic_tool_group.addAction(self.loadfile_action)
        self.basic_tool_group.addAction(self.show_quadrotor_3d)
        self.basic_tool_group.addAction(self.show_info)
        self.basic_tool_group.addAction(self.show_params)
        self.basic_tool_group.addAction(self.show_analysis_graphs)
        self.basic_tool_group.addAction(self.show_help)

        ## show some analysis graph
        # Left plot item widget
        self.plot_data_frame = QtGui.QFrame(self)
        self.plot_data_frame.setFrameShape(QtGui.QFrame.StyledPanel)
#         self.plot_data_layout_H = QtGui.QHBoxLayout(self.plot_data_frame)
        self.plot_data_layout_V = QtGui.QVBoxLayout(self.plot_data_frame)
        ## Data Plotting [id, filesystem, ]
        self.data_plotting = OrderedDict()
        ### There exists a Default graph
        self.line_ID = 0
        lbl_ploting_data = QtGui.QLabel('Data Plotting')
        self.plotting_data_tableView = TableView(self.plot_data_frame)
        self.plotting_data_tableView.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | 
                                                     QtGui.QAbstractItemView.SelectedClicked)
        self.plotting_data_tableView.setSortingEnabled(False)
        self.plotting_data_tableView.horizontalHeader().setStretchLastSection(True)
        self.plotting_data_tableView.resizeColumnsToContents()
        self.plotting_data_tableView.setColumnCount(3)
        self.plotting_data_tableView.setColumnWidth(0, 200)
        self.plotting_data_tableView.setColumnWidth(1, 60)
        self.plotting_data_tableView.setColumnWidth(2, 50)
        self.plotting_data_tableView.setHorizontalHeaderLabels(['Label', 'Visible', 'Curve Style'])
        self.id = 0
        lbl_ploting_data.setBuddy(self.plotting_data_tableView)
        self.plot_data_layout_V.addWidget(lbl_ploting_data)
        self.plot_data_layout_V.addWidget(self.plotting_data_tableView)
        
        edit_layout = QtGui.QHBoxLayout()
        self.delete_btn = QtGui.QPushButton('Delete')
        self.delete_btn.clicked.connect(self.callback_del_plotting_data)
        self.clear_btn = QtGui.QPushButton('Clear')
        self.clear_btn.clicked.connect(self.callback_clear_plotting_data)
        edit_layout.addWidget(self.clear_btn)
        edit_layout.addWidget(self.delete_btn)
        self.plot_data_layout_V.addLayout(edit_layout)
        
        ## Data in the log file
        self.list_data_frame = QtGui.QFrame(self)
        self.list_data_frame.setMinimumWidth(400)
        self.list_data_frame.setMaximumWidth(600)
        self.list_data_frame.resize(400, 500)
        self.list_data_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.list_data_layout = QtGui.QVBoxLayout(self.list_data_frame)
        ### line to search item
        self.choose_item_lineEdit = QtGui.QLineEdit(self.list_data_frame)
        self.choose_item_lineEdit.setPlaceholderText('filter by data name')
        self.choose_item_lineEdit.textChanged.connect(self.callback_filter)
        ### tree to show data to plot
        self.item_list_treeWidget = QtGui.QTreeWidget(self.list_data_frame)
        self.item_list_treeWidget.clear()
        self.item_list_treeWidget.setColumnCount(3)
        self.item_list_treeWidget.setColumnWidth(0, 160)
        self.item_list_treeWidget.setHeaderLabels(['Flight Data', 'Type', 'Length'])
        self.item_list_treeWidget.itemDoubleClicked.connect(self.callback_tree_double_clicked)
        self.item_list_treeWidget.resizeColumnToContents(2)
        self.list_data_layout.addWidget(self.choose_item_lineEdit)
        self.list_data_layout.addWidget(self.item_list_treeWidget)
        
        # Right plot item
        self.graph_frame = QtGui.QFrame(self)
        self.default_tab = TabWidget(self.graph_frame)
        self.graph_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.animation_layout = QtGui.QVBoxLayout(self.graph_frame)
        
        ## quadrotor 3d
        self.quadrotor_win = QuadrotorWin(self)
        self.quadrotor_win.closed.connect(self.quadrotor_win_closed_event)
        self.quadrotor_win.hide()
        self.first_load = True
        self.quadrotor_widget_isshowed = False
        
        ## default plot
        self.default_graph_widget_t = pg.GraphicsLayoutWidget()
        self.default_graph_widget_2d = pg.GraphicsLayoutWidget()
        self.default_graph_widget_3d = pg.GraphicsLayoutWidget()
        self.default_tab.addTab(self.default_graph_widget_t, 't')
        self.default_tab.addTab(self.default_graph_widget_2d, '2D')
        self.default_tab.addTab(self.default_graph_widget_3d, '3D')
        ### a hidable ROI region
        self.detail_graph = self.default_graph_widget_t.addPlot(row=0, col=0)
        self.detail_graph.setAutoVisible(True)
        self.detail_graph.hide()
        ### main graph to plot curves
        self.main_graph_t = self.default_graph_widget_t.addPlot(row=1, col=0)
        self.main_graph_t.showGrid(x=True, y=True)
        self.main_graph_t.keyPressEvent = self.keyPressed
        self.deletePressed.connect(self.callback_del_plotting_data)
        self.main_graph_t.addLegend()
        ROI_action = QtGui.QAction('show/hide ROI graph', self.main_graph_t)
        ROI_action.triggered.connect(self.callback_ROI_triggered)
        self.main_graph_t.scene().contextMenu.append(ROI_action)
        self.ROI_region = pg.LinearRegionItem()
        self.ROI_region.setZValue(10)
        self.ROI_region.hide()
        self.ROI_showed = False
        ### main graph
        self.main_graph_2d = self.default_graph_widget_2d.addPlot(row=0, col=0)
        self.main_graph_2d.showGrid(x=True, y=True)
        self.main_graph_3d = self.default_graph_widget_3d.addPlot(row=0, col=0)
        
        def update():
            self.ROI_region.setZValue(10)
            minX,  maxX = self.ROI_region.getRegion()
            self.detail_graph.setXRange(minX,  maxX,  padding=0)    
    
        self.ROI_region.sigRegionChanged.connect(update)
        
        def updateRegion(window,  viewRange):
            rgn = viewRange[0]
            self.ROI_region.setRegion(rgn)
        self.detail_graph.sigRangeChanged.connect(updateRegion)
        
        self.main_graph_t.addItem(self.ROI_region, ignoreBounds=True)
        
        ## vertical line
        self.vLine = pg.InfiniteLine(angle=90,  movable=False)
        self.vLine.hide()
        self.main_graph_t.addItem(self.vLine, ignoreBounds=True)
        self.vLine_detail = pg.InfiniteLine(angle=90,  movable=False)
        self.vLine_detail.hide()
        self.detail_graph.addItem(self.vLine_detail, ignoreBounds=True)
        
        ## flag whether there is a curve clicked after last clicked event
        self.curve_clicked = False
        self.curve_clicked_time = time.time()
        self.curve_highlighted = []
        self.animation_layout.addWidget(self.default_tab)
        ## time line
        self.time_line_frame = QtGui.QFrame(self)
        self.time_line_frame.setMaximumHeight(45)
        self.time_line_frame.setMinimumHeight(45)
        self.time_line_layout = QtGui.QHBoxLayout(self.time_line_frame)
        time_line_lbl = QtGui.QLabel('x')
        time_line_lbl.setToolTip('set play speed')
        speed_combo = QtGui.QComboBox()
        speed_combo.addItems(['1', '2', '4', '8'])
        self.speed_factor = 500
        self.time_line_layout.addWidget(time_line_lbl)
        self.time_line_layout.addWidget(speed_combo)
        speed_combo.currentIndexChanged.connect(self.callback_speed_combo_indexChanged)
        self.current_factor = 500/1
        self.time_line_button_play = QtGui.QPushButton(self.time_line_frame)
        self.time_line_button_play.setEnabled(False)
        self.time_line_button_play.setIcon(QtGui.QIcon(get_source_name("icons/play.jpg")))
        self.time_line_play = False
        self.time_line_button_play.clicked.connect(self.callback_play_clicked)
        self.time_line_button_stop = QtGui.QPushButton(self.time_line_frame)
        self.time_line_button_stop.setEnabled(False)
        self.time_line_button_stop.setIcon(QtGui.QIcon(get_source_name("icons/stop.jpg")))
        self.time_line_button_stop.clicked.connect(self.callback_stop_clicked)
        self.time_line_layout.addWidget(self.time_line_button_play)
        self.time_line_layout.addWidget(self.time_line_button_stop)
        self.time_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0, 100)
        #### index for time_stamp
        self.time_line_layout.addWidget(self.time_slider)
        
        ## timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.animation_update)
        self.current_time = 0
        self.dt = 50
        
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter1.addWidget(self.plot_data_frame)
        self.splitter1.addWidget(self.list_data_frame)
        
        self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter2.addWidget(self.graph_frame)
        self.splitter2.addWidget(self.time_line_frame)
        
        self.splitter3 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitter3.addWidget(self.splitter1)
        self.splitter3.addWidget(self.splitter2)
        self.mainlayout.addWidget(self.splitter3)
        self.setCentralWidget(self.main_widget)
        self.setGeometry(200, 200, 1000, 800)
        self.setWindowTitle("pyFlightAnalysis")
        self.quadrotorStateChanged.connect(self.quadrotor_win.callback_update_quadrotor_pos)
        self.quadrotorStateReseted.connect(self.quadrotor_win.callback_quadrotor_state_reset)
    
    def keyPressed(self, event):
        """Key Pressed function for graph"""
        if event.key() == QtCore.Qt.Key_Delete:
            self.deletePressed.emit(True)
        elif event.key() == QtCore.Qt.Key_R:
            # ROI graph can also be triggered by press 'r'
            self.callback_ROI_triggered()
    
    @staticmethod
    def getIndex(data, item):
        for ind, d in enumerate(data):
            if d > item:
                return ind
            
        return len(data) - 1
             
    @staticmethod
    def quat_to_euler(q0, q1, q2, q3):
        #321
        angles = []
        for i in range(len(q0)):
            roll = 180/np.pi * np.arctan2(2.0 * (q0[i] * q1[i] + q2[i] * q3[i]),  1.0 - 2.0 * (q1[i]**2 + q2[i]**2))
            pitch = 180/np.pi * np.arcsin(2.0 * (q0[i] * q2[i] - q3[i] * q1[i]))
            yaw = 180/np.pi * np.arctan2(2.0 * (q0[i] * q3[i] + q1[i] * q2[i]),  1.0 - 2.0 * (q2[i]**2 + q3[i]**2))
            angles.append([roll, pitch, yaw])
        return angles
        
    def callback_open_log_file(self):
        config_path = os.path.join(os.getcwd(), get_source_name('config.txt'))
        if os.path.exists(config_path):
            with open(config_path, 'r') as conf:
                path_hist = conf.readline()
                path = path_hist.split(':')[-1]
        else:
            path = ''
        if not path:
            from os.path import expanduser
            path = expanduser('~')
            
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open Log File', path, 'Log Files (*.ulg)')
        # On Window,  filename will be a tuple (fullpath,  filter)
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            try:
                self.log_file_name = filename
                self.id = 0
                self.load_data()
                self.load_data_tree()
                self.analysis_graph_list = OrderedDict()
                self.update_graph_after_log_changed()
                self.time_line_button_play.setEnabled(True)
                # write the file path to config.txt
                with open(get_source_name('config.txt'), 'w') as conf:
                    conf.write('last_path:' + os.path.split(filename)[0])
            except Exception as ex:
                print(ex)
    
    def callback_play_clicked(self):
        """Time line play"""
        self.time_line_play = not self.time_line_play
        if self.log_file_name is not None:
            if self.time_line_play:
                self.time_line_button_play.setIcon(QtGui.QIcon(get_source_name("icons/pause.jpg")))
                self.time_line_button_stop.setEnabled(True)
                if self.ROI_showed:
                    region = self.ROI_region.getRegion()
                    self.vLine.setPos(region[0])
                    self.vLine_detail.setPos(region[0])
                else:
                    self.vLine.setPos(self.time_range[0])
                    self.vLine_detail.setPos(self.time_range[0])
                self.vLine.show()
                self.vLine_detail.show()
                # start timer
                self.timer.start(self.dt)
            else:
                self.time_line_button_play.setIcon(QtGui.QIcon(get_source_name("icons/play.jpg")))
                self.time_line_button_stop.setEnabled(False)
                self.timer.stop()
    
    def callback_stop_clicked(self):
        self.time_line_play = False
        self.timer.stop()
        self.time_line_button_play.setIcon(QtGui.QIcon(get_source_name("icons/play.jpg")))
        self.time_line_button_stop.setEnabled(False)
        self.time_slider.setValue(0)
        self.time_index = 0
        self.vLine.hide()
        self.vLine_detail.hide()
        self.quadrotorStateReseted.emit(True)
    
    def animation_update(self):
        """update the quadrotor state"""
        dV = 100.0/(self.time_range[1] - self.time_range[0])
        
        if self.ROI_showed:
            start, end = self.ROI_region.getRegion() 
            t = self.current_time + start
            # emit data
            indexes = list(map(self.getIndex, [self.time_stamp_position, self.time_stamp_attitude, self.time_stamp_output], [t, t, t]))
            state_data = [self.position_history[indexes[0]], 
                          self.attitude_history[indexes[1]], self.output_history[indexes[2]]]
            self.quadrotorStateChanged.emit(state_data)
            # update slider
            self.time_slider.setValue(int(dV * (self.current_time + start - self.time_range[0])))
            # update vLine pos
            self.vLine.setPos(t)
            self.vLine_detail.setPos(t)
            if self.current_time > (end - start):
                self.current_time = 0
                self.quadrotorStateReseted.emit(True)
        else:
            t = self.current_time + self.time_range[0]
            self.time_slider.setValue(int(dV * self.current_time)) 
            # update quadrotor position and attitude and motor speed
            indexes = list(map(self.getIndex, [self.time_stamp_position, self.time_stamp_attitude, self.time_stamp_output], [t, t, t]))
            state_data = [self.position_history[indexes[0]], 
                          self.attitude_history[indexes[1]], self.output_history[indexes[2]]]
#             print('state:',state_data)
            self.quadrotorStateChanged.emit(state_data)
            # update vLine pos
            self.vLine.setPos(t)
            self.vLine_detail.setPos(t)
            # if arrive end just replay
            if self.current_time > (self.time_range[1] - self.time_range[0]):
                self.current_time = 0
                self.quadrotorStateReseted.emit(True)
    
        self.current_time += self.dt/self.current_factor
        
        
    def callback_show_quadrotor(self):
        if self.quadrotor_widget_isshowed:
            self.show_quadrotor_3d.setIcon(QtGui.QIcon(get_source_name('icons/quadrotor.gif')))
            self.quadrotor_widget_isshowed = not self.quadrotor_widget_isshowed
            self.quadrotor_win.hide()
            self.update()
        else:
            self.quadrotor_widget_isshowed = not self.quadrotor_widget_isshowed
            self.show_quadrotor_3d.setIcon(QtGui.QIcon(get_source_name('icons/quadrotor_pressed.gif')))
            splash = ThreadQDialog(self.quadrotor_win.quadrotor_widget, self.quadrotor_win)
            splash.run()
            self.quadrotor_win.show()
            self.update()
    
    def callback_show_info_pane(self):
        if self.log_info_data is not None:
            if self.info_pane_showed:
                self.show_info.setIcon(QtGui.QIcon(get_source_name('icons/info.gif')))
                self.info_pane.close()
                del self.info_pane
            else:
                self.show_info.setIcon(QtGui.QIcon(get_source_name('icons/info_pressed.gif')))
                self.info_pane = InfoWin(self.log_info_data)
                self.info_pane.closed.connect(self.callback_show_info_pane_closed)
                self.info_pane.show()
            self.info_pane_showed = not self.info_pane_showed
        else:
            load_file_first_info()
            
    def callback_show_info_pane_closed(self, closed):
        if closed:
            self.show_info.setIcon(QtGui.QIcon(get_source_name('icons/info.gif')))
    
    def callback_show_parameters_pane(self):
        if self.log_params_data is not None:
            if self.params_pane_showed:
                self.show_params.setIcon(QtGui.QIcon(get_source_name('icons/params.gif')))
                self.params_pane.close()
                del self.params_pane
            else:
                self.show_params.setIcon(QtGui.QIcon(get_source_name('icons/params_pressed.gif')))
                self.params_pane = ParamsWin(self.log_params_data, self.log_changed_params)
                self.params_pane.closed.connect(self.callback_show_params_pane_closed)
                self.params_pane.show()
            self.params_pane_showed = not self.params_pane_showed
        else:
            load_file_first_info()
        
    def callback_show_params_pane_closed(self, closed):
        if closed:
            self.params_pane_showed = False
            self.show_params.setIcon(QtGui.QIcon(get_source_name('icons/params.gif')))
    
    def callback_show_analysis_graph_pane(self):
        if self.log_data_list is not None:
            if self.analysis_graphs_showed:
                self.show_analysis_graphs.setIcon(QtGui.QIcon(get_source_name('icons/analysis_graph.gif')))
                self.analysis_graphs_pane.hide()
            else:
                self.show_analysis_graphs.setIcon(QtGui.QIcon(get_source_name('icons/analysis_graph_pressed.gif')))
                if self.analysis_graphs_pane is None:
                    self.analysis_graphs_pane = AnalysisGraphWin(self)
                    self.analysis_graphs_pane.closed.connect(self.callback_analysis_graphs_pane_closed)
                    self.analysis_graphs_pane.sigChecked.connect(self.callback_analysis_graph_data_checked)
                    self.analysis_graphs_pane.sigUnchecked.connect(self.callback_analysis_graph_data_unchecked)
                self.analysis_graphs_pane.show()
            self.analysis_graphs_showed = not self.analysis_graphs_showed
        else:
            load_file_first_info()
    
    def callback_analysis_graphs_pane_closed(self, closed):
        if closed:
            self.analysis_graphs_showed = False
            self.show_analysis_graphs.setIcon(QtGui.QIcon(get_source_name('icons/analysis_graph.gif')))
            
    def callback_analysis_graph_data_checked(self, curve_name_with_data):
        color_list = [(255, 0, 0), 
                      (0, 255, 0), 
                      (0, 0, 255),
                      (0, 255, 255),
                      (255, 0, 255), 
                      (155, 0, 160),
                      (0, 155, 155)]
        curve_name, data = curve_name_with_data
        data_type = data[0]
        if curve_name not in self.analysis_graph_list:
            new_graph = pg.GraphicsLayoutWidget()
            ax = new_graph.addPlot(row=0, col=0) 
            ax.addLegend()
            self.analysis_graph_list[curve_name] = new_graph
            self.default_tab.addTab(new_graph, curve_name)
            self.default_tab.setCurrentWidget(new_graph)
            for ind, curve_data in enumerate(data[1:]):
                ax.plot(curve_data[0], curve_data[1], pen=color_list[ind%len(color_list)], name=curve_data[2])
    
    def callback_analysis_graph_data_unchecked(self, graph_name):
        tab_index = 0
        for i in range(self.default_tab.count()):
            if self.default_tab.widget(i) == self.analysis_graph_list[graph_name]:
                tab_index = i
                break
        self.default_tab.removeTab(tab_index)
        self.analysis_graph_list.pop(graph_name)
    
    def callback_show_help_pane(self):
        if self.help_pane_showed:
            self.show_help.setIcon(QtGui.QIcon(get_source_name('icons/help.gif')))
            self.help_pane.hide()
        else:
            if self.help_pane is None:
                self.help_pane =  HelpWin()
                self.help_pane.closed.connect(self.callback_help_pane_closed)
                self.show_help.setIcon(QtGui.QIcon(get_source_name('icons/help_pressed.gif')))
            self.help_pane.show()
        self.help_pane_showed = not self.help_pane_showed
    
    def callback_help_pane_closed(self, closed):
        if closed:
            self.help_paned_showed = False
            self.show_help.setIcon(QtGui.QIcon(get_source_name('icons/help.gif')))
    
    def callback_speed_combo_indexChanged(self, index):
        self.current_factor = self.speed_factor / 2**index
    
    def callback_filter(self, filtertext):
        """Accept filter and update the tree widget"""
        filtertext = str(filtertext)
        if self.data_dict is not None:
            if filtertext == '':
                self.load_data_tree()
            else:
                self.item_list_treeWidget.clear()
                for key, values_name in self.data_dict.items():
                    values_satisfied = [] 
                    if filtertext in key:
                        for value in values_name:
                            values_satisfied.append(value)
                    else:
                        for value in values_name:
                            if filtertext in value[0]:
                                values_satisfied.append(value)
                    if values_satisfied:
                        param_name = QtGui.QTreeWidgetItem(self.item_list_treeWidget, [key])
                        self.item_list_treeWidget.expandItem(param_name)
                        for data_name in values_satisfied:
                            self.item_list_treeWidget.expandItem(
                                QtGui.QTreeWidgetItem(param_name, [data_name[0], data_name[1], data_name[2]]))
                            
        
    def callback_graph_clicked(self, event):
        """ set the curve highlighted to be normal """
        print('graph clicked')
        if self.curve_clicked:
            if event.modifiers() == QtCore.Qt.ControlModifier:
                pass
            else:
                for curve in self.curve_highlighted[:-1]:
                    curve.setShadowPen(pg.mkPen((200, 200, 200),  width=1,  cosmetic=True))
                self.curve_highlighted = self.curve_highlighted[-1:]
                
        if len(self.curve_highlighted) > 0 and not self.curve_clicked:
            for curve in self.curve_highlighted:
                curve.setShadowPen(pg.mkPen((120, 120, 120),  width=1,  cosmetic=True))
                self.curve_highlighted = []
                self.plotting_data_tableView.setCurrentCell(0,  0)
                
        self.curve_clicked = False
        
    def callback_tree_double_clicked(self, item, col):
        """Add clicked item to Data plotting area"""
        def expand_name(item):
            if item.parent() is None:
                return str(item.text(0))
            else:
                return expand_name(item.parent()) + '->' + str(item.text(0))
        # When click high top label,  no action will happened
        if item.parent() is None:
            return    
        item_label = expand_name(item)
        row = len(self.data_plotting)
        self.plotting_data_tableView.insertRow(row)
        
        # Label
        self.plotting_data_tableView.setCellWidget(row, 0, QtGui.QLabel(item_label))
        
        # Curve Visible
        chk = Checkbox(self.id, '')
        chk.setChecked(True)
        chk.sigStateChanged.connect(self.callback_visible_changed)
        self.plotting_data_tableView.setCellWidget(row, 1, chk)
        
        # Curve Color
        ## rgb, prefer deep color
        color = [random.randint(0, 150) for _ in range(3)]
        color_text = '#{0[0]:02x}{0[1]:02x}{0[2]:02x}'.format(color) 
        ## Curve Marker
        marker = None
        lbl = PropertyLabel(self.id, self, 
                            "<font color='{0}'>{1}</font> {2}".format(color_text,'▇▇',str(marker)))
        lbl.sigPropertyChanged.connect(self.callback_property_changed)
        self.plotting_data_tableView.setCellWidget(row, 2, lbl)
        
        data_index = list(list(self.data_dict.keys())).index(item_label.split('->')[0])
        data_name = item_label.split('->')[-1]
        
        ## ms to s
        t = self.log_data_list[data_index].data['timestamp']/10**6
        data = self.log_data_list[data_index].data[data_name]
        if len(self.data_plotting) == 0:
            label_style = {'color': '#EEEEEE', 'font-size':'14pt'}
            self.main_graph_t.setLabel('bottom', 't(s)', **label_style)
        curve = self.main_graph_t.plot(t, data, symbol=marker, pen=color, clickable=True, name=item_label)
        curve.curve.setClickable(True)
        # functional method
        curve.mouseDoubleClickEvent = show_curve_property_diag(self.id, self)
        # whether show the curve
        showed = True
        self.data_plotting[self.id] = [item_label, showed, curve]
        # increase the id
        self.id += 1
        self.update_ROI_graph()
        self.default_tab.setCurrentWidget(self.default_graph_widget_t)
    
    def callback_curve_clicked(self, curve):
        """"""
        print('curve clicked')
        self.curve_clicked = True
        dt = time.time() - self.curve_clicked_time 
        self.curve_clicked_time = time.time()
        if dt < 0.3:
            win = CurveModifyWin()
            curves = [data[2] for data in self.data_plotting.values()]
            ind = curves.index(curve)
            curve.setShadowPen(pg.mkPen((70, 70, 70),  width=5,  cosmetic=True))
            self.curve_highlighted.append(curve)
            self.plotting_data_tableView.setCurrentCell(ind, 0)
        
    def callback_del_plotting_data(self):
        """"""
        indexes = self.plotting_data_tableView.selectedIndexes()
        rows_del = set([ind.row() for ind in indexes])
        rows_all = set(range(len(self.data_plotting)))
        rows_reserved = list(rows_all - rows_del) 
        data_plotting = OrderedDict()
        keys, values = list(self.data_plotting.keys()), list(self.data_plotting.values())
        for row in rows_reserved:
            data_plotting[keys[row]] = values[row]
        self.data_plotting = data_plotting
        self.update_graph()
    
    def callback_visible_changed(self, chk):
        """"""
        state = True if chk.checkState() == QtCore.Qt.Checked else False
        self.data_plotting[chk.id][1] = state
        self.update_graph()
        
    def callback_color_changed(self, btn):
        color = [c*255 for c in btn.color('float')[:-1]]
        self.data_plotting[btn.id][2].opts['pen'] = color
        self.update_graph()
        
    def callback_marker_changed(self, mkr):
        self.data_plotting[mkr.id][2].opts['symbol'] = mkr.marker
        self.update_graph()
        
    def keyPressEvent(self, event, *args, **kwargs):
        print(event)
        if event.key() == QtCore.Qt.Key_S:
            print('S pressed')
            if self.splitter1.isHidden():
                self.splitter1.show()
            else:
                self.splitter1.hide()
        elif event.key() == QtCore.Qt.Key_D:
            print('D pressed')
            for curve in self.curve_highlighted:
                del(curve)
        return QtGui.QMainWindow.keyPressEvent(self, event, *args, **kwargs)
    
    def update_graph(self):
        # update tableView
        # clear 
        self.plotting_data_tableView.setRowCount(0)
        # add
        for ind, (item_id, item) in enumerate(self.data_plotting.items()):
            self.plotting_data_tableView.insertRow(ind)
            self.plotting_data_tableView.setCellWidget(ind, 0, QtGui.QLabel(item[0]))
            chkbox = Checkbox(item_id, '')
            chkbox.setChecked(item[1])
            chkbox.sigStateChanged.connect(self.callback_visible_changed)
            self.plotting_data_tableView.setCellWidget(ind, 1, chkbox)
            curve = item[2]
            color = curve.opts['pen']
            if isinstance(color, QtGui.QColor):
                color = color.red(), color.green(), color.blue()
            marker = curve.opts['symbol']
            marker_dict = OrderedDict([(None,'None'), ('s','☐'), ('t','▽'), ('o','○'), ('+','+')])
            color_text = '#{0[0]:02x}{0[1]:02x}{0[2]:02x}'.format(color)
            lbl_txt = "<font color='{0}'>{1}</font> {2}".format(color_text,'▇▇',str(marker_dict[marker]))
            lbl = PropertyLabel(item_id, self, lbl_txt)
            lbl.sigPropertyChanged.connect(self.callback_property_changed)
            self.plotting_data_tableView.setCellWidget(ind, 2, lbl)
        
        # update curve
        # remove curves in graph
        items_to_be_removed = []
        for item in self.main_graph_t.items:
            if isinstance(item, pg.PlotDataItem):
                items_to_be_removed.append(item)
        for item in items_to_be_removed:
            self.main_graph_t.removeItem(item)

        self.main_graph_t.legend.scene().removeItem(self.main_graph_t.legend)
        self.main_graph_t.addLegend()
        # redraw curves
        for ind, (item_id, item) in enumerate(self.data_plotting.items()):
            label, showed, curve = item
            color = curve.opts['pen']
            if isinstance(color, QtGui.QColor):
                color = color.red(), color.green(), color.blue()
            data = curve.xData, curve.yData
            marker = curve.opts['symbol']
            symbolSize = curve.opts['symbolSize']
            if showed:
                curve = self.main_graph_t.plot(data[0], data[1], symbol=marker, pen=color, name=label, symbolSize=symbolSize)
                self.data_plotting[item_id][2] = curve 
        self.update_ROI_graph()
        
    def callback_property_changed(self):
        self.update_graph()
    
    def callback_clear_plotting_data(self):
        """"""
        self.data_plotting = OrderedDict()
        self.curve_highlighted = []
        self.update_graph()
    
    def callback_graph_index_combobox_changed(self, index):
        """Add clicked config graph to Data plotting area"""
        print(index)
#         if index == self.graph_number:
#             # choose new
#             self.graph_number += 1
#             # add a graph
#             graph_widget = pg.GraphicsLayoutWidget()
#             graph_widget.addPlot(row=0, col=0)
#             self.graph_lines_dict.setdefault(graph_widget, 0)
#             for data in self.data_plotting:
#                 data[1].clear()
#                 for i in range(1, self.graph_number + 1):
#                     data[1].addItem(str(i))
#                 data[1].addItem('New')
#         else:
#             # change current curve's graph
#             pass
     
    def callback_visible_checkBox(self, checked):
        """Set the curve visible or invisible"""
        if checked:
            pass
        else:
            pass
    
    def callback_ROI_triggered(self):
        """Show the graph"""
        if self.ROI_showed:
            self.detail_graph.hide()
            self.ROI_region.hide()
            self.ROI_showed = not self.ROI_showed
        else:
            self.update_ROI_graph()
            self.detail_graph.show()
            self.ROI_region.show()
            self.ROI_showed = not self.ROI_showed
    
    def update_ROI_graph(self):
        items_to_be_removed = []
        for item in self.detail_graph.items:
            if isinstance(item, pg.PlotDataItem):
                items_to_be_removed.append(item)
                
        for item in items_to_be_removed:
            self.detail_graph.removeItem(item)
            
        items = self.main_graph_t.items
        for item in items:
            if isinstance(item, pg.PlotDataItem):
                self.detail_graph.plot(item.xData, item.yData, symbol=item.opts['symbol'], pen=item.opts['pen'])
    
    def load_data(self):
        log_data = ULog(str(self.log_file_name))
        self.log_info_data = {index:value for index,value in log_data.msg_info_dict.items() if 'perf_' not in index}
        self.log_info_data['SW version'] = log_data.get_version_info_str()
        self.log_params_data = log_data.initial_parameters
        self.log_params_data = OrderedDict([(key, self.log_params_data[key]) for key in sorted(self.log_params_data)])
        self.log_data_list = log_data.data_list
        self.data_dict = OrderedDict()
        for d in self.log_data_list:
            data_items_list = [f.field_name for f in d.field_data]
            data_items_list.remove('timestamp')
            data_items_list.insert(0, 'timestamp')
            data_items = [(item, str(d.data[item].dtype), str(len(d.data[item]))) for item in data_items_list]
            # add suffix to distinguish same name
            i = 0
            name = d.name
            while True:
                if i > 0:
                    name = d.name + '_' + str(i)
                if name in self.data_dict:
                    i += 1
                else:
                    break
            self.data_dict.setdefault(name, data_items[1:])    
#         pdb.set_trace()
        # attitude
        index = list(self.data_dict.keys()).index('vehicle_attitude')
        self.time_stamp_attitude = self.log_data_list[index].data['timestamp']/10**6
        q0 = self.log_data_list[index].data['q[0]']
        q1 = self.log_data_list[index].data['q[1]']
        q2 = self.log_data_list[index].data['q[2]']
        q3 = self.log_data_list[index].data['q[3]']
        self.attitude_history = self.quat_to_euler(q0, q1, q2, q3)
        index = list(self.data_dict.keys()).index('vehicle_attitude_setpoint')
        self.time_stamp_attitude_setpoint = self.log_data_list[index].data['timestamp']/10**6
        q0_d = self.log_data_list[index].data['q_d[0]']
        q1_d = self.log_data_list[index].data['q_d[1]']
        q2_d = self.log_data_list[index].data['q_d[2]']
        q3_d = self.log_data_list[index].data['q_d[3]']
        self.attitude_setpoint_history = self.quat_to_euler(q0_d, q1_d, q2_d, q3_d)
        # position
        index = list(self.data_dict.keys()).index('vehicle_local_position')
        self.time_stamp_position = self.log_data_list[index].data['timestamp']/10**6
        x = self.log_data_list[index].data['x']
        y = self.log_data_list[index].data['y']
        z = self.log_data_list[index].data['z']
        self.position_history = [(x[i]*self.SCALE_FACTOR, y[i]*self.SCALE_FACTOR, 
                                  z[i]*self.SCALE_FACTOR) for i in range(len(x))]
        # motor rotation
        index = list(self.data_dict.keys()).index('actuator_outputs')
        self.time_stamp_output = self.log_data_list[index].data['timestamp']/10**6
        output0 = self.log_data_list[index].data['output[0]']
        output1 = self.log_data_list[index].data['output[1]']
        output2 = self.log_data_list[index].data['output[2]']
        output3 = self.log_data_list[index].data['output[3]']
        self.output_history = [(output0[i], output1[i], output2[i], output3[i]) for i in range(len(output0))]
        
        # get common time range
        self.time_range = max([self.time_stamp_attitude[0], self.time_stamp_output[0], self.time_stamp_position[0]]), \
                            min([self.time_stamp_attitude[-1], self.time_stamp_output[-1], self.time_stamp_position[-1]])
        self.data_loaded = True
        
    def load_data_tree(self):
        # update the tree list table
        self.item_list_treeWidget.clear()
        for key, values in self.data_dict.items():
            param_name = QtGui.QTreeWidgetItem(self.item_list_treeWidget, [key])
            self.item_list_treeWidget.expandItem(param_name)
            for data_name in values:
                self.item_list_treeWidget.expandItem(
                    QtGui.QTreeWidgetItem(param_name, [data_name[0], data_name[1], data_name[2]]))
            param_name.setExpanded(False)
            
    def update_graph_after_log_changed(self):
        # after load_data_tree
        data_plotting = OrderedDict()
        if self.data_plotting:
            data_keys, data_values = list(self.data_dict.keys()), list(self.data_dict.values())
            for item_id, item in self.data_plotting.items():
                item_label, showed, curve = item
                t, data = curve.xData, curve.yData
                parent_name, data_name = item_label.split('->')
                found = False
                if parent_name in data_keys:
                    for item in data_values[data_keys.index(parent_name)]:
                        if data_name == item[0]:
                            found = True
                if found:
                    data_index = list(list(self.data_dict.keys())).index(parent_name)
                    t = self.log_data_list[data_index].data['timestamp']/10**6
                    data = self.log_data_list[data_index].data[data_name]
                    curve.setData(t, data)
                    data_plotting[item_id] = [item_label, showed, curve]
            self.data_plotting = data_plotting
            self.update_graph()
        
    def quadrotor_win_closed_event(self, closed):
        if closed:
            self.quadrotor_widget_isshowed = not self.quadrotor_widget_isshowed
            self.show_quadrotor_3d.setIcon(QtGui.QIcon(get_source_name('icons/quadrotor.gif')))
    
    def draw_predefined_graph(self, name):
        
        def add_context_action(ax):
            def callback(*args, **kargs):
                for item in ax.items():
                    if isinstance(item, pg.PlotDataItem):
                        if item.opts['symbol'] is None:
                            item.setData(item.xData, item.yData, symbol='s')
                        else:
                            item.setData(item.xData, item.yData, symbol=None) 
            return callback
        
        if name == 'XY_Estimation':
            graph_xy =  pg.GraphicsLayoutWidget()
            self.default_tab.addTab(graph_xy, name)
            ax = graph_xy.addPlot(row=0, col=0)
            show_marker_action = QtGui.QAction('show/hide marker', graph_xy)
            show_marker_action.triggered.connect(add_context_action(ax))
            data_index = list(list(self.data_dict.keys())).index('vehicle_local_position')
            x = self.log_data_list[data_index].data['x']
            y = self.log_data_list[data_index].data['y']
            # plot the xy trace line in red
            ax.plot(x, y, pen=(255, 0, 0))
            
    def closeEvent(self, *args, **kwargs):
        if self.analysis_graphs_showed:
            self.analysis_graphs_pane.close()
        if self.params_pane_showed:
            self.params_pane.close()
        if self.info_pane_showed:
            self.info_pane.close()
        if self.help_pane_showed:
            pass
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)
            
    
def main():
    def func():
        print(app.focusWidget())
    app = QtGui.QApplication(sys.argv)
    app.focusChanged.connect(func)
    mainwin = MainWindow()
    mainwin.show()
    print(app.focusWidget())
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
