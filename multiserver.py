import tornado.ioloop
import tornado.httpserver
from  tornado.web import RequestHandler, Application, url, stream_request_body
import tornado.options
from tornado import gen
import os,sys,re,time
from stat import *
from tornado.options import define, options
from os.path import getsize
import datetime
sys.path.insert(0, os.pardir)
# noinspection PyPep8
from tornadostreamform.multipart_streamer import MultiPartStreamer, StreamedPart, TemporaryFileStreamedPart
from tornadostreamform.bandwidthmonitor import BandwidthMonitor, format_speed, format_size

define("port",default=8000,help="run on the givin port",type=int)
"""Important knowledge for Tornado users: nax_buffer_size and max_body_size should be low by default.
The biggest file that can be POST-ed should be specified in the prepare() method of the stream_request_body handler.

For details see: https://groups.google.com/forum/#!topic/python-tornado/izEXQd71rQk
"""
MB = 1024 * 1024
GB = 1024 * MB
TB = 1024 * GB

MAX_BUFFER_SIZE = 4 * MB  # Max. size loaded into memory!
MAX_BODY_SIZE = 4 * MB  # Max. size loaded into memory!
MAX_STREAMED_SIZE = 0.5 * TB  # Max. size streamed in one request!
TMP_DIR = '/home/wangcong/leaf/mufd'  # Path for storing streamed temporary files. Set this to a directory that receives the files.


class MyStreamer(MultiPartStreamer):
    """You can create your own multipart streamer, and override some methods."""

    def __init__(self, total):
        super().__init__(total)
        self._last_progress = 0.0  # Last time of updating the progress
        self.bwm = BandwidthMonitor(total)  # Create a bandwidth monitor

    def create_part(self, headers):
        """In the create_part method, you should create and return StreamedPart instance.

        :param headers: A dict of header values for the new part to be created.

        For example, you can write your own StreamedPart descendant that streams data into a process (through a
        pipe) or send it on the network with another tornado.httpclient etc. You just need to make sure that you
        use async I/O operations that are supported by tornado. If you do not override this method,
        then the default create_part() method that creates a TemporaryFileStreamedPart instance for you. and it
        will stream file data into the system default temporary directory.
        """
        global TMP_DIR

        # you can use a dummy StreamedPart to examine the headers, as shown below.
        dummy = StreamedPart(self, headers)
        print("Starting new part, is_file=%s, headers=%s" % (dummy.is_file(), headers))

        # This is how you create a streamed file in a given directory.
        return  TemporaryFileStreamedPart(self, headers, tmp_dir=TMP_DIR)
        # The default method creates a TemporaryFileStreamedPart with default tmp_dir.
        # return super().create_part(headers)

    def data_received(self, chunk):
        """This method is called when data has arrived for the form.

        :param chunk: Binary string, data chunk received from the client.

        The default implementation does incremental parsing of the data, calls create_part for each part
        in the multipart/form-data and feeds data into the parts.

        In this example, we also monitor the upload speed / bandwidth for the upload."""
        super().data_received(chunk)
        self.bwm.data_received(len(chunk))  # Monitor bandwidth changes

    def on_progress(self, received, total):
        """The on_progress method is called when data is received but **before** it is fed into the current part.

        :param received: Number of bytes received
        :param total: Total bytes to be received.

        For the demonstration, we calculate the progress percent and remaining time of the upload, and display it.
        """
        if self.total:
            now = time.time()
            if now - self._last_progress > 0.5:
                self._last_progress = now

                percent = round(received * 1000 // total) / 10.0
                # Calculate average speed from the last 10*self.bwm.hist_interval = 5 seconds.
                speed = self.bwm.get_avg_speed(look_back_steps=10)
                if speed:
                    s_speed = format_speed(speed)
                    remaining_time = self.bwm.get_remaining_time(speed)
                    if remaining_time is not None:
                        mins = int(remaining_time / 60)
                        secs = int(remaining_time - mins * 60)
                        s_remaining = "%s:%s" % (
                            str(mins).rjust(2, '0'),
                            str(secs).rjust(2, '0'),
                        )
                    else:
                        s_remaining = "?"
                else:
                    s_speed = "?"
                    s_remaining = "?"
                now = datetime.datetime.now()
                now.strftime('%Y-%m-%d %H:%M:%S')  
                sys.stdout.write("  %.1f%% speed=%s remaining time=%s\n" % (percent, s_speed, s_remaining))
                sys.stdout.flush()

    def examine(self):
        """Debug method: print the structure of the multipart form to stdout."""
        for part in self.parts:
            print("examine function filename",part.get_filename())
            print("PART name=%s, filename=%s, size=%s" % (part.get_name(), part.get_filename(), part.get_size()))
            for hdr in part.headers:
                print("\tHEADER name=%s" % hdr.get("name", "???"))
                for key in sorted(hdr.keys()):
                    if key.lower() != "name":
                        print("\t\t\t%s=%s" % (key, hdr[key]))


#
# In order to use the stream parser, you need to use the stream_request_body decorator on you RequestHandler.
#

@stream_request_body
class StreamHandler(RequestHandler):
    def get(self):
        self.write('''<html><body>
<form method="POST" action="/" enctype="multipart/form-data">
File #1: <input name="file1" type="file"><br>
File #2: <input name="file2" type="file"><br>
File #3: <input name="file3" type="file"><br>
Other field 1: <input name="other1" type="text"><br>
Other field 2: <input name="other2" type="text"><br>
Other field 3: <input name="other3" type="text"><br>
<input type="submit">
</form>
</body></html>''')

    def prepare(self):
        """In request preparation, we get the total size of the request and create a MultiPartStreamer for it.

        In the prepare method, we can call the connection.set_max_body_size() method to set the max body size
        that can be **streamed** in the current request. We can do this safely without affecting the general
        max_body_size parameter."""
        global MAX_STREAMED_SIZE
        if self.request.method.lower() == "post":
            self.request.connection.set_max_body_size(MAX_STREAMED_SIZE)
            print("Changed max streamed size to %s" % format_size(MAX_STREAMED_SIZE))

        try:
            total = int(self.request.headers.get("Content-Length", "0"))
            print("total is :",total)
        except KeyError:
            total = 0  # For any well formed browser request, Content-Length should have a value.
        # noinspection PyAttributeOutsideInit
        self.ps = MyStreamer(total)

    def data_received(self, chunk):
        """When a chunk of data is received, we forward it to the multipart streamer.

        :param chunk: Binary string received for this request."""
        self.ps.data_received(chunk)

    def post(self):
        """Finally, post() is called when all of the data has arrived.

        Here we can do anything with the parts."""
        print("\n\npost() is called when streaming is over.")
        try:
            # Before using the form parts, you **must** call data_complete(), so that the last part can be finalized.
            self.ps.data_complete()
            targetpath = self.get_argument('targetpath')
            print("\n\ntargetfile is :",targetpath)
            # Use parts here!
            for idx, part in enumerate(self.ps.parts):
                part.move(targetpath)

            self.set_header("Content-Type", "text/plain")
            out = sys.stdout
            try:
                sys.stdout = self
                self.ps.examine()
            finally:
                sys.stdout = out
        finally:
            # Don't forget to release temporary files.
            self.ps.release_parts()
def read_in_chunks(infile, chunk_size=1024*1024):
   chunk = infile.read(chunk_size)
   while chunk:
       yield chunk
       chunk = infile.read(chunk_size)

def read_in_chunks_pos(base_dir, pos, size, chunk_size=1024*1024):
  realsize = getsize(base_dir)
  if(int(size)>=realsize):
   with open(base_dir, 'rb') as infile:
     infile.seek(int(pos))
     no = (realsize-int(pos)) // chunk_size
     i = 0
     while i<no:
        chunk = infile.read(chunk_size)
        yield chunk
        i = i+1
     if ((realsize-int(pos)) % chunk_size) != 0:
        last = (realsize-int(pos)) % chunk_size
        chunk = infile.read(last)
        yield chunk
   infile.close()
  else:   
   with open(base_dir, 'rb') as infile:
     infile.seek(int(pos))
     no = int(size) // chunk_size
     i = 0
     #chunk = infile.read(chunk_size)
     #while chunk and i<no:
     while i<no:
        chunk = infile.read(chunk_size)
        yield chunk
        i = i+1
     if (int(size) % chunk_size) != 0:
        last = int(size) % chunk_size
        chunk = infile.read(last)
        yield chunk
   infile.close()

class ReadRequestHandler(tornado.web.RequestHandler):
   @gen.coroutine
   def get(self):
        total_sent = 0
        uid = self.get_argument('uid')
        gid = self.get_argument('gid')
        base_dir = self.get_argument('filepath')
        pos = self.get_argument('pos')
        size = self.get_argument('size')
        # Python protocol does not require () on it's if statements like you are
        print("size",size)

        if base_dir==None or uid==None or gid==None or pos==None or size==None:
            self.write("Invalid argument!You caused a %d error."%status_code)
            exit(1)
        if os.path.exists(base_dir):
          statinfo = os.stat(base_dir)
          if(int(uid)==statinfo.st_uid and int(gid)==statinfo.st_gid):
              mode = statinfo.st_mode
          else:
              self.write("Permission denied.")
              exit(1)
        else:
            self.write("File or directory doesn't exist!You caused a %d error."%status_code)
            exit(1)
        if (S_ISDIR(mode)):
            self.write("This is not a file!You caused a %d error."%status_code)
            exit(1)
        else:
          #  with open(base_dir, 'rb') as infile:
                for chunk in read_in_chunks_pos(base_dir,pos,size):
                    self.write(chunk)
                    yield gen.Task(self.flush)
                    total_sent += len(chunk)
         #           print("sent",total_sent)
        #        print("senttotal",total_sent)
                self.finish()
class ListRequestHandler(tornado.web.RequestHandler):
   @tornado.web.asynchronous
   @gen.coroutine
   def get(self):
        uid = self.get_argument('uid')
        gid = self.get_argument('gid')
        base_dir = self.get_argument('path')
        if (base_dir==None or uid==None or gid==None):
            self.write("Invalid argument!You caused a %d error."%status_code)
            exit(1)
        if(os.path.exists(base_dir)):
          statinfo = os.stat(base_dir)
          self.write('{'+'"father_node"'+':')
          statdict = {'path':base_dir,'mode':str(statinfo.st_mode),'ino':str(statinfo.st_ino),'dev':str(statinfo.st_dev),'nlink':str(statinfo.st_nlink),'uid':str(statinfo.st_uid),'gid':str(statinfo.st_gid),'size':str(statinfo.st_size),'atime':str(statinfo.st_atime),'mtime':str(statinfo.st_mtime),'ctime':str(statinfo.st_ctime)}
          if(int(uid)==statinfo.st_uid and int(gid)==statinfo.st_gid):
              self.write(statdict)
              mode = statinfo.st_mode
          else:
              self.write("Permission denied.")
              exit(1)
        else:
            self.write("File or directory doesn't exist!You caused a %d error."%status_code)
            exit(1)
        if (S_ISDIR(mode)==None):
                self.write("This is not a directory!You caused a %d error."%status_code)
                exit(1)
        else:
                files = os.listdir(base_dir)
                for f in files:
                    statinfo = os.stat(base_dir + '/' +f)
                    self.write(',"'+f+'":')
                    statdict = {'path':(base_dir + '/' +f),'mode':str(statinfo.st_mode),'ino':str(statinfo.st_ino),'dev':str(statinfo.st_dev),'nlink':str(statinfo.st_nlink),'uid':str(statinfo.st_uid),'gid':str(statinfo.st_gid),'size':str(statinfo.st_size),'atime':str(statinfo.st_atime),'mtime':str(statinfo.st_mtime),'ctime':str(statinfo.st_ctime)}
              #      print ("statdict",statdict)
                    self.write(statdict)
                self.write("}")
   def write_error(self,status_code,**kwargs):
                self.write("Gosh darnit,user!You caused a %d error."%status_code)

class StreamingRequestHandler(tornado.web.RequestHandler):
   @tornado.web.asynchronous
   @gen.coroutine
   def get(self):
       # back as right now this is limited to what is hard coded in
        total_sent = 0
        uid = self.get_argument('uid')
        gid = self.get_argument('gid')
        base_dir = self.get_argument('filepath')
        if (base_dir==None or uid==None or gid==None):
            self.write("Invalid argument!You caused a %d error."%status_code)
            exit(1)
        if(os.path.exists(base_dir)):
          statinfo = os.stat(base_dir)
          if(int(uid)==statinfo.st_uid and int(gid)==statinfo.st_gid):
              mode = statinfo.st_mode
          else:
              self.write("Permission denied.")
              exit(1)
        else:
            self.write("File or directory doesn't exist!You caused a %d error."%status_code)
            exit(1)
        if (S_ISDIR(mode)):
            self.write("This is not a file!You caused a %d error."%status_code)
            exit(1)
        else:
            with open(base_dir, 'rb') as infile:
                for chunk in read_in_chunks(infile):
                    self.write(chunk)
                    yield gen.Task(self.flush)
                    total_sent += len(chunk)
                    print("sent",total_sent)

            self.finish()

if __name__ == "__main__":
   # this was connected to the pyCurl call and as far as I know now not
   # beng used so try without to insure it's no longer needed
   tornado.options.parse_command_line()
   application = tornado.web.Application([
    (r"/download", StreamingRequestHandler),
    (r"/list",ListRequestHandler),
    (r"/read",ReadRequestHandler),
    (r"/upload", StreamHandler),
    ])
   
   http_server = tornado.httpserver.HTTPServer(
            application,
            xheaders=True,
            max_body_size=MAX_BODY_SIZE,
            max_buffer_size=MAX_BUFFER_SIZE,
    )
   http_server.listen(options.port)
   tornado.ioloop.IOLoop.instance().start()

