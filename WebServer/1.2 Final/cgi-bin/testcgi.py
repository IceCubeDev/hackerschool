__author__ = 'Ivan Dortulov'

import cgi

print("Content-Type: text/plain;charset=utf-8")
print()

form = cgi.FieldStorage()
user = form.getfirst("file", "").upper()    # This way it's safe.
print(user)
#for i in range(1, 1024 * 1024):
#    testString = "abcdefg" * 1024
#    print(testString)
