#ifndef _CLIENT_HEADER_
#define _CLIENT_HEADER_
#include <iostream>
#include <Python.h>
using namespace std;
void transread(const char *host,const char *filepath,const char *targetdir,const char *uid,const char *gid,const char *position,const char *size);
void transupload(const char *host,const char *filepath,const char *targetdir);
#endif
