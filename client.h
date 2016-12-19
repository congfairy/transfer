#ifndef _CLIENT_HEADER_
#define _CLIENT_HEADER_
#include <iostream>
#include <Python.h>
using namespace std;
void transfer(const char *action,const char *host,const char *filepath,const char *targetdir,const char *uid,const char *gid,const char *position,const char *size);
#endif
