__author__ = 'Ivan Dortulov'


class HttpResponse(object):

    def __init__(self, code = 200, description = '', version=1.1):
        # Protocol version
        self.http_version = version

        # The Status-Code element is a 3-digit integer result
        # code of the attempt to understand and satisfy the request.
        self.status_code = code

        self.reason_phase = b""

        # Response headers
        self.headers = {}

        # The response extracted from this objec
        self.response = b""

        self.generate(code, description)


    def generate(self, code, description):

        if code == 200:
            (size, type) = description

            self.headers["content-length"] = str(size)

            if type in HttpResponse.mime_types:
                self.headers["content-type"] = HttpResponse.mime_types[type]
            else:
                self.headers["content-type"] = "application/octet-stream"

            self.reason_phase = HttpResponse.responses[code].encode()

            self.response = b"HTTP/" + str(self.http_version).encode() + b" " + str(self.status_code).encode()
            self.response += b" " + HttpResponse.responses[code].encode() + b"\r\n"

            for (key, value) in self.headers.items():
                self.response += key.encode() + b": " + value.encode() + b"\r\n"
            self.response += b"\r\n"

        if code >= 400 and code < 500:
            self.reason_phase = HttpResponse.responses[code].encode()

            data = b"<html><head><title>" + str(self.status_code).encode() + b" - "
            data += self.reason_phase + b"</title></head><body>"
            data += b"<h1>" + str(self.status_code).encode() + b" - " + self.reason_phase + b"</h1>"
            data += description.encode()
            data += b"</body></html>"

            self.headers["content-type"] = "text/html"
            self.headers["content-length"] = str(len(data))

            self.reason_phase = HttpResponse.responses[code].encode()
            self.response = b"HTTP/" + str(self.http_version).encode() + b" " + str(self.status_code).encode()
            self.response += b" " + HttpResponse.responses[code].encode() + b"\r\n"

            for (key, value) in self.headers.items():
                self.response += key.encode() + b": " + value.encode() + b"\r\n"
            self.response += b"\r\n"

            self.response += data

    responses = {200: "OK",
                 400: "Bad Request",
                 403: "Forbidden",
                 404: "File Not Found",
                 501: "Not Implemented"}

    mime_types = {"txt":  "text/plain",
                  "html": "text/html",
                  "xml":  "text/html",
                  "css":  "text/css",
                  "png":  "image/png",
                  "jpg":  "image/jpg",
                  "jpeg": "image/jpeg",
                  "gif":  "image/gif",
                  "mp3":  "audio/mpeg",
                  "avi":  "video/avi",
                  "mp4":  "video/mp4"
                  }