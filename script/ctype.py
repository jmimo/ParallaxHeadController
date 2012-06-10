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

class CameraAbilities(ctypes.Structure):
    _fields_ = [('model', (ctypes.c_char * 128)),
                ('status', ctypes.c_int),
                ('port', ctypes.c_int),
                ('speed', (ctypes.c_int * 64)),
                ('operations', ctypes.c_int),
                ('file_operations', ctypes.c_int),
                ('folder_operations', ctypes.c_int),
                ('usb_vendor', ctypes.c_int),
                ('usb_product', ctypes.c_int),
                ('usb_class', ctypes.c_int),
                ('usb_subclass', ctypes.c_int),
                ('usb_protocol', ctypes.c_int),
                ('library', (ctypes.c_char * 1024)),
                ('id', (ctypes.c_char * 1024)),
                ('device_type', ctypes.c_int),
                ('reserved2', ctypes.c_int),
                ('reserved3', ctypes.c_int),
                ('reserved4', ctypes.c_int),
                ('reserved5', ctypes.c_int),
                ('reserved6', ctypes.c_int),
                ('reserved7', ctypes.c_int),
                ('reserved8', ctypes.c_int)]

class CameraWidget(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int),
                ('label', (ctypes.c_char * 256)),
                ('info', (ctypes.c_char * 1024)),
                ('name', (ctypes.c_char * 256)),
                ('parent', (ctypes.c_void_p)),
                ('value_string', ctypes.c_char_p),
                ('value_int', ctypes.c_int),
                ('value_float', ctypes.c_float),
                ('choice', (ctypes.c_void_p)),
                ('choice_count', ctypes.c_int),
                ('min', ctypes.c_float),
                ('max', ctypes.c_float),
                ('increment', ctypes.c_float),
                ('children', (ctypes.c_void_p)),
                ('children_count', (ctypes.c_int)),
                ('changed', (ctypes.c_int)),
                ('readonly', (ctypes.c_int)),
                ('ref_count', (ctypes.c_int)),
                ('id', (ctypes.c_int)),
                ('callback', (ctypes.c_void_p))]

class cameraAbilities(object):
    def __init__(self):
        self._ab = CameraAbilities()

    def __repr__(self):
        return "Model : %s\nStatus : %d\nPort : %d\nOperations : %d\nFile Operations : %d\nFolder Operations : %d\nUSB (vendor/product) : 0x%x/0x%x\nUSB class : 0x%x/0x%x/0x%x\nLibrary : %s\nId : %s\n" % (self._ab.model, self._ab.status, self._ab.port, self._ab.operations, self._ab.file_operations, self._ab.folder_operations, self._ab.usb_vendor, self._ab.usb_product, self._ab.usb_class, self._ab.usb_subclass, self._ab.usb_protocol, self._ab.library, self._ab.id)

    model = property(lambda self: self._ab.model, None)
    status = property(lambda self: self._ab.status, None)
    port = property(lambda self: self._ab.port, None)
    operations = property(lambda self: self._ab.operations, None)
    file_operations = property(lambda self: self._ab.file_operations, None)
    folder_operations = property(lambda self: self._ab.folder_operations, None)
    usb_vendor = property(lambda self: self._ab.usb_vendor, None)
    usb_product = property(lambda self: self._ab.usb_product, None)
    usb_class = property(lambda self: self._ab.usb_class, None)
    usb_subclass = property(lambda self: self._ab.usb_subclass, None)
    usb_protocol = property(lambda self: self._ab.usb_protocol, None)
    library = property(lambda self: self._ab.library, None)
    id = property(lambda self: self._ab.id, None)



class cameraWidget(object):

    def __init__(self, type = None, label = ""):
        self._w = ctypes.c_void_p()
        if type is not None:
            gp.gp_widget_new(int(type), str(label), PTR(self._w))
            gp.gp_widget_ref(self._w)
        else:
            self._w = ctypes.c_void_p()

    def _get_name(self):
        name = ctypes.c_char_p()
        gp.gp_widget_get_name(self._w, PTR(name))
        return name.value
    def _set_name(self, name):
        gp.gp_widget_set_name(self._w, str(name))
    name = property(_get_name, _set_name)

    def _get_type(self):
        type = ctypes.c_int()
        gp.gp_widget_get_type(self._w, PTR(type))
        return type.value
    type = property(_get_type, None)

    def _get_value(self):
        value = ctypes.c_void_p()
        ans = gp.gp_widget_get_value(self._w, PTR(value))
        if self.type in [GP_WIDGET_MENU, GP_WIDGET_RADIO, GP_WIDGET_TEXT]:
            value = ctypes.cast(value.value, ctypes.c_char_p)
        elif self.type == GP_WIDGET_RANGE:
            value = ctypes.cast(value.value, ctypes.c_float_p)
        elif self.type in [GP_WIDGET_TOGGLE, GP_WIDGET_DATE]:
            #value = ctypes.cast(value.value, ctypes.c_int_p)
            pass
        else:
            return None
        ans
        return value.value
    def _set_value(self, value):
        if self.type in (GP_WIDGET_MENU, GP_WIDGET_RADIO, GP_WIDGET_TEXT):
            value = ctypes.c_char_p(value)
        elif self.type == GP_WIDGET_RANGE:
            value = ctypes.c_float_p(value) # this line not tested
        elif self.type in (GP_WIDGET_TOGGLE, GP_WIDGET_DATE):
            value = PTR(ctypes.c_int(value))
        #else:
            #return None # this line not tested
        gp.gp_widget_set_value(self._w, value)
    value = property(_get_value, _set_value)

    def set_value(self, value):
	self.value = value
	self._set_value(str(value))
	

    def __repr__(self):
	return "%s:%s" % (self.name,self.value)

#
# init camera
#
context = gp.gp_context_new()
camera = ctypes.c_void_p()
gp.gp_camera_new(ctypes.pointer(camera))
gp.gp_camera_init(camera, context)

#ab = cameraAbilities()

#gp.gp_camera_get_abilities(camera,PTR(ab._ab))


# print aperture widget
'''
main = CameraWidget()
gp.gp_widget_new(int(0),str('main'),PTR(main))
gp.gp_widget_ref(main)
gp.gp_camera_get_config(camera,PTR(main),context)

capturesettings = CameraWidget()
gp.gp_widget_new(int(1),str('capturesettings'),PTR(capturesettings))
gp.gp_widget_ref(capturesettings)
gp.gp_camera_get_config(camera,PTR(capturesettings),context)
'''
aperture = CameraWidget()
gp.gp_widget_new(int(2),str('aperture'),PTR(aperture))
gp.gp_widget_ref(aperture)
gp.gp_camera_get_config(camera,PTR(aperture),context)

print aperture.value_string

'''
main = cameraWidget(GP_WIDGET_WINDOW)

gp.gp_camera_get_config(camera,PTR(main._w),context)

print main

gp.gp_widget_get_child_by_name(main._w,str('capturesettings'),PTR(main._w))

print main

gp.gp_widget_get_child_by_name(main._w,str('aperture'),PTR(main._w))

print main

main.set_value('18')


print main

# write config

gp.gp_camera_set_config(camera,PTR(main._w),context)
'''

# /main/capturesettings/aperture
# /main/capturesettings/shutterspeed

#
# capture image
#
'''
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
