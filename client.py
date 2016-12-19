from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.simple_httpclient import SimpleAsyncHTTPClient
import tornado.ioloop
import tornado.web
import os,sys
from tornado import gen
from functools import partial
#import time,datatime


total_downloaded = 0
#action = sys.argv[1]
#filepath = sys.argv[2]
#uid = sys.argv[3]
#gid = sys.argv[4]
#pos = sys.argv[5]
def geturl(action,host,filepath,uid,gid,pos,size):
    if action=="read":
 #       uid = sys.argv[3]
  #      gid = sys.argv[4]
   #     pos = sys.argv[5]
        url = "http://"+host+":8888/read?filepath="+filepath+"&uid="+uid+"&gid="+gid+"&pos="+pos+"&size="+size
        print(url) 
        return url


def chunky(path, chunk):
#   print("self._max_body_size",self._max_body_size)
   global total_downloaded
   total_downloaded += len(chunk)
   print("chunk size",len(chunk))
   # the OS blocks on file reads + writes -- beware how big the chunks is as it could effect things
   with open(path, 'ab') as f:
       f.write(chunk)

@gen.coroutine
def writer(action,host,filepath,targetdir,uid,gid,pos,size):
   print("writer function")
#   tornado.ioloop.IOLoop.instance().start()
   file_name = targetdir+os.path.basename(filepath)
   if os.path.exists(targetdir):
       pass
   else:
       os.mkdir(targetdir)
   f = open(file_name,'w')
   f.close()
   request = HTTPRequest(geturl(action,host,filepath,uid,gid,pos,size), streaming_callback=partial(chunky, file_name))
   AsyncHTTPClient.configure('tornado.simple_httpclient.SimpleAsyncHTTPClient', max_body_size=512*1024*1024)
   http_client = AsyncHTTPClient(force_instance=True)
   #http_client.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient",max_body_size=524288000)
   response = yield http_client.fetch(request)
   tornado.ioloop.IOLoop.instance().stop()
   print("total bytes downloaded was", total_downloaded)

def entrance(action,host,filepath,targetdir,uid,gid,pos,size):
   #print("entrance function")
   writer(action,host,filepath,targetdir,uid,gid,pos,size)
   tornado.ioloop.IOLoop.instance().start()


