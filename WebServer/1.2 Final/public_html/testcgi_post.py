import cgi
import sys
import os

print("Content-Type: text/html")
print()

form = cgi.FieldStorage(sys.stdin)
for (key, value) in form.items():
	print(key, " => ", value)
print(user)
