__author__ = 'Ivan Dortulov'

import cgi

print("Content-Type: text/plain;charset=utf-8")
print()

form = cgi.FieldStorage()
user = form.getfirst("user", "").upper()    # This way it's safe.
print(user)