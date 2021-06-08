#!/usr/bin/env python3

import os
import os.path
import sys

def main():
	basedir = sys.argv[1]
	for subdir in os.listdir(basedir):
		subdir_path = os.path.join(basedir, subdir)
		if not os.path.isdir(subdir_path):
			print('ignoring', subdir_path)
			continue
		filenames = os.listdir(subdir_path)
		if not filenames:
			continue
		filepath = os.path.join(subdir_path, max(filenames))
		if os.stat(filepath).st_size == 7:
			print(filepath)
			os.unlink(filepath)

if __name__ == '__main__':
	main()
