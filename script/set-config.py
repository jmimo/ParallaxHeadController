import ctypes, os

PTR = ctypes.pointer

GP_OK = 0
GP_CAPTURE_IMAGE = 0
GP_FILE_TYPE_NORMAL = 1

GP_WIDGET_WINDOW = 0  # Window widget This is the toplevel configuration widget. It should likely contain multiple GP_WIDGET_SECTION entries.
GP_WIDGET_SECTION = 1 # Section widget (think Tab).
GP_WIDGET_TEXT = 2    # Text widget.
GP_WIDGET_RANGE = 3   # Slider widget.
GP_WIDGET_TOGGLE = 4  # Toggle widget (think check box).
GP_WIDGET_RADIO = 5   # Radio button widget.
GP_WIDGET_MENU = 6    # Menu widget (same as RADIO).
GP_WIDGET_BUTTON = 7  # Button press widget.
GP_WIDGET_DATE = 8    # Date entering widget.

gp = ctypes.CDLL('/usr/lib/libgphoto2.so.2')

class CameraFilePath(ctypes.Structure):
	_fields_=[('name', (ctypes.c_char * 128)),('folder', (ctypes.c_char * 1024))]

class Widget(object):
    def __init__(self):
	self._w = ctypes.c_void_p()

    def set_value(self,value):
	check(gp.gp_widget_set_value(self._w,str(value)))

class libgphoto2error(Exception):
    def __init__(self, result, message):
        self.result = result
        self.message = message
    def __str__(self):
        return self.message + ' (' + str(self.result) + ')'

def check(result):
    if result < 0:
        gp.gp_result_as_string.restype = ctypes.c_char_p
        message = gp.gp_result_as_string(result)
        raise libgphoto2error(result, message)
    return result



def retrieveWidget(parent, name):
	child = Widget()
	ret = gp.gp_widget_get_child_by_name(parent._w,str(name),PTR(child._w))
	if(ret != 0):
		check(gp.gp_widget_get_child_by_label(parent._w,str(name),PTR(child._w)))
	return child;

def setConfig(name, value):
	main = Widget()
	check(gp.gp_camera_get_config(camera,PTR(main._w),context))
	tokens = name.split('/')
	parent = main
	child = None
	for token in tokens:
		child = retrieveWidget(parent,token)
		parent = child
	child.set_value(value)
	check(gp.gp_camera_set_config(camera,main._w,context))

def getWidgetName(widget):
	name = ctypes.c_char_p()
        gp.gp_widget_get_name(widget._w, PTR(name))
        return name.value

def getWidgetType(widget):
        type = ctypes.c_int()
        gp.gp_widget_get_type(widget._w, PTR(type))
        return type.value

def getWidgetValue(widget):
        value = ctypes.c_void_p()
        ans = gp.gp_widget_get_value(widget._w, PTR(value))
        if getWidgetType(widget) in [GP_WIDGET_MENU, GP_WIDGET_RADIO, GP_WIDGET_TEXT]:
            value = ctypes.cast(value.value, ctypes.c_char_p)
        elif getWidgetType(widget) == GP_WIDGET_RANGE:
            value = ctypes.cast(value.value, ctypes.c_float_p)
        elif getWidgetType(widget) in [GP_WIDGET_TOGGLE, GP_WIDGET_DATE]:
            #value = ctypes.cast(value.value, ctypes.c_int_p)
            pass
        else:
            return None
        return value.value

def printCaptureTarget():
	main = Widget()
	check(gp.gp_camera_get_config(camera,PTR(main._w),context))
	capturetarget = retrieveWidget(main,'capturetarget')
	print "Widget name: [%s] type: [%s] value: [%s]" % (getWidgetName(capturetarget),getWidgetType(capturetarget),getWidgetValue(capturetarget))
#
# init camera
#
context = gp.gp_context_new()
camera = ctypes.c_void_p()
gp.gp_camera_new(ctypes.pointer(camera))
gp.gp_camera_init(camera, context)

#
# set config
#gp_widget_set_value

# '/main/capturesettings/aperture'

printCaptureTarget()

setConfig('capturetarget','Memory card')

printCaptureTarget()

setConfig('capturesettings/aperture','18')
setConfig('capturesettings/shutterspeed','1/250')

#####
##### 
#####

cam_path = CameraFilePath()  
gp.gp_camera_capture(camera,GP_CAPTURE_IMAGE,ctypes.pointer(cam_path),context)

print "CameraPath folder: [%s] name: [%s]" % (str(cam_path.folder),str(cam_path.name))

'''
#
# capture image
#

cam_path = CameraFilePath()  

gp.gp_camera_capture(camera,GP_CAPTURE_IMAGE,ctypes.pointer(cam_path),context)

#
# download and delete
#

cam_file = ctypes.c_void_p()  
fd = os.open('image.cr2', os.O_CREAT | os.O_WRONLY)  
gp.gp_file_new_from_fd(ctypes.pointer(cam_file), fd)  
gp.gp_camera_file_get(camera,  
                      cam_path.folder,  
                      cam_path.name,  
                      GP_FILE_TYPE_NORMAL,  
                      cam_file,  
                      context)  
gp.gp_camera_file_delete(camera,  
                         cam_path.folder,  
                         cam_path.name,  
                         context)  
gp.gp_file_unref(cam_file) 
'''
#
# release
#
gp.gp_camera_exit(camera, context)  
gp.gp_camera_unref(camera)
