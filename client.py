from tornado.httpclient import HTTPRequest, AsyncHTTPClient
import tornado.ioloop
import tornado.web
import os,sys
from tornado import gen
from functools import partial

total_downloaded = 0
#action = sys.argv[1]
#filepath = sys.argv[2]
#uid = sys.argv[3]
#gid = sys.argv[4]
#pos = sys.argv[5]
def geturl(action,host,filepath,uid,gid,pos):
    if action=="read":
 #       uid = sys.argv[3]
  #      gid = sys.argv[4]
   #     pos = sys.argv[5]
        url = "http://"+host+":8880/read?filepath="+filepath+"&uid="+uid+"&gid="+gid+"&pos="+pos
        print(url) 
        return url


def chunky(path, chunk):
#   print("self._max_body_size",self._max_body_size)
   global total_downloaded
   total_downloaded += len(chunk)
   print("chunk size",len(chunk))
   # the OS blocks on file reads + writes -- beware how big the chunks is as it could effect things
   with open(path, 'a+b') as f:
       f.write(chunk)

@gen.coroutine
def writer(action,host,filepath,uid,gid,pos):
   print("writer function")
#   tornado.ioloop.IOLoop.instance().start()
   file_name = os.path.basename(filepath)+"_new"
   f = open(os.path.basename(filepath)+"_new",'w')
   f.close()
   request = HTTPRequest(geturl(action,host,filepath,uid,gid,pos), streaming_callback=partial(chunky, file_name))
   http_client = AsyncHTTPClient()
   response = yield http_client.fetch(request)
   tornado.ioloop.IOLoop.instance().stop()
   print("total bytes downloaded was", total_downloaded)

def entrance(action,host,filepath,uid,gid,pos):
   print("entrance function")
   writer(action,host,filepath,uid,gid,pos)
   tornado.ioloop.IOLoop.instance().start()


