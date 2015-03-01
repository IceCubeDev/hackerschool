__author__ = 'Ivan Dortulov'


class HttpResponse(object):

    def __init__(self):
        # Protocol version
        self.httpVersion = 1.1

        # The Status-Code element is a 3-digit integer result
        # code of the attempt to understand and satisfy the request.
        self.statusCode = 200

        self.reasonPhase = "OK"

        # Response headers
        self.headers = {"Content-Type": "text/html"}

    def generate(code, description):
        response = b"HTTP/1.1 " + str(code).encode() + b" " + HttpResponse.responses[code].encode() + b"\n"

        # Ok
        if code == 200:
            response += b"Content-Length: " + str(len(description)).encode() + b"\n\n"
            response += description.encode()

        # Error codes
        elif code >= 400 and code < 500:
            text = b"<html>\n<head>\n\t<title>" + str(code).encode() + b" - " + HttpResponse.responses[code].encode() + b"</title>\n<body>"

            text += b"<center><h1> Oh noooooooo~! </h1></center>"
            text += b"<center><img src=\"/explode.gif\" /></center>"
            text += b"<h1>" + str(code).encode() + b" - " + HttpResponse.responses[code].encode() + b"</h1>\n"
            text += b"<p>" + description.encode() + b"</p>\n"
            text += b"<hr> <i>IceWeb Server</i>\n"
            text += b"</body>\n</html>"

            response += b"Content-Length: " + str(len(text)).encode() + b"\n\n"
            response += text

        return response

    def raw(self):
        response = b"HTTP/" + str(self.httpVersion).encode() + b" " + str(self.statusCode).encode() + b" " + self.reasonPhase.encode() + b"\n"

        for (key, value) in self.headers.items():
            response += key.encode() + b": " + value.encode() + b"\n"

        response += b"\n"
        return response

    responses = {200: "OK",
                 400: "Bad Request",
                 403: "Forbidden",
                 404: "File Not Found",
                 501: "Not Implemented"}