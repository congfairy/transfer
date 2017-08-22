import ctypes
ll=ctypes.cdll.LoadLibrary
lib=ll("./libpycall.so")
lib.update_bitmap(1048576, 2097152, "/root/leaf/pytoc/upload/test.log", 629146148)
print ("finish")
