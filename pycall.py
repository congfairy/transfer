from ctypes import *
import os


#ll=ctypes.cdll.LoadLibrary
#lib=ll('./libpycall.so')
#p=lib.foo(1,3)
#lib.update_bitmap(52,111,ctypes.c_char_p("/root/leaf/night.mkv"))
#print "result=%d"%p
#print("finish")
lib=cdll.LoadLibrary('./libpycall1.so')
print("start")
func=lib.update_bitmap
func.argtypes=(c_int,c_int,c_char_p)
func=lib.update_bitmap(52,111,"/root/leaf/pytoc/upload/night.mkv".encode("utf-8"))
print("finish")
