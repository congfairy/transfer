from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.simple_httpclient import SimpleAsyncHTTPClient
import tornado.ioloop
import tornado.web
import os,sys
from tornado import gen
from functools import partial
import urllib.parse
import mimetypes
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
import tornado.iostream
from tornado.escape import utf8
from tornado.log import gen_log
#import time,datatime

total_downloaded = 0
threadpool = ThreadPoolExecutor(1)  # A thread for reading chunks from the file

DEBUG = False

class NoQueueTimeoutHTTPClient(SimpleAsyncHTTPClient):
    def fetch_impl(self, request, callback):
        key = object()

        self.queue.append((key, request, callback))
        self.waiting[key] = (request, callback, None)

        self._process_queue()

        if self.queue:
            gen_log.debug("max_clients limit reached, request queued. %d active, %d queued requests." % (len(self.active), len(self.queue)))


class Client:
    def _gen_boundary(self, file_size):
        if file_size < 1024:
            blen = 10
        else:
            blen = math.ceil(math.log(file_size, 2))
        bcnt = max(blen / 32, 1)
        return "".join([str(uuid.uuid1()).replace("-", "") for _ in range(bcnt)])

    def put_stream(self, url, filename, on_response, chunk_size=8192):
        """Uploads file to provided url.

        :param url: URL to PUT the file data to
        :param filename: Name of the file (Content-Disposition header)
        :param file_size: Size of the file in bytes. Used to produce a Content-Size header from file_size.
        :param on_response: See AsyncHTTPClient.fetch

        :return: Future content value under the provided url as binary string.
        """
        
        print("filename is :",filename)
        file_size = os.path.getsize(filename)  # Be aware: this could also block! In production, you need to do this in a separated thread too!

        ext = os.path.splitext(filename)[1].lower()
        if ext:
            content_type = mimetypes.types_map.get(ext, "application/octet-stream")
        else:
            content_type = "application/octet-stream"

        enc_filename = urllib.parse.quote(filename)
        # http://stackoverflow.com/questions/4526273/what-does-enctype-multipart-form-data-mean/28380690#28380690
        boundary = self._gen_boundary(file_size)
        CRLF = '\r\n'
        post_head = b''.join(map(utf8, [
            '--', boundary, CRLF,
            # See https://tools.ietf.org/html/rfc5987 section 3.2.2 examples
            'Content-Disposition: form-data; name="file"; filename*=utf-8\'\'%s' % enc_filename, CRLF,
            'Content-Type: ', content_type, CRLF,
            'Content-Transfer-Encoding: binary', CRLF,
            CRLF,
        ]))
        post_tail = b''.join(map(utf8, [
            CRLF, '--', boundary, '--', CRLF
        ]))
        content_length = len(post_head) + int(file_size) + len(post_tail)
        headers = {
            'Content-Type': 'multipart/form-data; boundary=' + boundary,
            'Content-Transfer-Encoding': 'binary',
            'Content-Length': str(content_length),
        }

        @gen.coroutine
        def body_producer(write):
            if DEBUG:
                sys.stdout.write(post_head.decode('ascii'))
            write(post_head)
            remaining = file_size
            with open(filename, "rb") as fileobj:
                while remaining > 0:
                    data = yield threadpool.submit(fileobj.read, chunk_size)
                    if data:
                        remaining -= len(data)
                        if DEBUG:
                            sys.stdout.write(data.decode('utf-8'))
                        yield write(data)
                    else:
                        break
            if DEBUG:
                sys.stdout.write(post_tail.decode('ascii'))
            write(post_tail)

        request = tornado.httpclient.HTTPRequest(url=url, request_timeout=1200, method='POST', headers=headers,
                                                 body_producer=body_producer)
        return tornado.httpclient.AsyncHTTPClient().fetch(request, callback=on_response)


def geturl(action,host,filepath,uid,gid,pos,size):
    if action=="read":
        url = "http://"+host+"/read?filepath="+filepath+"&uid="+uid+"&gid="+gid+"&pos="+pos+"&size="+size
        print(url) 
        return url

def geturl(action,host,targetpath):
    if action=="upload":
        url = "http://"+host+"/upload?targetpath="+targetpath
        print(url) 
        return url

def chunky(path, chunk):
#   print("self._max_body_size",self._max_body_size)
    global total_downloaded
    total_downloaded += len(chunk)
  # print("chunk size",len(chunk))
   # the OS blocks on file reads + writes -- beware how big the chunks is as it could effect things
    with open(path, 'ab') as f:
        f.write(chunk)

@gen.coroutine
def writer(host,filepath,targetdir,uid,gid,pos,size):
   print("writer function")
#   tornado.ioloop.IOLoop.instance().start()
   file_name = targetdir+os.path.basename(filepath)
   if os.path.exists(targetdir):
       pass
   else:
       os.makedirs(targetdir)
   f = open(file_name,'w')
   f.close()
   request = HTTPRequest(geturl("read",host,filepath,uid,gid,pos,size), streaming_callback=partial(chunky, file_name))
   AsyncHTTPClient.configure('tornado.simple_httpclient.SimpleAsyncHTTPClient', max_body_size=512*1024*1024)
   http_client = AsyncHTTPClient(force_instance=True)
   #http_client.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient",max_body_size=524288000)
   response = yield http_client.fetch(request)
   tornado.ioloop.IOLoop.instance().stop()
   print("total bytes downloaded was", total_downloaded)

@gen.coroutine
def upload(host,filepath,targetpath):
    def on_response(request):
        print("=============== GOT RESPONSE ======")
        print(request.body.decode('ascii'))
        #print(request.body)
        print("===================================")
        tornado.ioloop.IOLoop.current().stop() # Stop the loop when the upload is omplete.

    client = Client()
    yield client.put_stream(geturl("upload",host,targetpath), filepath, on_response)



def readentrance(host,filepath,targetdir,uid,gid,pos,size):
   #print("entrance function")
    writer(host,filepath,targetdir,uid,gid,pos,size)
    tornado.ioloop.IOLoop.instance().start()

def uploadentrance(host,filepath,targetpath):
    upload(host,filepath,targetpath)
    tornado.ioloop.IOLoop.instance().start()


