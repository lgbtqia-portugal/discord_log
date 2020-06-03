#!/usr/bin/env python3

import os
from os import path
import sys

import lz4framed

def main():
	query = sys.argv[1].casefold()
	for file_path in sys.argv[2:]:
		search_path(query, file_path)

def search_path(query, file_path):
	if path.isdir(file_path):
		for filename in os.listdir(file_path):
			search_path(query, path.join(file_path, filename))
	else:
		for author_id, time, contents in search_file(query, file_path):
			print(file_path, author_id, time, contents)

def search_file(query, full_path):
	with open(full_path, 'rb') as f:
		compressed = f.read()
	contents = lz4framed.decompress(compressed)
	if contents[-1] != 0:
		raise Exception('corrupt log file', full_path)
	for message in contents.split(b'\0')[:-1]:
		msg_id, time, author_id, contents = message.split(b'|', 3)
		contents = contents.decode('utf-8')
		if query in contents.casefold():
			yield author_id.decode('ascii'), time.decode('ascii'), contents

if __name__ == '__main__':
	main()
