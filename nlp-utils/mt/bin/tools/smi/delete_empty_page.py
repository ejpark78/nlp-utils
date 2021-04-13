#!/usr/bin/env python 

import os

list_dirs= {}

file_path='./file'
for top, dirs, files in os.walk(file_path):
	if len(dirs) == 0 :
		continue

	for d in dirs:
		list_dirs[d] = 1


page_path='./page'
for top, dirs, files in os.walk(page_path):
	for f in files:
		fname = f.split('.')[0]

		if list_dirs.has_key(fname) :
			continue

		print "delete "+top+"/"+f
		os.unlink(top+"/"+f)


