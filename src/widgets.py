
from __future__ import division
import time
import pkg_resources
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_SHININESS
from pyqtgraph.Qt import QtCore,QtGui,QtOpenGL
from objloader import WFObject
import numpy as np
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

def rotate_model(yaw,roll,pitch):
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

class InfoWin(QtGui.QMainWindow):
    closed = pyqtSignal(bool)
    
    def __init__(self, info_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(QtCore.QSize(500,500))
        self.info_table = QtGui.QTableWidget()
        self.setCentralWidget(self.info_table)
        self.info_table.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | 
                                                     QtGui.QAbstractItemView.SelectedClicked)
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
        

class QuadrotorWin(QtGui.QMainWindow):
    closed = pyqtSignal(bool)
    
    def __init__(self,*args,**kwargs):
        super(QuadrotorWin,self).__init__(*args,**kwargs)
        self.toolBar = self.addToolBar('showSetting')
        self.trace_show = QtGui.QAction(QtGui.QIcon(get_source_name('icons/trace.gif')),'show trace',self)
        self.trace_show.triggered.connect(self.callback_show_trace)
        self.trace_showed = False
        self.vector_show = QtGui.QAction(QtGui.QIcon(get_source_name('icons/rotor_vector.gif')),'show rotation speed vector',self)
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
        self.far = 500
        
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
        if self.eye_R > 5:
            self.eye_R += self.scale_ratio * scale_size
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
        self.setScale(event.delta())

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
            self.drone_position = pos
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
