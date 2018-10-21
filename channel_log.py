from collections import defaultdict
import datetime
import os
from os import path

import lz4framed

import config

channel_logs = {}

def log_message(channel_path, message):
	try:
		timestamp = datetime.datetime.strptime(message['timestamp'], '%Y-%m-%dT%H:%M:%S.%f+00:00')
	except ValueError:
		timestamp = datetime.datetime.strptime(message['timestamp'], '%Y-%m-%dT%H:%M:%S+00:00')
	date = timestamp.date()

	cl = channel_logs.get(channel_path)
	if cl is not None and cl.date != date:
		assert cl.date < date, 'new message is older than previously logged'
		cl.close()
		cl = None
	if cl is None:
		print('opening', channel_path, date)
		cl = ChannelLog(channel_path, date)
		channel_logs[channel_path] = cl

	cl.log(message['id'], timestamp.strftime('%H:%M:%S'), message['author']['id'], message['content'])

def flush():
	for cl in channel_logs.values():
		cl.close()

def last_message_id(abspath):
	return _parse(abspath)[0]

def _parse(abspath):
	with open(abspath, 'rb') as f:
		compressed = f.read()
	contents = lz4framed.decompress(compressed)
	if contents[-1] != 0:
		raise Exception('corrupt log file', abspath)
	last_message = contents[contents.rfind(b'\0', 0, -1) + 1:-1]
	lmi = last_message.split(b'|', 1)[0].decode()
	return lmi, contents

class ChannelLog:
	def __init__(self, channel_path, date):
		abspath = path.join(config.log_dir, channel_path, date.strftime('%Y-%m-%d')) + '.lz4'
		try:
			self.file = open(abspath, 'xb')
			contents = None
		except FileExistsError:
			_, contents = _parse(abspath)
			self.file = open(abspath, 'wb')
		self.compressor = lz4framed.Compressor(self.file)
		if contents is not None:
			self.compressor.update(contents)

		self.date = date

	def log(self, *args):
		line = '|'.join(args).encode('utf-8') + b'\0'
		self.compressor.update(line)

	def close(self):
		self.compressor.end()
		self.file.close()
