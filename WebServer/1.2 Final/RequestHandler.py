__author__ = 'Ivan Dortulov'

import re
import queue
import os
import stat
import subprocess
import fcntl

from Log import *


class HttpRequest(object):

    def __init__(self, request_string):
        request_string = request_string.lower()
        idx = request_string.find("\r\n")
        self.request_line = request_string[:idx].split()
        request_string = request_string[idx + 2:]

        self.headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", request_string))

        self.request_method = self.request_line[0]
        self.request_uri = self.request_line[1]
        self.request_version = self.request_line[2]

        self.remaining = 0
        self.processing = False
        self.is_script = False
        self.abs_path = ""
        self.temp_buffer = b""
        self.input_file = None

    @staticmethod
    def extract_headers_from_string(headers):
        return dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", headers))

class RequestHandler(object):

    responses = {200: "OK",
                 404: "File Not Found"}

    SCRIPT_MAX_HEADER_SIZE = 4098

    def __init__(self, server, address=""):
        self.server = server
        self.address = address

        self.input = b""
        self.output = b""
        self.should_close = False

        self.current_request = None
        self.request_queue = queue.Queue()
        self.request_resource = None

    def __del__(self):
        if self.request_resource is not None:
            try:
                if not isinstance(self.request_resource, subprocess.Popen):
                    self.request_resource.close()
                    self.request_resource = None
            except IOError:
                Log.w("RequestHandler", "Destructor: nothing to close.")

    def process_data(self, data):
        self.input += data

    def finish_request(self):
        Log.d("RequestHandler", "finish_request: " + self.current_request.request_line[0] +
              " request from " + str(self.address) + " was processed.")

        if self.request_resource is not None:
            try:
                if not self.current_request.is_script:
                    self.request_resource.close()
                else:
                    self.request_resource.kill()
                self.request_resource = None
            except IOError as ex:
                Log.w("RequestHandler", "finish_request: " + self.address +
                      " Unable to close file: " + str(ex.args[1]))

        if self.current_request.input_file is not None:
            self.current_request.input_file.close()
        
        del self.current_request
        self.current_request = None
        self.should_close = True

    def process_next_request(self):
        if self.current_request is not None:
            if self.current_request.processing:
                if self.current_request.remaining <= 0:
                    self.finish_request()
                else:
                    if self.current_request.request_method == "get":
                        self.process_get_request()
                    elif self.current_request.request_method == "post":
                        self.process_post_request()
            else:
                self.finish_request()
        else:
            if not self.request_queue.empty():
                Log.d("RequestHandler", "process_next_request: Processing next request from " + self.address)
                self.current_request = self.request_queue.get(False)
                self.init_request(self.current_request)
            else:
                idx = self.input.find(b"\r\n\r\n")
                if idx >= 0:
                    request_string = self.input[:idx + 4].decode()
                    self.input = self.input[idx + 4:]

                    request = HttpRequest(request_string)
                    self.request_queue.put(request)
                    Log.d("RequestHandler", "process_data: Received " + request.request_method + " request from " +
                          self.address)

    def process_script(self):
        if self.request_resource.poll() is None:
            try:
                script_output = self.request_resource.stdout.read(1024)
            except IOError as ex:
                print("Poll exception", ex.args[0])
                return

            if script_output is not None:
                Log.d("RequestHandler", "process_script: " + self.address +
                      " Script outputed " + str(script_output))
                if self.current_request.remaining == 1:
                    script_output = script_output.replace(b"\n", b"\r\n")
                    self.current_request.temp_buffer += script_output

                    idx = self.current_request.temp_buffer.find(b"\r\n\r\n")
                    if idx >= 0:
                        headers = self.current_request.temp_buffer[:idx+4]
                        Log.d("RequestHandler", "process_script: Finished reading script headers: " +
                              str(headers))
                        self.current_request.temp_buffer = self.current_request.temp_buffer[idx+4:]
                        self.current_request.remaining = 2
                        self.output += self.generate_response(200, "1.1",
                                                              HttpRequest.extract_headers_from_string(headers.decode())).\
                                                              encode()

                        Log.d("RequestHandler", "process_script: Content after headers: " +
                              str(self.current_request.temp_buffer))
                        self.output += self.current_request.temp_buffer
                else:
                    self.output += script_output
        else:
            self.current_request.remaining = 0
            Log.d("RequestHandler", "process_script: Finished reading script headers: " +
                  str(self.current_request.temp_buffer))

    def process_get_request(self):
        # Check if file still exists
        if not self.current_request.is_script:
            try:
                if os.stat(self.current_request.abs_path)[stat.ST_SIZE] <= 0:
                    Log.w("RequestHandler", "process_get_request: " + self.address +
                          " Error writing to file: File deleted")
                    self.current_request.processing = False
                read_chunk = self.request_resource.read(self.server.CHUNK_SIZE)
            except IOError as ex:
                Log.w("RequestHandler", "process_get_request: " + self.address +
                      " Error reading file: " + str(ex.args[1]))
                self.current_request.remaining = 0
            else:
                Log.d("RequestHandler", "process_get_request: " + self.address +
                      " Read " + str(len(read_chunk)) + " bytes from " +
                      self.current_request.request_uri)
                self.output += read_chunk
                self.current_request.remaining -= len(read_chunk)
        else:
            self.process_script()

    def process_post_request(self):
        if self.request_resource is not None:
            try:
                if os.stat(self.current_request.abs_path)[stat.ST_SIZE] <= 0:
                    Log.w("RequestHandler", "process_get_request: " + self.address +
                          " Error writing to file: File deleted")
                    self.current_request.remaining = 0

                write_chunk = self.input[:self.current_request.remaining]
                written = self.request_resource.write(write_chunk)
                self.current_request.remaining -= written
                self.input = self.input[written:]
                Log.d("RequestHandler", "process_post_request: " + self.address +
                      " Wrote " + str(written) + " bytes to file." + str(self.current_request.remaining) +
                      " bytes left to be written.")
            except IOError as ex:
                Log.w("RequestHandler", "process_get_request: " + self.address +
                      " Error writing to file: " + str(ex.args[1]))
                self.current_request.remaining = 0

            if self.current_request.remaining <= 0:
                self.current_request.remaining = 1
                self.current_request.is_script = True
                self.request_resource.close()
                self.request_resource = None

                self.current_request.request_method = "get"
                try:
                    self.current_request.input_file = open(self.current_request.abs_path, "rb")
                except IOError as ex:
                    Log.e("RequestHandler", "process_post_request: " + str(ex))
                    # TODO: Add proper response

                self.init_request(self.current_request)

    def init_request(self, request):
        Log.d("RequestHandler", "init_request: " + self.address + " Initializing request")

        file_path = self.server.server_variables["document_root"] + "/public_html" + \
                        self.current_request.request_uri
        file_path = file_path.replace("\\", "/")
        self.current_request.abs_path = file_path

        if request.request_method == "get":

            Log.d("RequestHandler", "init_request: " + self.address + " requested " + self.current_request.request_uri)
            if os.path.isfile(file_path):
                (file_name, file_ext) = os.path.splitext(os.path.basename(file_path))

                if file_ext == ".py":
                    Log.d("RequestHandler", "init_request: " + self.address + " requested a script execution '" +
                          self.current_request.request_uri)

                    try:
                        if request.input_file is not None:
							request.input_file.seek(0, 2)
							size = request.input_file.tell()
							request.input_file.seek(0, 0)
							
							environ = os.environ.copy()
							environ["CONTENT-LENGTH"] = str(size)
							
                            self.request_resource = subprocess.Popen(['python3', file_path],
                                                                     stdout=subprocess.PIPE,
                                                                     stdin=request.input_file,
                                                                     stderr=subprocess.PIPE,
																	 env = environ)
                        else:
                            self.request_resource = subprocess.Popen(["python3", file_path],
                                                                     stdout=subprocess.PIPE,
                                                                     stderr=subprocess.PIPE)

                    except subprocess.SubprocessError as ex:
                        Log.w("RequestHandler", "init_request: " + self.address +
                              " Error executing script: " + str(ex.args[1]))
                    else:
                        self.current_request.processing = True
                        self.current_request.is_script = True
                        self.current_request.remaining = 1

                        fd = self.request_resource.stdout.fileno()
                        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                else:
                    try:
                        self.request_resource = open(file_path, "rb")
                    except IOError as ex:
                        Log.w("RequestHandler", "init_request: " + self.address +
                              " Could not open file '" + file_path + "': " + str(ex.args[1]))
                        self.current_request.remaining = 0
                    else:
                        (file_name, file_ext) = os.path.splitext(os.path.basename(file_path))
                        file_size = os.path.getsize(file_path)

                        Log.d("RequestHandler", "init_request: " + self.address + " File '" + file_path +
                              "' was found(" +str(file_size) + ")")

                        self.output += self.generate_response(200, "1.1",
                                                              {"Content-Type": self.guess_content_type(file_ext),
                                                               "Content-Length": str(file_size),
                                                               "Connection": "close"}).encode()
                        self.current_request.remaining = file_size
                        self.current_request.processing = True
            elif os.path.isdir(file_path):
                Log.w("RequestHandler", "init_request: Directory listing not implemented!")
                self.current_request.remaining = 0
                self.current_request.processing = False
            else:
                self.output += self.generate_response(404, "1.1", {"Content-Type": "text/html",
                                                                   "Connection": "close"},
                                                      "<html><body><h1>404 - File not found</h1>"
                                                      "<p>The requested resource was not found on this server!</p>"
                                                      "</body></html>").encode()

                self.current_request.remaining = 0
                self.current_request.processing = False

        elif request.request_method == "post":
            if os.path.isfile(file_path):
                (file_name, file_ext) = os.path.splitext(os.path.basename(file_path))

                if file_ext == ".py":
                    self.request_resource = open(file_path + "__stdin", "wb")
                    self.current_request.remaining = int(request.headers['content-length'])
                    self.current_request.processing = True
                else:
                    self.output += self.generate_response(404, "1.1", {"Content-Type": "text/html",
                                                                       "Connection": "close",
                                                                       "Content-Length":"0"}).encode()


    @staticmethod
    def generate_response(code = 200, version="1.1", headers={}, extra=""):
        if code == 200:
            response = "HTTP/" + version + " " + str(code) + " " + RequestHandler.responses[code] + "\r\n"
            for (key, value) in headers.items():
                response += str(key) + ": " + str(value) + "\r\n"

            response += "\r\n"
            return response
        if code >= 400:
            response = "HTTP/" + version + str(code) + " " + RequestHandler.responses[code] + "\r\n"
            for (key, value) in headers.items():
                response += str(key) + ": " + str(value) + "\r\n"
            response += "Content-Length: " + str(len(extra)) + "\r\n"

            response += "\r\n"
            response += extra
            return response

    @staticmethod
    def guess_content_type(ext):
        if ext == ".txt":
            return "text/plain"
        elif ext == ".html":
            return "text/html"
        elif ext == ".css":
            return "text/css"
        elif ext == ".js":
            return "application/javascript"
        elif ext == ".png":
            return "image/png"
        else:
            return "application/octet-stream"
