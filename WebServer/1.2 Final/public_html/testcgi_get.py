import cgi
import sys
import os

print("Content-Type: text/html")
print()

for i in range(1024 * 1024):
	print("abcdefg" * 1024)
