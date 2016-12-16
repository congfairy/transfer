#include "client.h"
void transfer(const char *action,const char *host,const char *filepath,const char *uid,const char *gid,const char *position)
{
 
 Py_Initialize();
 if(Py_IsInitialized())
 {
   printf("can't initialize\n");
 }
 PyObject * pModule = NULL;
 PyObject * pFunc = NULL;
 PyObject * result = NULL;
 PyRun_SimpleString("import sys");  
 PyRun_SimpleString("import os");
 PyRun_SimpleString("import string");
 PyRun_SimpleString("sys.path.append('./')");
 PyObject *pArgs = PyTuple_New(6);   
 PyTuple_SetItem(pArgs,0,Py_BuildValue("s",action));  
 PyTuple_SetItem(pArgs,1,Py_BuildValue("s",host));  
 PyTuple_SetItem(pArgs,2,Py_BuildValue("s",filepath));
 PyTuple_SetItem(pArgs,3,Py_BuildValue("s",uid));  
 PyTuple_SetItem(pArgs,4,Py_BuildValue("s",gid));  
 PyTuple_SetItem(pArgs,5,Py_BuildValue("s",position));  
 pModule = PyImport_ImportModule("client");
 if(pModule == NULL)
 {
   printf("can't python file\n");
 }
 pFunc = PyObject_GetAttrString(pModule,"entrance");
 if(pFunc == NULL)
 {
   printf("can't load function\n");
 }
 result = PyEval_CallObject(pFunc,pArgs);
 Py_DECREF(pArgs);
 if(result == NULL)
     cout<<"null"<<endl;
 Py_DECREF(result);
 Py_Finalize();
 //return 0;

}
