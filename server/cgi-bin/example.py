#!/opt/lighttpd_python/bin/python3

from urllib.parse import unquote
from os.path import exists, isfile

import lib

def main():
	params = lib.params()
	path = "/" + unquote(params.get("path")).strip("/")

	if not path or ".." in path:
		raise lib.HttpResponse("400 Bad Request", "'path' parameter must exist and be valid")

	full_path = "/mnt/shared/media" + path

	if not exists(full_path):
		raise lib.HttpResponse("404 Not Found", f"{full_path} does not exist")
	if not isfile(full_path):
		raise lib.HttpResponse("422 Unprocessable Entity", f"{full_path} is not a file")

	print("Status: 200 OK")
	print("Content-Type: text/html")
	print()
	print(lib.template("video_frame", type="video/mp4", path=path))

lib.wrap(main)
